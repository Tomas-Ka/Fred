# -*- coding: UTF-8 -*-
import discord
from discord import app_commands
from discord.ext import commands

# -----------------------STATIC VARS----------------------
ARCHIVE_ROLE = "Archive"

# --------------------PERSISTENT VIEWS--------------------


class PersistentArchiveRoleView(discord.ui.View):
    # This is the View that adds the button to get or remove the Archive role
    def __init__(self) -> None:
        # set the timeout to none so the View can be persistent
        super().__init__(timeout=None)

    # set up the button and the callback function (the callback function is
    # the function that is run when the button is pressed)
    @discord.ui.button(label='Toggle archives',
                       style=discord.ButtonStyle.grey,
                       custom_id='archive_access_button')
    async def archive(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        # get the Archive role from the Server
        role = discord.utils.get(interaction.guild.roles, name=ARCHIVE_ROLE)
        if role in interaction.user.roles:
            # If the user has the role, remove it and send a confirm message
            await interaction.user.remove_roles(role)
            await interaction.response.send_message('The Archives are hidden from you once more', ephemeral=True)
        else:
            # Id the user doesn't have the role, add it to the player and send
            # confirm message
            await interaction.user.add_roles(role)
            await interaction.response.send_message('Welcome to the Archives! You can find them at the bottom of the channel list. If you want to hide them, hit the button once more', ephemeral=True)


# -----------------------MAIN CLASS-----------------------
class ArchiveHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # command to send the archive join message (/join_arhive), should be
    # locked to admin role
    @app_commands.command(description="Sends the Archive joining message")
    async def join_archive(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="The Archives",
            description="If you want to see all our old chatlogs from previous years, they are all available in our archive that is hidden by default. To view it, just press the button bellow this message!")
        await interaction.channel.send(embed=embed, view=PersistentArchiveRoleView())
        await interaction.response.send_message("Message sent successfully", ephemeral=True)


# ------------------------MAIN CODE-----------------------
# This setup is required for the cog to setup and run,
# and is run when the cog is loaded with bot.load_extensions()
async def setup(bot: commands.Bot) -> None:
    print(f"\tcogs.archive_handler begin loading")
    bot.add_view(PersistentArchiveRoleView())

    await bot.add_cog(ArchiveHandler(bot))
