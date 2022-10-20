# -*- coding: UTF-8 -*-
import discord
from discord.ext import commands
# traceback is for error logging
import traceback

from os import environ
from dotenv import load_dotenv

load_dotenv()
token = environ["TOKEN"]

# -----------------------STATIC VARS----------------------
# test guild, discord bot testing grounds
TEST_GUILD = discord.Object(752506220400607295)  # 538846461614489675


# -----------------------MAIN CLASS-----------------------
class FredBot(commands.Bot):
    def __init__(self, command_prefix: str) -> None:
        # set up intents and initialize the bot
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(
            intents=intents,
            command_prefix=command_prefix,
            description="DnD Discord Bot",
            activity=discord.Game(
                name="Here to help you roll absolute garbage"))

    async def on_ready(self) -> None:
        # login, probably want to log more info here
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def setup_hook(self) -> None:
        # do any data processing to get data into memory here

        # load cogs:
        print("loading cogs:")
        extensions = [
            'cogs.dice_roller',
            'cogs.quest_handler',
            'cogs.sticky_handler',
            'cogs.archive_handler',
            'cogs.whale_handler'
        ]

        for extension in extensions:
            try:
                await bot.load_extension(extension)
                print(f"\t{extension} loaded")
            except Exception as e:
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()

        # sync app commands with Discord
        # await self.tree.sync()
        # self.tree.copy_global_to(guild=TEST_GUILD)
        # await self.tree.sync(guild=TEST_GUILD)

# ------------------------MAIN CODE-----------------------


bot = FredBot(command_prefix="!")
bot.run(token)  # Fred
