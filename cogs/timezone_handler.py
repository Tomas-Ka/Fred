from discord.ext import commands
from discord import app_commands
import discord
from re import search
import db_handler as db
import pytz
from datetime import datetime, time, tzinfo
from thefuzz import process, fuzz


class TimezoneHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.timezones = pytz.all_timezones_set
        self.timezones.add("st")

    tzgroup = app_commands.Group(name="timezone", description="Commands to handle setting what timezone you're in")
    
    async def tz_string_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Returns autocomplete results given part of a string.

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
            current (str): The part of the string to provide autocomplete for.

        Returns:
            list[app_commands.Choice[str]]: A list of autocompletes in the form of application command choices.
        """
        if current == '':
            return []
        fuzzy_matches = [tz for tz in process.extract(current, self.timezones, scorer=fuzz.ratio, limit=25) if tz[1] >= 50]
        return [app_commands.Choice(name=tz[0], value=tz[0]) for tz in fuzzy_matches]

    @app_commands.command(description="Displays the given time in your own timezone")
    @app_commands.autocomplete(tz_string=tz_string_autocomplete)
    @app_commands.rename(time_string="time")
    @app_commands.rename(tz_string="timezone")
    async def time(self, interaction: discord.Interaction, time_string: str, tz_string: str) -> None:
        """Returns the given time in your own timezone 

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
            time_string (str): 24h or 12h time, with or without minutes.
            tz_string (str): The timezone of the given time (to convert to your timezone)
        """
        results = search("(\d{1,2}):*(\d{1,2})*(am|pm)*", time_string)
        if results == None:
            # Time input string imporperly formatted, error and return.
            return
        
        if not tz_string in self.timezones:
            # Timezone input does not exist, error and return.
            await interaction.response.send_message(f"{tz_string} is not a valid timezone.")
            return
        
        # Here we hack in "servertime" for FFXIV, because I'm totally not addicted and this entire
        # cog was totally not written just to save me the annoyance of converting to and fro...
        if tz_string.lower() == "st":
            tz_string = "UTC"


        # Set target hour
        if results.group(1) == None:
            # Input is missing an hour, error and return.
            return
        hour = int(results.group(1))

        # Set target minute.
        if results.group(2):
            minute = int(results.group(2))
        else:
            # If there is no minute we assume the user means an even hour.
            minute = 0

        # Deal with am / pm bullshit:
        # 12h time format is scuffed asf, 12am is midnight, 12pm is midday.
        # This fixes that by removing 12h if we are at midnight or midday.
        if results.group(3) == "am" and hour == 12:
            hour = 0
        if results.group(3) == "pm" and not hour == 12:
            hour += 12
        
        user_tz = db.get_tz(interaction.user.id)
        # Gets and prints the time in the users' timezone.

        # Uses the current date for calculations.
        given_tz_obj = datetime.now(pytz.timezone(tz_string))

        # Replaces the time on the current date with the given one
        given_tz_obj = given_tz_obj.replace(hour = hour, minute = minute)

        # Convert timezones and output to user
        target_tz_obj = given_tz_obj.astimezone(pytz.timezone(user_tz))

        await interaction.response.send_message(f"**{target_tz_obj.strftime('%H:%M')}** local time\n({time_string} in timezone {tz_string})")



    @tzgroup.command()
    @app_commands.rename(tz_string="timezone")
    @app_commands.autocomplete(tz_string=tz_string_autocomplete)
    async def set(self, interaction: discord.Interaction, tz_string: str):
        """Sets the timezone for a given user, given an Olson database string.

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
            tz_string (str): An Olson database formatted timezone name.
        """
        if not tz_string in self.timezones:
            await interaction.response.send_message(f"{tz_string} is not a valid timezone.")
            return
        
        # Here we hack in "servertime" for FFXIV, because I'm totally not addicted and this entire
        # cog was totally not written just to save me the annoyance of converting to and fro...
        if tz_string.lower() == "st":
            tz_string = "UTC"
        
        db.set_tz(interaction.user.id, tz_string)
        await interaction.response.send_message(f"Set {interaction.user.display_name}'s timezone to {tz_string}")
        print(tz_string)
    
    @tzgroup.command()
    async def get(self, interaction:discord.Interaction):
        """Displays what your current set timezone is

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
        """        
        await interaction.response.send_message(f"Your set timezone is {db.get_tz(interaction.user.id)}")
    
async def setup(bot: commands.Bot) -> None:
    print(f"\tcogs.timezone_handler begin loading")
    await bot.add_cog(TimezoneHandler(bot))