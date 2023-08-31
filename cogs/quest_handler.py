# -*- coding: UTF-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
import discord.utils
# traceback is for error logging
import traceback
# webcolors is needed to take colour names and make them into a hex value
import webcolors
import db_handler as db
from helpers import QuestInfo


# -----------------------STATIC VARS----------------------
# VS Code is annoying and runs the code in the home directory. This shouldn't be requred once I actually run the code as a standalone
# Then I should just change this to "."
FILE_LOCATION = "."


# --------------------PERSISTENT VIEWS--------------------
class PersistentQuestJoinView(discord.ui.View):
    # View for the join quest button.
    def __init__(self, info: QuestInfo, disabled: bool = False) -> None:
        self.quest_id = db.get_quest_by_title(info.quest_title)[0]
        self.info = info
        # create the button here since I need access to self.info for the
        # custom_id.
        self.join_button = discord.ui.button(
            label="Join Quest",
            style=discord.ButtonStyle.primary,
            custom_id=f"quest:{info.thread_id}-{info.quest_title}",
            disabled=disabled)(
            PersistentQuestJoinView.quest_join)
        # not sure what this does tbh, but I'm scared to remove it
        super().__init_subclass__()
        # set timeout to zero which is needed for a persistent view
        super().__init__(timeout=None)

    # The callback function for self.join_button, it is added where the Button
    # is defined.
    async def quest_join(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        dm_role = discord.utils.get(interaction.guild.roles, name="Dm")

        # get thread and role of quest
        role = interaction.guild.get_role(self.info.quest_role_id)
        thread = interaction.guild.get_thread(self.info.thread_id)
        # check if user has the quest role
        if role in interaction.user.roles:
            # if user has role, remove it and remove from quest
            await interaction.user.remove_roles(role)
            await thread.remove_user(interaction.user)
            await interaction.response.defer()
            # if the user isn't a dm remove them from the player list
            if dm_role in interaction.user.roles:
                return
            self.info.remove_player(interaction.user.id)
        else:
            # if user doesn't have role, add it and add user to the thread
            await interaction.user.add_roles(role)
            await thread.add_user(interaction.user)
            await interaction.response.defer()
            # if the user isn't a dm, add them to the player list
            if dm_role in interaction.user.roles:
                return
            self.info.add_player(interaction.user.id)
        namestring = ""
        for player_id in self.info._players:
            name = interaction.guild.get_member(player_id).display_name
            quests_played = db.get_player(player_id)
            namestring += f"`{name}`: {quests_played}\n"
        await interaction.channel.get_partial_message(self.info.pin_message_id).edit(embed=discord.Embed(title="Players:", description=namestring, color=discord.Color.from_str(self.info.embed_colour)))
        db.update_quest(self.quest_id, self.info)


# ------------------------MODALS--------------------------
class CreateQuest(discord.ui.Modal, title="Create Quest"):
    # The modal that shows up when you want to create a quest.
    quest_title = discord.ui.TextInput(
        label="Quest title",
        placeholder="Quest title here..."
    )

    contractor = discord.ui.TextInput(
        label="Contractor",
        placeholder="In game questgiver here..."
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Quest description here...",
        style=discord.TextStyle.long,
        max_length=1800
    )

    reward = discord.ui.TextInput(
        label="Reward",
        placeholder="Quest reward here..."
    )

    embed_colour = discord.ui.TextInput(
        label="Embed Colour",
        default="Teal"
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        # create embed for the message (with error handling for the colour
        # selection).
        try:
            embed_colour = webcolors.name_to_hex(self.embed_colour.value)
        except ValueError:
            # error handling for misspellt or non-existing colour name
            await interaction.response.send_message(f'Colour name "{self.embed_colour.value}" either non-existent or misspellt, please try again', ephemeral=True)
            return

        embed = discord.Embed(
            title=self.quest_title.value,
            description=self.description.value,
            color=discord.Color.from_str(
                embed_colour))
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.avatar.url)
        embed.add_field(
            name="Contractor",
            value=self.contractor.value,
            inline=True)
        embed.add_field(name="Reward", value=self.reward.value, inline=True)

        # create the quest role with the name of the quest title
        quest_role = await interaction.guild.create_role(name=self.quest_title.value, mentionable=True, reason="New Quest created")

        # send the actual message with the quest info
        msg = await interaction.channel.send(embed=embed)

        # create & attatch the thread to the newly created quest info message
        thread = await msg.create_thread(name=self.quest_title.value, auto_archive_duration=10080)

        # send the player amount message in the thread and pin it
        pin_message: discord.Message = await thread.send(embed=discord.Embed(title="Players:", color=discord.Color.from_str(embed_colour)))
        await pin_message.pin()

        # update the QuestInfo in memory
        quest = QuestInfo(self.quest_title.value,
                          self.contractor.value,
                          self.description.value,
                          self.reward.value,
                          embed_colour,
                          thread.id,
                          quest_role.id,
                          pin_message.id)

        db.create_quest(msg.id, quest)

        # set the quest join button to appear under the joined players list
        await pin_message.edit(view=PersistentQuestJoinView(quest))
        await interaction.response.defer()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Something went wrong, please try again.", ephemeral=True)

        # make sure we know what the error is
        traceback.print_tb(error.__traceback__)


class EditQuest(discord.ui.Modal, title="Edit Quest"):
    # The modal that shows up when you want to edit a quest.
    def __init__(self, message: discord.Message) -> None:
        super().__init__()
        self.message = message
        self.quest_info: QuestInfo = db.get_quest(self.message.id)
        self.quest_title.default = self.quest_info.quest_title
        self.contractor.default = self.quest_info.contractor
        self.description.default = self.quest_info.description
        self.reward.default = self.quest_info.reward
        self.embed_colour.default = webcolors.hex_to_name(
            self.quest_info.embed_colour)

    quest_title = discord.ui.TextInput(
        label="Quest title",
        placeholder="Quest title here..."
    )

    contractor = discord.ui.TextInput(
        label="Contractor",
        placeholder="In game questgiver here..."
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Quest description here...",
        style=discord.TextStyle.long,
        max_length=1800
    )

    reward = discord.ui.TextInput(
        label="Reward",
        placeholder="Quest reward here..."
    )

    embed_colour = discord.ui.TextInput(
        label="Embed Colour",
        default="Teal"
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        thread_id = self.quest_info.thread_id
        quest_role_id = self.quest_info.quest_role_id

        try:
            self.embed_colour = webcolors.name_to_hex(self.embed_colour.value)
        except ValueError:
            # error handling for misspellt or non-existing colour name
            await interaction.response.send_message(f'Colour name "{self.embed_colour.value}" either non-existent or misspellt, please try again', ephemeral=True)
            return
        embed = discord.Embed(
            title=self.quest_title.value,
            description=self.description.value,
            color=discord.Color.from_str(self.embed_colour))
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.avatar.url)
        embed.add_field(
            name="Contractor",
            value=self.contractor.value,
            inline=True)
        embed.add_field(name="Reward", value=self.reward.value, inline=True)
        await self.message.edit(embed=embed)

        # edit thread and role names
        thread = self.message.channel.get_thread(thread_id)
        await thread.edit(name=self.quest_title.value)
        await self.message.guild.get_role(quest_role_id).edit(name=self.quest_title.value)

        quest = QuestInfo(self.quest_title.value,
                          self.contractor.value,
                          self.description.value,
                          self.reward.value,
                          self.embed_colour,
                          thread_id,
                          quest_role_id,
                          self.quest_info.pin_message_id,
                          self.quest_info.players
                          )
        db.update_quest(self.message.id, quest)
        await thread.get_partial_message(self.quest_info.pin_message_id).edit(view=PersistentQuestJoinView(quest))
        await interaction.response.defer()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Something went wrong, please try again.", ephemeral=True)

        # make sure we know what the error is
        traceback.print_tb(error.__traceback__)


class DelQuest(discord.ui.Modal, title="Delete Quest"):
    # The confirmation modal that shows up when you want to delete a quest.
    def __init__(self, message: discord.Message) -> None:
        super().__init__()
        self.message = message
        self.quest_info: QuestInfo = db.get_quest(self.message.id)
        if len(self.quest_info.quest_title) < 16:
            self.title = f"Delete Quest {self.quest_info.quest_title}"
            self.confirmation.label = f'Type questname: "{self.quest_info.quest_title}" to confirm'
        else:
            self.confirmation.label = f'Type quest name to confirm'
        self.confirmation.max_length = len(self.quest_info.quest_title)

    msg_del_flag = discord.ui.TextInput(
        style=discord.TextStyle.short,
        max_length=3,
        label="Delete quest message? (yes/no)",
        default="no"
    )

    thread_del_flag = discord.ui.TextInput(
        style=discord.TextStyle.short,
        max_length=3,
        label="Delete quest thread? (yes/no)",
        default="no"
    )

    confirmation = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Retype quest name to confirm"
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not self.confirmation.value.lower() == self.quest_info.quest_title.lower():
            await interaction.response.send_message("Quest delete confiramation failed, names did not match.", ephemeral=True)
            return

        if not self.msg_del_flag.value.lower(
        ) == "yes" and not self.msg_del_flag.value.lower() == "no":
            await interaction.response.send_message("Message deletion flag has to be yes or no", ephemeral=True)
            return

        if not self.thread_del_flag.value.lower(
        ) == "yes" and not self.thread_del_flag.value.lower() == "no":
            await interaction.response.send_message("Thread deletion flag has to be yes or no", ephemeral=True)
            return

        thread = interaction.guild.get_thread(self.quest_info.thread_id)

        # if we should delete the thread, do so
        if self.thread_del_flag.value.lower() == "yes":
            await thread.delete()
        else:
            # Send quests played embed and lock the quest
            embed = await _get_all_quests_played(thread, self.quest_info)
            await thread.send(embed=embed)
            await thread.edit(locked=True, archived=True)

        # del role
        await interaction.guild.get_role(self.quest_info.quest_role_id).delete()

        # del quest
        db.del_quest(self.message.id)

        await interaction.response.send_message(f"Quest {self.quest_info.quest_title} removed!", ephemeral=True)

        # if we should delete the message, delete it
        if self.msg_del_flag.value.lower() == "yes":
            await self.message.delete()
        # otherwise, disable the join quest button
        else:
            disabled_view = PersistentQuestJoinView(
                self.quest_info, disabled=True)
            await thread.get_partial_message(self.quest_info.pin_message_id).edit(view=disabled_view)
            # stop the persistent view to stop wasting resources
            disabled_view.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Something went wrong, please try again.", ephemeral=True)

        # make sure we know what the error is
        traceback.print_tb(error.__traceback__)


class SetQuestAmount(discord.ui.Modal, title="Set Quests Played"):
    # The modal that lets you set the amount of quests played by a certain
    # player.
    def __init__(self, user=discord.Member):
        super().__init__()
        self.user = user
        self.player.label = f'{user.display_name} quest count:'
        self.player.default = db.get_player(user.id)

    player = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="quests played by user"
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            amount = int(self.player.value)
            db.update_player(self.user.id, amount)
            await interaction.response.send_message(f"Updated amount of quests for player {self.user.display_name} to be {self.player.value}")
        except ValueError:
            await interaction.response.send_message(f'"{self.player.value}" is not a number')

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Something went wrong, please try again.", ephemeral=True)

        # make sure we know what the error is
        traceback.print_tb(error.__traceback__)

# -----------------------MAIN CLASS-----------------------


class QuestHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ctx_edit_quest = app_commands.ContextMenu(
            name="Edit Quest", callback=self.edit_quest)
        self.ctx_del_quest = app_commands.ContextMenu(
            name="Delete Quest", callback=self.del_quest)
        self.ctx_get_quests_played = app_commands.ContextMenu(
            name="Get quests played", callback=self.get_quests_played)
        self.ctx_set_quests_played = app_commands.ContextMenu(
            name="Set quests played", callback=self.set_quests_played)

        self.bot.tree.add_command(self.ctx_edit_quest)
        self.bot.tree.add_command(self.ctx_del_quest)
        self.bot.tree.add_command(self.ctx_get_quests_played)
        self.bot.tree.add_command(self.ctx_set_quests_played)

    @app_commands.command(description="Make a Quest")
    async def create_quest(self, interaction: discord.Interaction) -> None:
        """Command to create a new quest (/create_quest), should be locked to DM role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
        """
        await interaction.response.send_modal(CreateQuest())

    @app_commands.command(
        description="Get amount of quests played for all users in the channel")
    async def get_all_quests_played(self, interaction: discord.Interaction) -> None:
        """Command to get how many quests players in a channel have played (/get_all_quests_played).
        Should be locked to DM role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
        """
        embed = await _get_all_quests_played(interaction.channel)
        await interaction.response.send_message(embed=embed)

    async def get_quests_played(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """Command to get the quests played by a specific user, doesn't have to be locked to DM role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
            user (discord.Member): The user who the command should run on, is also passed automatically.
        """
        quests = db.get_player(user.id)
        await interaction.response.send_message(f"{user.display_name} has played {quests} quests")

    async def set_quests_played(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """Command that sets amount of quests played by a specific user, should be locked to some sort of admin role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically
            user (discord.Member): The user who the commmand should un on, is also passed automatically.
        """
        await interaction.response.send_modal(SetQuestAmount(user))

    @app_commands.command(
        description="Increments the quest played count for all players in the thread")
    async def update_quest_count(self, interaction: discord.Interaction) -> None:
        """A command to increment the quests played by all users in a thread (/update_quest_count).
        Should be locked to dm role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
        """
        if interaction.channel.type == discord.ChannelType.public_thread:

            quest_info = db.get_quest_by_thread_id(interaction.channel.id)[1]
            embed = await _get_all_quests_played(interaction.channel, quest_info, True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("This channel is not a quest thread and thus the command can't be used", ephemeral=True)

    async def edit_quest(self, interaction: discord.Interaction, message: discord.Message) -> None:
        """Command to edit a quest (right click and edit quest), should be locked to DM role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
            message (discord.Message): The quest message the command should run on, also passed automatically.
        """
        await interaction.response.send_modal(EditQuest(message))

    async def del_quest(self, interaction: discord.Interaction, message: discord.Message) -> None:
        """Command to delete quest from memory and storage (right click and del_quest),
        should be locked to DM role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
            message (discord.Message): The quest message the command should run on, also passed automatically.
        """
        await interaction.response.send_modal(DelQuest(message))


# ---------------------OTHER FUNCTIONS--------------------
async def _get_all_quests_played(channel, quest_info: QuestInfo = None, increment: bool = False) -> discord.Embed:
    """Returns an Embed containing all players in a channel, along with how many quests they've played.
    THIS USES AN API CALL TO DISCORD, handle with care.

    Args:
        channel (any discord channel): The channel to check for players in.
        quest_info (QuestInfo, optional): Contains info about the quest, such as colour of the embed. Defaults to None.
        increment (bool, optional): whether or not to increment the players quest count. Defaults to False.

    Returns:
        discord.Embed: An embed with all players in a channel along with how many quests they've played.
    """
    player_role = discord.utils.get(channel.guild.roles, name="Player")
    players = {}
    namestring = ""

    # If we are passed a quest_info object we already have a list of players
    # we can grab, and thus less api calls
    if quest_info:
        members_in_channel = []
        player_list = quest_info._players

        # Check so that we don't have over 20 players in the quest, which would
        # warrant pure fear for other reasons, but eh
        if len(player_list) > 20:
            return discord.Embed(
                title="Quests Played:",
                description="Too many players in channel (more than 20)",
                color=discord.Color.from_str("#ffffff")
            )
        for player in player_list:
            members_in_channel.append(channel.guild.get_member(player))

    else:
        if channel.type == discord.ChannelType.public_thread:
            # fetch_members is an api call to discord, which isn't great, but I
            # couldn't find a better solution, and this *shouldn't* be too bad...
            # hopefully
            members_in_channel = await channel.fetch_members()
        else:
            members_in_channel = channel.members

    if len(members_in_channel) > 20:
        return discord.Embed(
            title="Quests Played:",
            description="Too many players in channel (more than 20)",
            color=discord.Color.from_str("#ffffff")
        )
    for player in members_in_channel:
        player = channel.guild.get_member(player.id)
        if player_role not in player.roles:
            continue
        if increment:
            quests_played = db.get_player(player.id) + 1
            db.update_player(player.id, quests_played)
        else:
            quests_played = db.get_player(player.id)

        players[player] = quests_played
        namestring += f"{player.display_name}: {quests_played}\n"
    if quest_info is None:
        embed_colour = "#ffffff"
    else:
        embed_colour = quest_info.embed_colour
    return discord.Embed(
        title="Quests Played:",
        description=namestring,
        color=discord.Color.from_str(embed_colour))

# ----------------------MAIN PROGRAM----------------------
# This setup is required for the cog to setup and run,
# and is run when the cog is loaded with bot.load_extensions()


async def setup(bot: commands.Bot) -> None:
    print(f"\tcogs.quest_handler begin loading")

    print("\t\tQuests in database:")
    quests = db.get_quest_list()
    for quest in quests:
        bot.add_view(PersistentQuestJoinView(quest))
        print(f"\t\t\t{quest.quest_title}")
    if not quests:
        print(f"\t\t\tNo quests in db!")

    await bot.add_cog(QuestHandler(bot))
