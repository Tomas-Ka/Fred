from time import time

import discord
from discord.ext import commands


class WhaleHandler(commands.Cog):
    bot: commands.Bot

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.time: float = time()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        assert self.bot.user
        # This is only for the character sticky messages.
        # If the bot sent the message, ignore.
        if msg.author.id == self.bot.user.id:
            return
        if "🐋" in msg.content and "🥛" in msg.content:
            if self.time + 40 < time():
                await msg.add_reaction("👀")
                self.time = time()


# ----------------------MAIN PROGRAM----------------------
# This setup is required for the cog to setup and run,
# and is run when the cog is loaded with bot.load_extensions().
async def setup(bot: commands.Bot) -> None:
    print(f"\tcogs.whale_handler begin loading")
    await bot.add_cog(WhaleHandler(bot))
