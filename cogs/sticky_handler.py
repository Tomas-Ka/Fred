# -*- coding: UTF-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
import db_handler as db

# -----------------------MAIN CLASS-----------------------


class StickyHandler(commands.Cog):
    def __init__(self, bot: commands.Bot, sticky_channels: List) -> None:
        self.bot = bot
        self.sticky_channels = sticky_channels

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        # This is only for the character sticky messages.
        # If the bot sent the message, ignore.
        if msg.author.id == self.bot.user.id:
            return

        # If we don't have a sticky in the channel, ignore.
        if msg.channel.id not in self.sticky_channels:
            return

        # Create the sticky embed (should probably cash this somewhere, but
        # wth, this works).
        sticky_embed = discord.Embed(title="Character Template", description="Här lägger ni in era nya karaktärers introduktion, det medlemmar i gillet skulle veta.\nREKOMMENDERAD MALL FÖR HUR MAN SKRIVER IN SIN KARAKTÄR: \n\n(namn), (klass/klasser och antalet levelar i klassen/klasserna, inkludera subclass/subclasses), (race), (Antal GP), (Lista över magic items) \n\n(Kort beskrivning av karaktärens background/personlighet, så vi vet vem vi har att göra med. Inga detaljer behöver vara med här, särskillt ingenting som ni vill att andra spelare inte ska känna till.) \n\n(Kort beskrivning av playstyle, till exempel:\nGet into opponent's faces and hit them with an axe;\nConfuse and disrupt with illusion magic;\nSnipe down important targets with a heavy crossbow) \n\nTryck shift+enter om ni vill göra en radbrytning utan att skicka meddelandet!\n\nP.S. håll er till ett meddelande, ni kan skicka en textfil med backstory om ni får slut på plats, och ni kan skicka character art i #art-gallery", color=0x00ff00)
        sticky_embed.set_footer(text="Stickied by Nat 1 Fred")

        # Send the new sticky and delete the old one.
        new_sticky = await msg.channel.send(embed=sticky_embed)
        sticky_id = await db.get_sticky(msg.channel.id)
        await msg.channel.get_partial_message(sticky_id).delete()
        # Process the data of the sticky (update references and the like), and
        # write the changes to disk.
        await db.update_sticky(msg.channel.id, new_sticky.id)

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.command(description="Creates the New Character sticky in a channel")
    async def new_char_sticky(self, interaction: discord.Interaction) -> None:
        """Discord command (/new_char_sticky) that creates a new-character
        sticky in a specific channel as well as the database.
        This command should be locked behind an admin role on discord.

        Args:
            interaction (discord.Interaction): Object with info about the command interaction.
        """
        sticky_embed = discord.Embed(title="Character Template", description="Här lägger ni in era nya karaktärers introduktion, det medlemmar i gillet skulle veta.\nREKOMMENDERAD MALL FÖR HUR MAN SKRIVER IN SIN KARAKTÄR: \n\n(namn), (klass/klasser och antalet levelar i klassen/klasserna, inkludera subclass/subclasses), (race), (Antal GP), (Lista över magic items) \n\n(Kort beskrivning av karaktärens background/personlighet, så vi vet vem vi har att göra med. Inga detaljer behöver vara med här, särskillt ingenting som ni vill att andra spelare inte ska känna till.) \n\n(Kort beskrivning av playstyle, till exempel:\nGet into opponent's faces and hit them with an axe;\nConfuse and disrupt with illusion magic;\nSnipe down important targets with a heavy crossbow) \n\nTryck shift+enter om ni vill göra en radbrytning utan att skicka meddelandet!", color=0x00ff00)
        sticky_embed.set_footer(text="Stickied by Nat 1 Fred")
        # Check if the sticky already exists in the channel.
        if interaction.channel.id in self.sticky_channels:
            # If it exists, just return an error message.
            await interaction.response.send_message("There is already a sticky in that channel", ephemeral=True)
        else:
            # If it doesn't exist, create a new sticky and add it to the db.
            new_sticky = await interaction.channel.send(embed=sticky_embed)
            await db.create_sticky(interaction.channel.id, new_sticky.id)
            self.sticky_channels.append(interaction.channel.id)
            await interaction.response.send_message(f"Sticky created in channel: {interaction.channel.name}", ephemeral=True)

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.command(description="Removes the New Character sticky from a channel")
    @app_commands.describe(del_sticky="Should the old sticky message be removed?")
    async def unsubscribe_new_char_sticky(self, interaction: discord.Interaction, del_sticky: Optional[bool] = False) -> None:
        """Discord command (/unsubscribe_new_char_sticky) that removes a
        new-character sticky in a specifc channel as well as the database.
        This command should be locked behind an admin role on discord.

        Args:
            interaction (discord.Interaction): Object with info about the command interaction.
            del_sticky (Optional[bool], optional): Delete the current sticky message or not; defaults to False.
        """
        # If a sticky exists in selected channel.
        if interaction.channel.id in self.sticky_channels:
            # If del_sticky flag is set, delete message, else just delete the
            # database entry.
            if del_sticky:
                sticky_id = await db.get_sticky(interaction.channel.id)
                await interaction.channel.get_partial_message(sticky_id).delete()
            await db.del_sticky(interaction.channel.id)
            self.sticky_channels.remove(interaction.channel.id)
            await interaction.response.send_message("Sticky has been deleted" if del_sticky else "Sticky has been unsubscribed", ephemeral=True)
        else:
            # Jst return an error as there isn't a sticky message to remove.
            await interaction.response.send_message(f"There is no new character sticky to remove from this channel", ephemeral=True)


# ----------------------MAIN PROGRAM----------------------
# This setup is required for the cog to setup and run,
# and is run when the cog is loaded with bot.load_extensions().
async def setup(bot: commands.Bot) -> None:
    print("\tcogs.sticky_handler begin loading")

    STICKY_CHANNELS = await db.get_sticky_list()
    print("\t\tLoaded stickies in channels:")

    if not STICKY_CHANNELS:
        print("\t\t\tNo stickies in database")
    else:
        for pair in STICKY_CHANNELS:
            print(f"\t\t\t{pair[0]}")

    sticky_channels = []
    for channel in STICKY_CHANNELS:
        sticky_channels.append(channel[0])

    await bot.add_cog(StickyHandler(bot, sticky_channels))
