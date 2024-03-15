from discord.ext import commands
from discord import app_commands
import discord
from re import match
import db_handler as db
import pytz
from datetime import datetime, time, tzinfo
from thefuzz import process, fuzz


class TimezoneHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.timezones = pytz.all_timezones_set
        self.timezones.add("ST")

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

        #! TODO; Split the fuzzy search up on the "/" Characters so we can search for just a city name as well

    @app_commands.command(description="Displays the given time in your own timezone")
    @app_commands.autocomplete(tz_string=tz_string_autocomplete)
    @app_commands.rename(time_string="time")
    @app_commands.rename(tz_string="timezone")
    async def time(self, interaction: discord.Interaction, time_string: str, tz_string: str, date: str = None) -> None:
        """Returns the given time in your own timezone 

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
            time_string (str): 24h or 12h time, with or without minutes.
            tz_string (str): The timezone of the given time (to convert to your timezone)
            date (str): A date in dd/mm/yy, dd/mm-yy or dd-mm-yy with one or two digits for d and m, and two or four digits for y.
        """
        #! TODO; ADD ERROR HANDLING TO THIS ENTIRE FUNCTION
        time_results = match("(\d{1,2}):*(\d{1,2})*(am|pm)*", time_string)
        if time_results == None:
            # TODO Time input string imporperly formatted, error and return.
            return
        
        if not tz_string.lower() in self.timezones:
            # TODO Timezone input does not exist, error and return. (Make embed, and ephemeral)
            await interaction.response.send_message(f"{tz_string} is not a valid timezone.")
            return

        # Here we hack in "servertime" for FFXIV, because I'm totally not addicted and this entire
        # cog was totally not written just to save me the annoyance of converting to and fro...
        if tz_string.lower() == "st":
            tz_string = "UTC"


        # TODO This needs error correcting
        # Set the correct day
        given_tz_obj = datetime.now()
        if not date == None:
            date_results = match("(\d{1,2})[-\/](\d{1,2})[-\/]?(\d{2,4})?", date)
            day = int(date_results.group(1).lstrip("0"))
            month = int(date_results.group(2).lstrip("0"))
            year_string = date_results.group(3)
            if year_string:
                if len(year_string) == 2:
                    year_string = "20" + year_string
                year = int(year_string.lstrip("0"))
            else:
                year = given_tz_obj.year
            #! TODO; use a try / catch here
            given_tz_obj = datetime(year, month, day, tzinfo=pytz.timezone(tz_string))

        # Set target hour
        if time_results.group(1) == None:
            # TODO Input is missing an hour, error and return.
            return
        hour = int(time_results.group(1))

        # Set target minute.
        if time_results.group(2):
            minute = int(time_results.group(2))
        else:
            # If there is no minute we assume the user means an even hour.
            minute = 0

        # Deal with am / pm bullshit:
        # 12h time format is scuffed asf, 12am is midnight, 12pm is midday.
        # This fixes that by removing 12h if we are at midnight or midday.
        if time_results.group(3) == "am" and hour == 12:
            hour = 0
        if time_results.group(3) == "pm" and not hour == 12:
            hour += 12
        
        #! TODO, check so hour and minute is within 24 and 60 spans.

        # Replaces the time on the current date with the given one
        given_tz_obj = given_tz_obj.replace(hour = hour, minute = minute)

        # Convert timezones and output to user
        user_tz = db.get_tz(interaction.user.id)
        target_tz_obj = given_tz_obj.astimezone(pytz.timezone(user_tz))

        await interaction.response.send_message(f"**{target_tz_obj.strftime('%H:%M')}** local time\n({time_string} in {tz_string} timezone)")
        #! TODO; MAKE EMBED (original time & timezone be footer?)
        #! TODO; check if it's +1 day
        #! TODO; ALSO ADD DISCORD TIMESTAMP



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
        #! TODO; MAKE EMBED
    
    @tzgroup.command()
    async def get(self, interaction:discord.Interaction):
        """Displays what your current set timezone is

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
        """        
        await interaction.response.send_message(f"Your set timezone is {db.get_tz(interaction.user.id)}")
        #! TODO; MAKE EMBED (and also ephemeral)
    
async def setup(bot: commands.Bot) -> None:
    print(f"\tcogs.timezone_handler begin loading")
    await bot.add_cog(TimezoneHandler(bot))