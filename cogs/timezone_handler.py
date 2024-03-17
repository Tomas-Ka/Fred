from discord.ext import commands
from discord import app_commands
import discord
from re import match
import db_handler as db
import pytz
from datetime import datetime
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
    async def time(self, interaction: discord.Interaction, time_string: str, date: str = None, tz_string: str = None) -> None:
        
        """Makes a discord timestamp of the given time

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
            time_string (str): 24h or 12h time, with or without minutes.
            date (str): A date in dd/mm/yy, dd/mm-yy or dd-mm-yy with one or two digits for d and m, and two or four digits for y.
            tz_string (str): The timezone of the given time (to use instead of your timezone)
        """
        time_results = match("(\d{1,2}):*(\d{1,2})*(am|pm)*", time_string)
        if time_results == None or time_results.group(1) == None:
            # TODO Time input string improperly formatted, error and return.
            return
        
        hour = int(time_results.group(1))

        # Deal with am / pm bullshit:
        # 12h time format is scuffed asf, 12am is midnight, 12pm is midday.
        # This fixes that by removing 12h if we are at midnight or midday.
        if time_results.group(3) == "am" and hour == 12:
            hour = 0
        if time_results.group(3) == "pm" and not hour == 12:
            hour += 12
        hour = hour % 24

        if time_results.group(2):
            minute = int(time_results.group(2))
        else:
            # If there is no minute we assume the user means an even hour.
            minute = 0
        minute = minute % 60


        if tz_string == None:
            tz_string = db.get_tz(interaction.user.id)

        if not tz_string in self.timezones:
            # TODO Timezone input does not exist, error and return. (Make embed, and ephemeral)
            await interaction.response.send_message(f"{tz_string} is not a valid timezone.")
            return

        # Here we hack in "servertime" for FFXIV, because I'm totally not addicted and this entire
        # cog was totally not written just to save me the annoyance of converting to and fro...
        if tz_string.lower() == "st":
            tz_string = "UTC"

        tz_object = datetime.now(tz=pytz.timezone(tz_string))
        if not date == None:
            date_results = match("(\d{1,2})[-\/](\d{1,2})[-\/]?(\d{2,4})?", date)
            if date_results == None:
                # TODO Error, date format invalid
                return
            day = int(date_results.group(1))
            month = int(date_results.group(2))
            year_string = date_results.group(3)
            if year_string:
                if len(year_string) == 2:
                    year_string = "20" + year_string
                year = int(year_string)
            else:
                year = tz_object.year
            try:
                tz_object = datetime(year, month, day, tzinfo=pytz.timezone(tz_string))
                print(tz_object.minute)
            except ValueError:
                # TODO Error, day or month is too large
                return

        tz_object = tz_object.replace(hour = hour, minute = minute)
        print(tz_object.minute)
        new_time = tz_object.astimezone(pytz.timezone("UTC"))
        print(new_time.minute)
        utc_timestamp = int(tz_object.astimezone(pytz.timezone("UTC")).timestamp())
        print(utc_timestamp)
        #! There is some strange error here which increases our minutes by 7 when a date is given... Will have to check properly
        
        embed=discord.Embed(title=f"<t:{utc_timestamp}:t>")
        embed.set_footer(text=f"original time: {time_string} in {tz_string} timezone")
        await interaction.response.send_message(embed=embed)



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
            embed=discord.Embed(title="Timezone update failed", description=f"{tz_string} is not a valid timezone.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Here we hack in "servertime" for FFXIV, because I'm totally not addicted and this entire
        # cog was totally not written just to save me the annoyance of converting to and fro...
        if tz_string.lower() == "st":
            tz_string = "UTC"
        
        db.set_tz(interaction.user.id, tz_string)
        embed=discord.Embed(title="Timezone update", description=f"Set your timezone to {tz_string}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @tzgroup.command()
    async def get(self, interaction:discord.Interaction):
        """Displays what your current set timezone is

        Args:
            interaction (discord.Interaction): The discord Interaction object that's passed automatically.
        """
        embed=discord.Embed(title="Timezone", description=f"Your set timezone is {db.get_tz(interaction.user.id)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
async def setup(bot: commands.Bot) -> None:
    print(f"\tcogs.timezone_handler begin loading")
    await bot.add_cog(TimezoneHandler(bot))