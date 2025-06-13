from os import environ

import discord
from discord import app_commands
from discord.ext import commands

import db_handler as db

BOARD_RECEIPTS_CHANNEL_ID = environ["BOARD_RECEIPTS_CHANNEL"]


class ReceiptDenyModal(discord.ui.Modal):
    def __init__(
        self,
        user_id: int,
        receipt_name: str,
        interaction: discord.Interaction,
        message_id: int,
        message_jump: str,
    ) -> None:

        super().__init__(title="Deny Receipt")
        self.user_id = user_id
        self.receipt_name = receipt_name
        self.receipt_interaction = interaction
        self.message_id = message_id
        self.message_jump = message_jump

    reason = discord.ui.TextInput(
        label="Reason for denying Receipt", placeholder="type text here..."
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            return
        user = interaction.guild.get_member(self.user_id)
        if not user:
            return
        await user.send(
            f'Your receipt "{self.receipt_name}" has been checked and needs amending. The reason is: {self.reason.value}'
            + f"\nyou can find your receipt here: {self.message_jump}"
        )
        await interaction.response.send_message(
            f"{interaction.user} rejected receipt, reasoning: {self.reason.value}"
        )
        if not self.receipt_interaction.message:
            return
        await db.del_receipt_board(self.receipt_interaction.message.id)
        await self.receipt_interaction.message.edit(
            view=PublicMessageView(self.message_id, self.message_jump, True)
        )


class PublicMessageView(discord.ui.View):
    def __init__(
        self, message_id: int, message_jump: str, disabled: bool = False
    ) -> None:

        self.message_id = message_id
        self.message_jump = message_jump
        # Create the button here since I need access to self.info for the
        # custom_id.
        self.accept_button = discord.ui.button(
            label="Accept",
            style=discord.ButtonStyle.green,
            custom_id=str(f"{message_id}:accept"),
            disabled=disabled,
        )(PublicMessageView.accept_receipt)

        self.deny_button = discord.ui.button(
            label="Deny",
            style=discord.ButtonStyle.gray,
            custom_id=str(f"{message_id}:deny"),
            disabled=disabled,
        )(PublicMessageView.deny_receipt)

        # Not sure what this does tbh, but I'm scared to remove it...
        super().__init_subclass__()

        # Set timeout to zero which is needed for a persistent view.
        super().__init__(timeout=None)

    async def accept_receipt(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        # - TODO: fix actual web scraping / pushing here!
        if not interaction.message:
            return
        _embed = interaction.message.embeds[0]
        if _embed.image.url is not None:
            await interaction.message.edit(
                view=PublicMessageView(self.message_id, self.message_jump, True)
            )
            await db.del_receipt_board(interaction.message.id)

            await interaction.followup.send(f"{interaction.user} accepted receipt!")
        else:
            await interaction.followup.send(
                "Error, cannot find the image in that message!"
            )

    async def deny_receipt(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        embed = interaction.message.embeds[0]
        # await db.del_receipt_board(interaction.message.id)
        # await interaction.message.edit(view=PublicMessageView(self.message_id, True))
        await interaction.response.send_modal(
            ReceiptDenyModal(
                int(embed.author.url[8:-12]),
                embed.fields[0].name,
                interaction,
                self.message_id,
                self.message_jump,
            )
        )


class ReceiptsHandler(commands.Cog):
    bot: commands.Bot

    def __init__(self, bot):
        self.bot = bot
        self.board_receipts_channel = bot.get_channel(BOARD_RECEIPTS_CHANNEL_ID)

    @app_commands.guild_only()
    @app_commands.command(description="Upload a receipt")
    async def upload_receipt(
        self,
        interaction: discord.Interaction,
        receipt_image: discord.Attachment,
        name: str,
        total: int,
        phone_number: int,
    ):
        """
        Command to upload receipts
        """
        embed = discord.Embed()
        embed.title = "Receipt"
        embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.display_avatar.url,
            url=f"https://{interaction.user.id}.nonexistant",
        )
        embed.add_field(name=name, value=f"""total: {total} number: {phone_number}""")
        embed.set_image(url=receipt_image.url)

        await interaction.response.defer(thinking=False)

        public_msg: discord.Message = await interaction.followup.send(embed=embed)

        board_msg = await self.bot.get_channel(int(BOARD_RECEIPTS_CHANNEL_ID)).send(
            embed=embed, view=PublicMessageView(public_msg.id, public_msg.jump_url)
        )
        await db.create_receipt(public_msg.id, board_msg.id)


# ----------------------MAIN PROGRAM----------------------
# This setup is required for the cog to setup and run,
# and is run when the cog is loaded with bot.load_extensions().
async def setup(bot: commands.Bot) -> None:
    print("\tcogs.receipts_handler begin loading")

    receipts = await db.get_receipt_list()

    print("\t\tloading following receipts")
    if receipts:
        for receipt in receipts:
            print(f"\t\t\t{receipt[1]}")
            bot.add_view(PublicMessageView(receipt[0]))
    else:
        print("\t\t\tNo receipts in database")

    await bot.add_cog(ReceiptsHandler(bot))
