import asqlite
from sqlite3 import Error
import asyncio
from helpers import QuestInfo


global db_file
db_file = "db.sqlite"


async def _create_tables() -> None:
    """Initialization function to create the database if it doesn't exist yet.
    """
    create_quests_table = """
    CREATE TABLE IF NOT EXISTS quests (
        "id" INTEGER PRIMARY KEY NOT NULL,
        "guild_id" INTEGER NOT NULL,
        "quest_title" TEXT NOT NULL,
        "contractor" TEXT,
        "description" TEXT NOT NULL,
        "reward" TEXT,
        "embed_colour" TEXT NOT NULL,
        "thread_id" INTEGER NOT NULL,
        "quest_role_id" INTEGER NOT NULL,
        "pin_message_id" INTEGER NOT NULL,
        "players" BLOB
    );
    """
    await _execute_query(create_quests_table)

    create_stickies_table = """
    CREATE TABLE IF NOT EXISTS stickies (
        "channel_id" INTEGER UNIQUE,
        "message_id" INTEGER UNIQUE
    );
    """
    await _execute_query(create_stickies_table)

    create_players_table = """
    CREATE TABLE IF NOT EXISTS players (
        "guild_id" INTEGER NOT NULL,
        "player_id" INTEGER NOT NULL,
        "quests_completed" INTEGER
    );
    """
    await _execute_query(create_players_table)

    create_receipts_table = """
    CREATE TABLE IF NOT EXISTS receipts (
        "public_message_id" INTEGER NOT NULL,
        "board_message_id" INTEGER NOT NULL
    );
    """
    await _execute_query(create_receipts_table)

    print("all done, closing out!")


async def _execute_query(query: str, vars: tuple = ()) -> None:
    """Execute the given query in the globally defined database.

    Args:
        query (str): The query string.
        vars (tuple): The vars to replace the spots in the queary string.
    """
    async with asqlite.connect(db_file) as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(query, vars)
                await conn.commit()
            except Error as e:
                print(f"the error {e} occured")


async def _execute_multiple_read_query(query: list, vars: tuple = ()) -> list[tuple]:
    """Same as execute_query except it returns values,
    and is used for reading from the db.

    Args:
        query (str): The string to query the database with.
        vars (tuple): The vars to replace the spots in the queary string.

    Returns:
        list: a list containing all the data found from the query.
    """
    async with asqlite.connect(db_file) as conn:
        async with conn.cursor() as cursor:
            result = None
            try:
                await cursor.execute(query, vars)
                result = await cursor.fetchall()
                return result
            except Error as e:
                print(f"The error '{e}' occurred")


async def _execute_read_query(query: list, vars: tuple = ()) -> tuple:
    """Same as execute_read_query except it only returns a single value

    Args:
        query (str): The string to query the database with.
        vars (tuple): The vars to replace the spots in the queary string.

    Returns:
        tuple: A Touple containing the data at the found row.
    """
    async with asqlite.connect(db_file) as conn:
        async with conn.cursor() as cursor:
            result = None
            try:
                await cursor.execute(query, vars)
                result = await cursor.fetchone()
                return result
            except Error as e:
                print(f"The error '{e}' occurred")


async def get_quest(quest_id: int) -> QuestInfo:
    """Returns a quest given a quest id.

    Args:
        quest_id (int): The quest id to get from the database.

    Returns:
        QuestInfo: An object containing the data from the db.
    """
    quest_query = """
    SELECT * FROM quests
    WHERE id = ?;"""

    # This returns a list and we take the first object as there should only
    # ever be one due to unique constraints in the db.
    query_return = await _execute_read_query(quest_query, (quest_id,))

    # The first value returned is the id of the quest, which we don't want to
    # parse.
    if query_return:
        quest = QuestInfo(*query_return[1:])
        return quest
    return None


async def get_quest_by_title(guild_id: int, quest_title: str) -> tuple[int, QuestInfo]:
    """Returns a tuple containing the quest id
    and a questInfo object, given a quest title.

    Args:
        guild_id (int): The id of the discord guild to look for the quest in.
        quest_title (str): The quest name to get from the database.

    Returns:
        tuple[int, QuestInfo]: An object containing the data from the db.
    """
    quest_query = """
    SELECT * FROM quests
    WHERE
        quest_title = ?
    AND
        guild_id = ?;
    """

    # This returns a list and we take the first object as there should only
    # ever be one due to unique constraints in the db.
    query_return = await _execute_read_query(quest_query, (quest_title, guild_id,))
    if query_return:
        quest = QuestInfo(*query_return[1:])
        return (query_return[0], quest)
    return None


async def get_quest_by_thread_id(thread_id: int) -> tuple[int, QuestInfo]:
    """Returns a tuple containing the quest id
    and a questInfo object, given the id for the quest thread.

    Args:
        thread_id (int): The thread id search for in the database.

    Returns:
        tuple[int, QuestInfo]: An object containing the data from the db.
    """
    quest_query = """
    SELECT * FROM quests
    WHERE thread_id = ?;"""

    # This returns a list and we take the first object as there should only
    # ever be one due to unique constraints in the db.
    query_return = await _execute_read_query(quest_query, (thread_id,))

    # The first value returned is the id of the quest, which we don't want to
    # parse.

    if query_return:
        quest = QuestInfo(*query_return[1:])
        return (query_return[0], quest)
    return None


async def get_quest_list(guild_id: int) -> list[QuestInfo]:
    """Returns a list of all quests in the database

    Args:
        guild_id (int): The id of the discord guild to grab the quests for.

    Returns:
        list[QuestInfo]: The list of objects
    """

    quest_query = """
    SELECT * FROM quests
    WHERE guild_id = ?;
    """

    query_return = await _execute_multiple_read_query(quest_query, (guild_id,))
    quests = []
    if query_return:
        for quest in query_return:
            quests.append(QuestInfo(*quest[1:]))
    return quests


async def get_all_quest_list() -> list[QuestInfo]:
    """Returns a list of all quests in the database

    Returns:
        list[QuestInfo]: The list of objects
    """

    quest_query = """
    SELECT * FROM quests;
    """

    query_return = await _execute_multiple_read_query(quest_query)
    quests = []
    if query_return:
        for quest in query_return:
            quests.append(QuestInfo(*quest[1:]))
    return quests


async def create_quest(id: int, quest_info: QuestInfo) -> None:
    """Adds a quest to the db.

    Args:
        id (int): The message id the quest is linked to in both the database, and discord.
        quest_info (QuestInfo): The information to store in the database.
    """
    quest_add = """
    INSERT INTO
        quests (
        id, guild_id,
        quest_title, contractor,
        description, reward,
        embed_colour, thread_id,
        quest_role_id, pin_message_id
        )
    VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    vars = (
        id,
        quest_info.guild_id,
        quest_info.quest_title,
        quest_info.contractor,
        quest_info.description,
        quest_info.reward,
        quest_info.embed_colour,
        quest_info.thread_id,
        quest_info.quest_role_id,
        quest_info.pin_message_id,)

    await _execute_query(quest_add, vars)


async def update_quest(id: int, quest_info: QuestInfo) -> None:
    """Updates an already existing quest by id.

    Args:
        id (int): The id of the quest to update.
        quest_info (QuestInfo): The info to update the quest with.
    """
    quest_update = """
    UPDATE quests
    SET
        quest_title = ?,
        contractor = ?,
        description = ?,
        reward = ?,
        embed_colour = ?,
        thread_id = ?,
        quest_role_id = ?,
        pin_message_id = ?,
        players = ?
    WHERE
        id = ?
    AND
        guild_id = ?
    """
    vars = (
        quest_info.quest_title,
        quest_info.contractor,
        quest_info.description,
        quest_info.reward,
        quest_info.embed_colour,
        quest_info.thread_id,
        quest_info.quest_role_id,
        quest_info.pin_message_id,
        quest_info.players,
        id,
        quest_info.guild_id,
    )

    await _execute_query(quest_update, vars)


async def del_quest_by_title(guild_id: int, quest_title: str) -> None:
    """Remove a quest from the db given a quest title.

    Args:
        guild_id (int): The id of the discord guild to look for the quest in.
        quest_title (str): The title of the quest to remove.
    """
    quest_del = """
    DELETE FROM quests
    WHERE
        quest_title = ?
    AND
        guild_id = ?
    """
    await _execute_query(quest_del, (quest_title, guild_id,))


async def del_quest(id: int) -> None:
    """Remove a quest from the db given an id.

    Args:
        id (int): The id of the quest to remove.
    """
    quest_del = "DELETE FROM quests WHERE id = ?"
    await _execute_query(quest_del, (id,))


async def get_sticky(channel_id: int) -> int:
    """Returns a sticky given the id of the channel it's in.

    Args:
        channel_id (int): The id of the channel the sticky is in.

    Returns:
        int: The id if the sticky message itself.
    """
    sticky_query = """
    SELECT * FROM stickies
    WHERE channel_id = ?"""
    # This returns a list and we take the first object as there should only
    # ever be one due to unique constraints in the db.
    return (await _execute_read_query(sticky_query, (channel_id,)))[1]


async def get_sticky_list() -> list[tuple]:
    """Returns a list of all stickies in the database.

    Returns:
        list[tuple]: A list of tuples on the form (channel_id, message_id)
    """
    sticky_query = """
    SELECT * FROM stickies"""
    return await _execute_multiple_read_query(sticky_query)


async def create_sticky(channel_id: int, message_id: int) -> None:
    """Adds a new sticky to the database.

    Args:
        channel_id (int): The discord Channel id of the message.
        message_id (int): The id of the message itself.
    """
    sticky_add = """
    INSERT INTO
        stickies (channel_id, message_id)
    VALUES
        (?, ?);
    """
    await _execute_query(sticky_add, (channel_id, message_id,))


async def update_sticky(channel_id: int, message_id: int) -> None:
    """Updates the sticky in a certain channel to another message.

    Args:
        channel_id (int): The id of the discord channel the sticky is in.
        message_id (int): The id of the new sticky.
    """
    sticky_update = """
    UPDATE stickies
    SET
        message_id = ?
    WHERE
        channel_id = ?
    """
    await _execute_query(sticky_update, (message_id, channel_id,))


async def del_sticky(channel_id: int):
    """Remove a sticky from the db given a channel id

    Args:
        channel_id (int): The Id of the channel to remove the sticky from
    """
    sticky_del = "DELETE FROM stickies WHERE channel_id = ?"
    await _execute_query(sticky_del, (channel_id,))


async def get_player(guild_id: int, player_id: int) -> int:
    """Gets a player and the amount of quests they've run, and if they aren't
    in the db, initialize them with 0 quests made.

    Args:
        guild_id (int): The id of the discord guild to look for the player in.
        player_id (int): The id of the player to check.

    Returns:
        int: The amount of quests that player has run.
    """
    player_query = """
    SELECT quests_completed FROM players
    WHERE
        player_id = ?
    AND
        guild_id = ?;
    """

    query_return = await _execute_read_query(player_query, (player_id, guild_id,))
    if query_return is None:
        # The player doesn't exist in the db, let's add them.
        player_add = """
        INSERT INTO
            players (
                player_id,
                guild_id,
                quests_completed
            )
        VALUES
            (?, ?, ?);
        """
        await _execute_query(player_add, (player_id, guild_id, 0))
        return 0
    return query_return[0]


async def update_player(guild_id: int, player_id: int, quests_completed: int) -> None:
    """Sets an entry in the db to a specific value.

    Args:
        guild_id (int): The id of the discord guild to look for the player in.
        player_id (int): The player id of the row that should be updated.
        quests_completed (int): The amount of completed quests that should be entered.
    """
    player_update = """
        UPDATE players
        SET
            quests_completed = ?
        WHERE
            player_id = ?
        AND
            guild_id = ?
    """
    await _execute_query(player_update, (quests_completed, player_id, guild_id))


async def create_receipt(public_message_id: int, board_message_id: int) -> None:
    """Adds a receipt message to the database

    Args:
        public_message_id (int): The id of the discord channel the receipt was sent in.
        board_message_id (int): The id of the discord channel the receipts is copied to.
    """
    receipt_update = """
        INSERT INTO
            receipts (public_message_id, board_message_id)
        VALUES
            (?, ?);
    """
    await _execute_query(receipt_update, (public_message_id, board_message_id,))

async def get_receipt_list() -> list[tuple[int, int]]:
    """Returns a list of all receipts in the database
    Returns:
        list[tuple[int, int]]: a list of all receipt tuples in the database
    """
    receipts_get = """SELECT * FROM receipts"""
    return await _execute_multiple_read_query(receipts_get)

async def del_receipt_public(public_message_id: int) -> None:
    """Remove a receipt from the db given the public id

    Args:
        public_message_id (int): The Id of the message to remove
    """
    receipt_del = "DELETE FROM receipts WHERE public_message_id = ?"
    await _execute_query(receipt_del, (public_message_id,))


async def del_receipt_board(board_message_id: int) -> None:
    """Remove a receipt from the db given the board message id

    Args:
        board_message_id (int): The Id of the message to remove
    """
    receipt_del = "DELETE FROM receipts WHERE board_message_id = ?"
    await _execute_query(receipt_del, (board_message_id,))


if __name__ == "__main__":
    print("Creating tables if they don't exist")
    asyncio.run(_create_tables())
