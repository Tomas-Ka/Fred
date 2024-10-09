import discord
from discord.ext import commands
from discord import app_commands
from os import environ

BOARD_RECEIPTS_CHANNEL_ID = environ["BOARD_RECEIPTS_CHANNEL"]


class SendInReceiptModal(discord.ui.Modal):
    def __init__(self):
        super().__init__()
        pass


class ReceiptsHandler(commands.Cog):
    bot: commands.Bot

    def __init__(self, bot):
        self.bot = bot
        self.board_receipts_channel = bot.get_channel(BOARD_RECEIPTS_CHANNEL_ID)

    @app_commands.guild_only()
    @app_commands.command(description="Upload a receipt")
    async def upload_receipt(self,
                             interaction: discord.Interaction,
                             receipt_image: discord.Attachment,
                             name: str,
                             total: int,
                             phone_number: int):
        """
        Command to upload receipts
        """
        embed = discord.Embed()
        embed.title = "Receipt"
        embed.set_author(name=interaction.user.name,
                         icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="",
                        value=f"""name: {name}
                        total: {total}
                        number: {phone_number}""")
        embed.set_image(url=receipt_image.url)

        await self.bot.get_channel(int(BOARD_RECEIPTS_CHANNEL_ID)).send(embed=embed)
        await interaction.response.send_message(embed=embed)


# ----------------------MAIN PROGRAM----------------------
# This setup is required for the cog to setup and run,
# and is run when the cog is loaded with bot.load_extensions().
async def setup(bot: commands.Bot) -> None:
    print("\tcogs.receipts_handler begin loading")
    await bot.add_cog(ReceiptsHandler(bot))
