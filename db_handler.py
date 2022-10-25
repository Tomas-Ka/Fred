import sqlite3
from sqlite3 import Connection, Error
from typing import List, Tuple
from helpers import QuestInfo


def _create_connection(path) -> Connection:
    """Creates a new connection to the database file and returns an object
    we can use to get data from the db.

    Args:
        path (str or bytepath): Path to the databasefile

    Returns:
        Connection: Object that can be used to communicate with the database
    """
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


def _create_tables() -> None:
    """Initialization function to create the database if it doesn't exist yet.
    """
    create_quests_table = """
    CREATE TABLE IF NOT EXISTS quests (
        "id" INTEGER PRIMARY KEY NOT NULL,
        "quest_title" TEXT UNIQUE NOT NULL,
        "contractor" TEXT NOT NULL,
        "description" TEXT NOT NULL,
        "reward" TEXT NOT NULL,
        "embed_colour" TEXT NOT NULL,
        "thread_id" INTEGER NOT NULL,
        "quest_role_id" INTEGER NOT NULL,
        "pin_message_id" INTEGER NOT NULL,
        "players" BLOB
    );
    """
    _execute_query(connection, create_quests_table, ())

    create_stickies_table = """
    CREATE TABLE IF NOT EXISTS stickies (
        "channel_id" INTEGER UNIQUE,
        "message_id" INTEGER UNIQUE
    );
    """
    _execute_query(connection, create_stickies_table, ())

    create_players_table = """
    CREATE TABLE IF NOT EXISTS players (
        "player_id" INTEGER UNIQUE,
        "quests_completed" INTEGER
    );
    """

    _execute_query(connection, create_players_table, ())


def _execute_query(connection: Connection, query: str, vars: Tuple) -> None:
    """Execute the given query with the given connection (database).

    Args:
        connection (Connection): An sqlite3 database connecttion.
        query (str): The query string.
        vars (Tuple): The vars to replace the spots in the queary string.
    """
    cursor = connection.cursor()
    try:
        cursor.execute(query, vars)
        connection.commit()
        # print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")


def _execute_multiple_read_query(
        connection: Connection, query: List) -> List[Tuple]:
    """Same as execute_query except it returns values,
    and is used for reading from the db.

    Args:
        connection (Connection): A connection to the database.
        query (str): The string to query the database with.

    Returns:
        List: a list containing all the data found from the query.
    """
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")


def _execute_read_query(connection: Connection,
                        query: List, vars: Tuple) -> Tuple:
    """Same as execute_read_query except it only returns a single value

    Args:
        connection (Connection): A connection to the database.
        query (str): The string to query the database with.

    Returns:
        Tuple: A Touple containing the data at the found row.
    """
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query, vars)
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")


def get_quest_by_title(quest_title) -> QuestInfo:
    """Returns the first found quest given the quest title.

    Args:
        quest_title (string): The title of the quest to search for.

    Returns:
        QuestInfo: An object containing the data from the db.
    """
    quest_query = """
    SELECT * FROM quests
    WHERE quest_title = ?"""
    # This returns a list and we take the first object as there should only
    # ever be one due to unique constraints in the db
    query_return = _execute_read_query(connection, quest_query, (quest_title))

    # The first value returned is the id of the quest, which we don't want to
    # parse
    if query_return:
        quest = QuestInfo(*query_return[1:])
    return quest


def get_quest(quest_id: int) -> QuestInfo:
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
    # ever be one due to unique constraints in the db
    query_return = _execute_read_query(connection, quest_query, (quest_id,))

    # The first value returned is the id of the quest, which we don't want to
    # parse
    quest = None
    if query_return:
        quest = QuestInfo(*query_return[1:])
    return quest


def get_quest_by_title(quest_title: str) -> Tuple[int, QuestInfo]:
    """Returns a tuple containing the quest id
    and a questInfo object, given a quest title.

    Args:
        quest_id (int): The quest name to get from the database.

    Returns:
        Tuple[int, QuestInfo]: An object containing the data from the db.
    """
    quest_query = """
    SELECT * FROM quests
    WHERE quest_title = ?;"""

    # This returns a list and we take the first object as there should only
    # ever be one due to unique constraints in the db
    query_return = _execute_read_query(connection, quest_query, (quest_title,))

    # The first value returned is the id of the quest, which we don't want to
    # parse
    quest = []
    if query_return:
        quest = QuestInfo(*query_return[1:])
    return (query_return[0], quest)


def get_quest_list() -> List[QuestInfo]:
    """Returns a list of all quests in the database

    Returns:
        List[QuestInfo]: The list of objects
    """

    quest_querty = """
    SELECT * FROM quests;
    """

    query_return = _execute_multiple_read_query(connection, quest_querty)
    quests = []
    if query_return:
        for quest in query_return:
            quests.append(QuestInfo(*quest[1:]))
    return quests


def create_quest(id: int, quest_info: QuestInfo) -> None:
    """Adds a quest to the db.

    Args:
        id (int): The message id the quest is linked to in both the database, and discord.
        quest_info (QuestInfo): The information to store in the database.
    """
    quest_add = """
    INSERT INTO
        quests (
        id, quest_title, contractor,
        description, reward,
        embed_colour, thread_id,
        quest_role_id, pin_message_id
        )
    VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    vars = (
        id,
        quest_info.quest_title,
        quest_info.contractor,
        quest_info.description,
        quest_info.reward,
        quest_info.embed_colour,
        quest_info.thread_id,
        quest_info.quest_role_id,
        quest_info.pin_message_id,)

    _execute_query(connection, quest_add, vars)


def update_quest(id: int, quest_info: QuestInfo) -> None:
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
        id,)

    _execute_query(connection, quest_update, vars)


def del_quest_by_title(quest_title: str) -> None:
    """Remove a quest from the db given a quest title.

    Args:
        quest_title (str): The title of the quest to remove.
    """
    quest_del = f"DELETE FROM quests WHERE quest_title = ?"
    _execute_query(connection, quest_del, (quest_title,))


def del_quest(id: int) -> None:
    """Remove a quest from the db given an id.

    Args:
        id (int): The id of the quest to remove.
    """
    quest_del = f"DELETE FROM quests WHERE id = ?"
    _execute_query(connection, quest_del, (id,))


def get_sticky(channel_id: int) -> int:
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
    # ever be one due to unique constraints in the db
    return _execute_read_query(connection, sticky_query, (channel_id,))[1]


def get_sticky_list() -> List[int]:
    """Returns a list of all stickies in the database.

    Returns:
        List[int]: A list of ids for the channels the stickies are in.
    """
    sticky_query = """
    SELECT * FROM stickies"""
    return _execute_multiple_read_query(connection, sticky_query)


def create_sticky(channel_id: int, message_id: int) -> None:
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
    _execute_query(connection, sticky_add, (channel_id, message_id,))


def update_sticky(channel_id: int, message_id: int) -> None:
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
    _execute_query(connection, sticky_update, (message_id, channel_id,))


def del_sticky(channel_id: int):
    """Remove a sticky from the db given a channel id

    Args:
        channel_id (int): The Id of the channel to remove the sticky from
    """
    sticky_del = f"DELETE FROM stickies WHERE channel_id = ?"
    _execute_query(connection, sticky_del, (channel_id,))


def get_player(player_id: int) -> int:
    """Gets a player and the amount of quests they've run, and if they aren't
    in the db, initialize them with 0 quests made.

    Args:
        player_id (int): The id of the player to check.

    Returns:
        int: The amount of quests that player has run.
    """
    player_query = """
    SELECT quests_completed FROM players
    WHERE player_id = ?;"""

    query_return = _execute_read_query(connection, player_query, (player_id,))
    if query_return is None:
        # The player doesn't exist in the db, let's add them
        player_add = """
        INSERT INTO
            players (
                player_id,
                quests_completed
            )
        VALUES
            (?, ?);
        """
        _execute_query(connection, player_add, (player_id, 0))
        return 0
    return query_return[0]


def update_player(player_id: int, quests_completed: int) -> None:
    """Sets an entry in the db to a specific value.

    Args:
        player_id (int): The player id of the row that should be updated.
        quests_completed (int): The amount of completed quests that should be entered.
    """
    player_update = """
        UPDATE players
        SET
            quests_completed = ?
        WHERE
            player_id = ?
    """
    _execute_query(connection, player_update, (quests_completed, player_id))


global connection
connection = _create_connection("db.sqlite")


if __name__ == "__main__":
    _create_tables()
