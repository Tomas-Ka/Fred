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

# --------------------PERSISTENT VIEWS--------------------


class PersistentQuestJoinView(discord.ui.View):
    # View for the join quest button.
    def __init__(
            self,
            info: QuestInfo,
            quest_id=int,
            disabled: bool = False) -> None:
        self.quest_id = quest_id
        self.info = info

        # Create the button here since I need access to self.info for the
        # custom_id.
        self.join_button = discord.ui.button(
            label="Join Quest",
            style=discord.ButtonStyle.primary,
            custom_id=f"quest:{info.thread_id}-{info.quest_title}",
            disabled=disabled)(
            PersistentQuestJoinView.quest_join)
        # Not sure what this does tbh, but I'm scared to remove it...
        super().__init_subclass__()

        # Set timeout to zero which is needed for a persistent view.
        super().__init__(timeout=None)

     # Callback for the join button, is linked in init where the button is
     # defined.
    async def quest_join(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        dm_role = discord.utils.get(interaction.guild.roles, name="Dm")

        # Get thread and role of quest.
        role = interaction.guild.get_role(self.info.quest_role_id)
        thread = interaction.guild.get_thread(self.info.thread_id)
        # Check if user has the quest role.
        if role in interaction.user.roles:
            # If user has role, remove it and remove from quest.
            await interaction.user.remove_roles(role)
            await thread.remove_user(interaction.user)
            await interaction.response.defer()

            # If the user isn't a dm remove them from the player list.
            if dm_role in interaction.user.roles:
                return
            self.info.remove_player(interaction.user.id)
        else:
            # If user doesn't have role, add it and add user to the thread.
            await interaction.user.add_roles(role)
            await thread.add_user(interaction.user)
            await interaction.response.defer()

            # If the user isn't a dm, add them to the player list.
            if dm_role in interaction.user.roles:
                return
            self.info.add_player(interaction.user.id)
        namestring = ""

        # Update the quest list message to reflect all players currently in the
        # quest.
        for player_id in self.info._players:
            name = interaction.guild.get_member(player_id).display_name
            quests_played = await db.get_player(interaction.guild_id, player_id)
            namestring += f"`{name}`: {quests_played}\n"

        # Send the quest list message and update database to reflect new data:
        await interaction.channel.get_partial_message(self.info.pin_message_id).edit(embed=discord.Embed(title="Players:", description=namestring, color=discord.Color.from_str(self.info.embed_colour)))
        await db.update_quest(self.quest_id, self.info)


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
        # Create embed for the message (with error handling for the colour
        # selection and checking if we already have a quest with the same
        # name).
        try:
            raw_colour_value = self.embed_colour.value
            embed_colour = webcolors.name_to_hex(raw_colour_value)
        except ValueError:
            # Error handling for misspellt or non-existing colour name.
            message = f"""Colour name "{raw_colour_value}" either non-existent or misspellt, please try again.

            Here is your quest info:

            **Title:** {self.quest_title.value}

            **Contractor:** {self.contractor.value}

            **Description:** {self.description.value}

            **Reward:** {self.reward.value}

            **Colour:** {raw_colour_value}"""

            await interaction.response.send_message(message, ephemeral=True)
            return

        # Make sure we don't have duplicate quest titles:
        if await db.get_quest_by_title(interaction.guild_id, self.quest_title.value):
            message = f"""The quest name "{self.quest_title.value}" is already in use, please try another name

            Here is your quest info:

            **Title:** {self.quest_title.value}

            **Contractor:** {self.contractor.value}

            **Description:** {self.description.value}

            **Reward:** {self.reward.value}

            **Colour:** {raw_colour_value}"""

            await interaction.response.send_message(message, ephemeral=True)
            return

        # Create the quest embed for use later.
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

        # Create the quest role with the name of the quest title.
        quest_role = await interaction.guild.create_role(name=self.quest_title.value, mentionable=True, reason="New Quest created")

        # Send the actual message with the quest info.
        # (Check that the player role exists before we ping it):
        player_role = discord.utils.get(interaction.guild.roles, name="Player")
        if player_role:
            msg = await interaction.channel.send(content=f'<@&{player_role.id}>', embed=embed)
        else:
            msg = await interaction.channel.send(content="", embed=embed)

        # Create & attatch the thread to the newly created quest info message.
        thread = await msg.create_thread(name=self.quest_title.value, auto_archive_duration=10080)

        # Send the player amount message in the thread and pin it.
        pin_message: discord.Message = await thread.send(embed=discord.Embed(title="Players:", color=discord.Color.from_str(embed_colour)))
        await pin_message.pin()

        # Update the QuestInfo in memory.
        quest = QuestInfo(interaction.guild_id,
                          self.quest_title.value,
                          self.contractor.value,
                          self.description.value,
                          self.reward.value,
                          embed_colour,
                          thread.id,
                          quest_role.id,
                          pin_message.id)

        await db.create_quest(msg.id, quest)

        # Set the quest join button to appear under the joined players list.
        quest_id = (await db.get_quest_by_title(interaction.guild_id, quest.quest_title))[0]
        await pin_message.edit(view=PersistentQuestJoinView(quest, quest_id))
        await interaction.response.defer()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        try:
            message = f"""Something went wrong, please try again.

            Here is your quest info:

            **Title:** {self.quest_title.value}

            **Contractor:** {self.contractor.value}

            **Description:** {self.description.value}

            **Reward:** {self.reward.value}

            **Colour:** {self.embed_colour.value}"""

            await interaction.response.send_message(message, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Something went wrong, please try again.", ephemeral=True)

        # Make sure we know what the error is.
        traceback.print_tb(error.__traceback__)


class EditQuest(discord.ui.Modal, title="Edit Quest"):
    # The modal that shows up when you want to edit a quest.
    def __init__(self, message: discord.Message,
                 quest_info: QuestInfo) -> None:
        super().__init__()
        self.message = message
        self.quest_info = quest_info
        self.quest_title.default = self.quest_info.quest_title
        self.old_title = self.quest_info.quest_title
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

        # Checking to make sure our inputs are valid:

        try:
            raw_colour_value = self.embed_colour.value
            self.embed_colour = webcolors.name_to_hex(raw_colour_value)
        except ValueError:
            # Error handling for misspellt or non-existing colour name.
            message = f"""Colour name "{raw_colour_value}" either non-existent or misspellt, please try again.

            Here is your quest info:

            **Title:** {self.quest_title.value}

            **Contractor:** {self.contractor.value}

            **Description:** {self.description.value}

            **Reward:** {self.reward.value}

            **Colour:** {raw_colour_value}"""

            await interaction.response.send_message(message, ephemeral=True)
            return

        # Make sure we don't have duplicate quest titles.
        if not self.quest_title.value == self.old_title:
            if await db.get_quest_by_title(interaction.guild_id, self.quest_title.value):
                message = f"""The quest name "{self.quest_title.value}" is already in use, please try another name

                Here is your quest info:

                **Title:** {self.quest_title.value}

                **Contractor:** {self.contractor.value}

                **Description:** {self.description.value}

                **Reward:** {self.reward.value}

                **Colour:** {raw_colour_value}"""

                await interaction.response.send_message(message, ephemeral=True)
                return

        # Create the quest embed for use later.
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

        # Check that the player role exists before we ping it:
        player_role = discord.utils.get(interaction.guild.roles, name="Player")
        if player_role:
            await self.message.edit(content=f'<@&{player_role.id}>', embed=embed)
        else:
            await self.message.edit(content="", embed=embed)

        # Edit thread and role names.
        thread = self.message.channel.get_thread(thread_id)
        await thread.edit(name=self.quest_title.value)
        await self.message.guild.get_role(quest_role_id).edit(name=self.quest_title.value)

        quest = QuestInfo(interaction.guild_id,
                          self.quest_title.value,
                          self.contractor.value,
                          self.description.value,
                          self.reward.value,
                          self.embed_colour,
                          thread_id,
                          quest_role_id,
                          self.quest_info.pin_message_id,
                          self.quest_info.players
                          )
        await db.update_quest(self.message.id, quest)
        quest_id = (await db.get_quest_by_title(interaction.guild_id, quest.quest_title))[0]
        await thread.get_partial_message(self.quest_info.pin_message_id).edit(view=PersistentQuestJoinView(quest, quest_id))
        await interaction.response.defer()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        try:
            message = f"""Something went wrong, please try again.

            Here is your quest info:

            **Title:** {self.quest_title.value}

            **Contractor:** {self.contractor.value}

            **Description:** {self.description.value}

            **Reward:** {self.reward.value}

            **Colour:** {self.embed_colour.value}"""

            await interaction.response.send_message(message, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Something went wrong, please try again.", ephemeral=True)

        # Make sure we know what the error is.
        traceback.print_tb(error.__traceback__)


class DelQuest(discord.ui.Modal, title="Delete Quest"):
    # The confirmation modal that shows up when you want to delete a quest.
    def __init__(self, message: discord.Message,
                 quest_info: QuestInfo) -> None:
        super().__init__()
        self.message = message
        self.quest_info = quest_info
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
            await interaction.response.send_message("Quest delete confirmation failed, names did not match.", ephemeral=True)
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

        # If we should delete the thread, do so.
        if self.thread_del_flag.value.lower() == "yes":
            await thread.delete()
        else:
            # Send quests played embed and lock the quest.
            embed = await _get_all_quests_played(thread, self.quest_info)
            await thread.send(embed=embed)
            await thread.edit(locked=True, archived=True)

        # Delete role.
        await interaction.guild.get_role(self.quest_info.quest_role_id).delete()

        # Delete quest.
        await db.del_quest(self.message.id)

        await interaction.response.send_message(f"Quest {self.quest_info.quest_title} removed!", ephemeral=True)

        # If we should delete the message, delete it.
        if self.msg_del_flag.value.lower() == "yes":
            await self.message.delete()

        # If not, disable the join quest button.
        else:
            quest_id = (await db.get_quest_by_title(interaction.guild_id, self.quest_info.quest_title))[0]
            disabled_view = PersistentQuestJoinView(
                self.quest_info, quest_id, disabled=True)
            await thread.get_partial_message(self.quest_info.pin_message_id).edit(view=disabled_view)

            # Stop the persistent view to stop wasting resources (and potential
            # memory leak? maybe?).
            disabled_view.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Something went wrong, please try again.", ephemeral=True)

        # Make sure we know what the error is.
        traceback.print_tb(error.__traceback__)


class SetQuestAmount(discord.ui.Modal, title="Set Quests Played"):
    # The modal that lets you set the amount of quests played by a certain
    # player.
    def __init__(self, user: discord.Member, current_quest_run: int):
        super().__init__()
        self.user = user
        self.player.label = f'{user.display_name} quest count:'
        self.player.default = current_quest_run

    player = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="quests played by user"
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        # Try to update the player and error if the value supplied isn't a
        # number.
        try:
            amount = int(self.player.value)
            await db.update_player(interaction.guild_id, self.user.id, amount)
            await interaction.response.send_message(f"Updated amount of quests for player {self.user.display_name} to be {self.player.value}")
        except ValueError:
            await interaction.response.send_message(f'"{self.player.value}" is not a number')

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Something went wrong, please try again.", ephemeral=True)

        # Make sure we know what the error is.
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

        # Make sure these commands are only available in servers (and not DMs).
        self.ctx_edit_quest.guild_only = True
        self.ctx_del_quest.guild_only = True
        self.ctx_get_quests_played.guild_only = True
        self.ctx_set_quests_played.guild_only = True

        # Set default permissions required to use the given commands:
        self.ctx_edit_quest.default_permissions = discord.Permissions(
            manage_events=True, manage_messages=True, create_public_threads=True)
        self.ctx_del_quest.default_permissions = discord.Permissions(
            manage_events=True, manage_messages=True, create_public_threads=True)

        self.ctx_set_quests_played.default_permissions = discord.Permissions(
            manage_events=True, manage_messages=True, create_public_threads=True)

        # Actually add the commands to the bot:
        self.bot.tree.add_command(self.ctx_edit_quest)
        self.bot.tree.add_command(self.ctx_del_quest)
        self.bot.tree.add_command(self.ctx_get_quests_played)
        self.bot.tree.add_command(self.ctx_set_quests_played)

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_events=True,
                                      manage_messages=True,
                                      create_public_threads=True)
    @app_commands.command(description="Make a Quest")
    async def create_quest(self, interaction: discord.Interaction) -> None:
        """Command to create a new quest (/create_quest), should be locked to DM role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
        """
        await interaction.response.send_modal(CreateQuest())

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_events=True,
                                      manage_messages=True,
                                      create_public_threads=True)
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
        quests = await db.get_player(interaction.guild_id, user.id)
        await interaction.response.send_message(f"{user.display_name} has played {quests} quests")

    async def set_quests_played(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """Command that sets amount of quests played by a specific user, should be locked to some sort of admin role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically
            user (discord.Member): The user who the commmand should un on, is also passed automatically.
        """
        current_quests_run = await db.get_player(interaction.guild_id, user.id)
        await interaction.response.send_modal(SetQuestAmount(user, current_quests_run))

    @app_commands.default_permissions(manage_events=True,
                                      manage_messages=True,
                                      create_public_threads=True)
    @app_commands.command(
        description="Increments the quest played count for all players in the thread")
    async def update_quest_count(self, interaction: discord.Interaction) -> None:
        """A command to increment the quests played by all users in a thread (/update_quest_count).
        Should be locked to dm role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
        """
        if interaction.channel.type == discord.ChannelType.public_thread:
            quest_info = await db.get_quest_by_thread_id(interaction.channel.id)
            # Check to see if return is empty (aka the quest doesn't exist in
            # the database).
            if quest_info is not None:
                quest_info = quest_info[1]
            else:
                await interaction.response.send_message("Error\nThis is not a quest thread", ephemeral=True)
                return

            embed = await _get_all_quests_played(interaction.channel, quest_info, True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Error\nThis is not a quest thread", ephemeral=True)

    async def edit_quest(self, interaction: discord.Interaction, message: discord.Message) -> None:
        """Command to edit a quest (right click and edit quest), should be locked to DM role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
            message (discord.Message): The quest message the command should run on, also passed automatically.
        """
        quest = await db.get_quest(message.id)
        if (quest is None):
            # Quest does not exist, so we can return an error and skip the
            # modal.
            await interaction.response.send_message("Error\nThe selected message is not a quest message", ephemeral=True)
            return
        await interaction.response.send_modal(EditQuest(message, quest))

    async def del_quest(self, interaction: discord.Interaction, message: discord.Message) -> None:
        """Command to delete quest from memory and storage (right click and del_quest),
        should be locked to DM role.

        Args:
            interaction (discord.Interaction): The discord interaction obj that is passed automatically.
            message (discord.Message): The quest message the command should run on, also passed automatically.
        """
        quest = await db.get_quest(message.id)
        if (quest is None):
            # Quest does not exist, so we can return an error and skip the
            # modal.
            await interaction.response.send_message("Error\nThe selected message is not a quest message", ephemeral=True)
            return

        await interaction.response.send_modal(DelQuest(message, quest))


# ---------------------OTHER FUNCTIONS--------------------
async def _get_all_quests_played(channel: discord.TextChannel | discord.Thread, quest_info: QuestInfo = None, increment: bool = False) -> discord.Embed:
    """Returns an Embed containing all players in a channel, along with how many quests they've played.
    May cause fred to hit a rate limit if used too much, handle with care.

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
    # we can grab, and thus make less api calls.
    if quest_info:
        members_in_channel = []
        player_list = quest_info._players

        # Check so that we don't have over 20 players in the quest, which would
        # warrant pure fear for other reasons, but eh, it's fiiine.
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
            # Fetch_members is an api call to discord, which isn't great, but I
            # couldn't find a better solution, and this *shouldn't* be too bad...
            # Hopefully...
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
            quests_played = await db.get_player(channel.guild.id, player.id) + 1
            await db.update_player(channel.guild.id, player.id, quests_played)
        else:
            quests_played = await db.get_player(channel.guild.id, player.id)

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
# and is run when the cog is loaded with bot.load_extensions().


async def setup(bot: commands.Bot) -> None:
    print(f"\tcogs.quest_handler begin loading")

    print("\t\tQuests in database:")
    # Get all quests from the database and add their persistent
    # views to the bot one by one.
    quests = await db.get_all_quest_list()
    for quest in quests:
        quest_id = (await db.get_quest_by_title(quest.guild_id, quest.quest_title))[0]
        bot.add_view(PersistentQuestJoinView(quest, quest_id))
        print(f"\t\t\t{quest.quest_title}")
    if not quests:
        print(f"\t\t\tNo quests in db!")

    await bot.add_cog(QuestHandler(bot))
