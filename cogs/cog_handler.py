import traceback

import discord
from discord import app_commands
from discord.ext import commands

from main import FredBot


class CogHandler(commands.Cog):
    bot: FredBot

    def __init__(self, bot: FredBot) -> None:
        self.bot = bot

    @app_commands.command(description="lists all loaded extensions")
    @app_commands.dm_only()
    async def check_extensions(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.bot.owner:
            _ = await interaction.response.send_message(
                "Error, only the bot owner can run this command"
            )
            return
        response_string = "Loaded extensions:\n```"
        for name in self.bot.extensions:
            response_string += " - " + name + "\n"
        response_string += "```"
        _ = await interaction.response.send_message(response_string)

    @app_commands.command(description="Syncs the discord command tree")
    @app_commands.dm_only()
    @app_commands.rename(guild_id_str="guild_id")
    async def sync_tree(
        self, interaction: discord.Interaction, guild_id_str: None | str = None
    ) -> None:
        if interaction.user.id != self.bot.owner:
            _ = await interaction.response.send_message(
                "Error, only the bot owner can run this command"
            )
            return

        if not guild_id_str:
            _ = await self.bot.tree.sync()
            _ = await interaction.response.send_message("Synced command tree")
            return

        try:
            guild_id = int(guild_id_str)
        except ValueError:
            _ = await interaction.response.send_message(f"{guild_id_str} is not a valid integer")
            return

        for guild in self.bot.guilds:
            if guild.id == guild_id:
                self.bot.tree.copy_global_to(guild=guild)
                _ = await self.bot.tree.sync(guild=guild)
                _ = await interaction.response.send_message(
                    f"Synced command tree for guild {guild.name}"
                )
                return
        else:
            _ = await interaction.response.send_message(f"I am not in a guild with id {guild_id}")

    @app_commands.command(description="Loads a given extension")
    @app_commands.dm_only()
    async def command_load_extension(
        self, interaction: discord.Interaction, extension_name: str
    ) -> None:
        if interaction.user.id != self.bot.owner:
            _ = await interaction.response.send_message(
                "Error, only the bot owner can run this command"
            )
            return
        try:
            await self.bot.load_extension(extension_name)
            print(f"\t{extension_name} loaded")
            _ = await interaction.response.send_message(f"{extension_name} loaded!")
        except Exception:
            _ = await interaction.response.send_message(
                f"Failed to load extension {extension_name}."
            )
            traceback.print_exc()

    async def autocomplete_extension_name(self, _interaction: discord.Interaction, current: str):
        options: list[app_commands.Choice[str]] = []
        for name in self.bot.extensions:
            if name.lower().startswith(current.lower()):
                options.append(app_commands.Choice(name=name, value=name))
        return options

    @app_commands.command(description="unloads a given extension")
    @app_commands.dm_only()
    @app_commands.autocomplete(extension_name=autocomplete_extension_name)
    async def unload_extension(self, interaction: discord.Interaction, extension_name: str) -> None:
        if interaction.user.id != self.bot.owner:
            _ = await interaction.response.send_message(
                "Error, only the bot owner can run this command"
            )
            return

        if extension_name not in self.bot.extensions:
            _ = await interaction.response.send_message(
                f"{extension_name} is not a loaded extension"
            )
            return

        try:
            await self.bot.unload_extension(extension_name)
            print(f"\t{extension_name} unloaded")
            _ = await interaction.response.send_message(f"{extension_name} unloaded!")
        except Exception:
            _ = await interaction.response.send_message(
                f"Failed to unload extension {extension_name}."
            )
            traceback.print_exc()


# ----------------------MAIN PROGRAM----------------------
# This setup is required for the cog to setup and run,
# and is run when the cog is loaded with bot.load_extensions().
async def setup(bot: FredBot) -> None:
    print("\tcogs.cog_handler begin loading")
    await bot.add_cog(CogHandler(bot))
