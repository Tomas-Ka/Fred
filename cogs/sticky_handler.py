# -*- coding: UTF-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
#pickle is for storing and retrieving data
import pickle
#traceback is for error logging
import traceback


#-----------------------STATIC VARS----------------------
CHARACTER_STICKIES = {}
#VS Code is annoying and runs the code in the home directory. This shouldn't be requred once I actually run the code as a standalone
#Then I should just change this to "."
FILE_LOCATION = "."


#-----------------------FUNCTIONS------------------------
def write_stickies() -> None:
    with open(f'{FILE_LOCATION}/Character_stickies.dat', 'wb') as stickies:
        pickle.dump(CHARACTER_STICKIES, stickies)
        stickies.truncate()


#-----------------------MAIN CLASS-----------------------
class StickyHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        #this is only for the character sticky messages
        #if the bot sent the message, ignore
        if msg.author.id == self.bot.user.id:
            return
        #if we don't have a sticky in the channel, ignore
        if msg.channel.id not in CHARACTER_STICKIES:
            return
        #create the sticky embed (should probably cash this somewhere, but wth, this works)
        sticky_embed=discord.Embed(title="Character Template", description="Här lägger ni in era nya karaktärers introduktion, det medlemmar i gillet skulle veta.\nREKOMMENDERAD MALL FÖR HUR MAN SKRIVER IN SIN KARAKTÄR: \n\n(namn), (klass/klasser och antalet levelar i klassen/klasserna, inkludera subclass/subclasses), (race), (Antal GP), (Lista över magic items) \n\n(Kort beskrivning av karaktärens background/personlighet, så vi vet vem vi har att göra med. Inga detaljer behöver vara med här, särskillt ingenting som ni vill att andra spelare inte ska känna till.) \n\n(Kort beskrivning av playstyle, till exempel:\nGet into opponent's faces and hit them with an axe;\nConfuse and disrupt with illusion magic;\nSnipe down important targets with a heavy crossbow) \n\nTryck shift+enter om ni vill göra en radbrytning utan att skicka meddelandet!\n\nP.S. håll er till ett meddelande, ni kan skicka en textfil med backstory om ni får slut på plats, och ni kan skicka character art i #art-gallery", color=0x00ff00)
        sticky_embed.set_footer(text="Stickied by Nat 1 Fred")
        #send the new sticky and delete the old one
        new_sticky = await msg.channel.send(embed=sticky_embed)
        await msg.channel.get_partial_message(CHARACTER_STICKIES[msg.channel.id]).delete()
        #proces the data of the sticky (update references and the like), and write the changes to disk.
        CHARACTER_STICKIES[msg.channel.id] = new_sticky.id
        write_stickies()

    #command to create a new character sticky in a specific channel and memory/storage (/new_char_sticky), should be locked to admin role
    @app_commands.command(description="Creates the New Character sticky in a channel")
    async def new_char_sticky(self, interaction: discord.Interaction) -> None:
        sticky_embed=discord.Embed(title="Character Template", description="Här lägger ni in era nya karaktärers introduktion, det medlemmar i gillet skulle veta.\nREKOMMENDERAD MALL FÖR HUR MAN SKRIVER IN SIN KARAKTÄR: \n\n(namn), (klass/klasser och antalet levelar i klassen/klasserna, inkludera subclass/subclasses), (race), (Antal GP), (Lista över magic items) \n\n(Kort beskrivning av karaktärens background/personlighet, så vi vet vem vi har att göra med. Inga detaljer behöver vara med här, särskillt ingenting som ni vill att andra spelare inte ska känna till.) \n\n(Kort beskrivning av playstyle, till exempel:\nGet into opponent's faces and hit them with an axe;\nConfuse and disrupt with illusion magic;\nSnipe down important targets with a heavy crossbow) \n\nTryck shift+enter om ni vill göra en radbrytning utan att skicka meddelandet!", color=0x00ff00)
        sticky_embed.set_footer(text="Stickied by Nat 1 Fred")
        #check if the sticky already exists in the channel
        if interaction.channel.id in CHARACTER_STICKIES:
            #if it exists, just return an error message
            await interaction.response.send_message("There is already a sticky in that channel", ephemeral=True)
        else:
            #if it doesn't exist, create a new sticky and add it to memory/storage
            new_sticky = await interaction.channel.send(embed=sticky_embed)
            CHARACTER_STICKIES[interaction.channel.id] = new_sticky.id
            write_stickies()
            await interaction.response.send_message(f"Sticky created in channel: {interaction.channel.name}", ephemeral=True)
        

    #command to remove a new character sticky in a specific channel and memory/storage (/unsubscribe_new_char_sticky), should be locked to admin role
    @app_commands.command(description="Removes the New Character sticky from a channel")
    @app_commands.describe(del_sticky="Should the old sticky message be removed?")
    async def unsubscribe_new_char_sticky(self, interaction: discord.Interaction, del_sticky: Optional[bool] = False) -> None:
        #if a sticky exists in selected channel
        if interaction.channel.id in CHARACTER_STICKIES:
            #if del_sticky flag is set, delete message, else just delete the memory/storage references
            if del_sticky:
                await interaction.channel.get_partial_message(CHARACTER_STICKIES[interaction.channel.id]).delete()
            del CHARACTER_STICKIES[interaction.channel.id]
            write_stickies()
            await interaction.response.send_message("Sticky has been deleted" if del_sticky else "Sticky has been unsubscribed", ephemeral=True)
        else:
            #just return an error as there isn't a sticky message to remove
            await interaction.response.send_message(f"There is no new character sticky to remove from this channel", ephemeral=True)


#----------------------MAIN PROGRAM----------------------
#this setup is required for the cog to setup and run.
#this is run when the cog is loaded with bot.load_extensions()
async def setup(bot: commands.Bot) -> None:
    print(f"\tcogs.sticky_handler begin loading")
    global CHARACTER_STICKIES

    #load in the data and set it up in the global var
    with open(f'{FILE_LOCATION}/Character_stickies.dat', 'rb') as stickies:
        CHARACTER_STICKIES = pickle.load(stickies)
    print("\t\tLoaded stickies:")
    print(f"\t\t{CHARACTER_STICKIES}")

    await bot.add_cog(StickyHandler(bot))