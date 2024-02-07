from discord.ext import commands
from discord import app_commands
import discord
from re import search
import db_handler as db
import pytz
from thefuzz import process, fuzz


class TimezoneHandler(commands.GroupCog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(description="Displays the given time in your own timezone")
    async def time(self, interaction: discord.Interaction, time_string: str) -> None:
        results = search("(\d{1,2}):*(\d{1,2})*(am|pm)*", time_string)
        pass

    tzgroup = app_commands.Group(name="timezone", description="Commands to handle setting what timezone you're in")
    
    async def set_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Returns autocomplete results given part of a string.

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
            current (str): The part of the string to provide autocomplete for.

        Returns:
            list[app_commands.Choice[str]]: A list of autocompletes in the form of application command choices.
        """
        if current == '':
            return pytz.all_timezones[0:25]
        fuzzy_matches = [tz for tz in process.extract(current, pytz.all_timezones_set, scorer=fuzz.ratio, limit=25) if tz[1] >= 50]
        return [app_commands.Choice(name=tz[0], value=tz[0]) for tz in fuzzy_matches]
    
    @tzgroup.command()
    @app_commands.autocomplete(tz_string=set_autocomplete)
    async def set(self, interaction: discord.Interaction, tz_string: str):
        """Sets the timezone for a given user, given an Olson database string.

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
            tz_string (str): An Olson database formatted timezone name.
        """
        if not tz_string in pytz.all_timezones_set:
            await interaction.response.send_message(f"{tz_string} is not a valid timezone.")
            return
        
        # db.set_tz(interaction.user.id, tz_string)
        await interaction.response.send_message(f"Set {interaction.user.display_name}'s timezone to {tz_string}")
    
    @tzgroup.command()
    async def get(self, interaction:discord.Interaction):
        await interaction.response.send_message(f"Your set timezone is {'db.get_tz(interaction.user.id)'}")
    
async def setup(bot: commands.Bot) -> None:
    print(f"\tcogs.timezone_handler begin loading")
    await bot.add_cog(TimezoneHandler(bot))