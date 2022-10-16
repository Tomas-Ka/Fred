import sqlite3
from sqlite3 import Connection, Error
from typing import List
from cogs.quest_handler import QuestInfo


def create_connection(path) -> Connection:
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


def execute_query(connection: Connection, query: str) -> None:
    """Execute the given query with the given connection (database).

    Args:
        connection (Connection): An sqlite3 database connecttion.
        query (str): The query string.
    """
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Same as execute_query except it can return values, so it's to be used
# when reading from the db


def execute_read_query(connection: Connection, query: List):
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


def get_quest_by_title(quest_title) -> QuestInfo:
    """Returns the first found quest given the quest title.

    Args:
        quest_title (string): The title of the quest to search for.

    Returns:
        QuestInfo: An object containing the data from the db.
    """
    quest_query = f"""
  SELECT * FROM quests
  WHERE quest_title = '{quest_title}'"""
    # This returns a list and we take the first object as there should only
    # ever be one due to unique constraints in the db
    query_return = execute_read_query(connection, quest_query)[0]

    # The first value returned is the id of the quest, which we don't want to
    # parse
    quest = QuestInfo(*query_return[1:])
    return quest


def get_quest(quest_id: int) -> QuestInfo:
    """Returns a quest given a quest id.

    Args:
        quest_id (int): The quest id to get from the database.

    Returns:
        QuestInfo: An object containing the data from the db.
    """
    quest_query = f"""
  SELECT * FROM quests
  WHERE id = '{quest_id}'"""

    # This returns a list and we take the first object as there should only
    # ever be one due to unique constraints in the db
    query_return = execute_read_query(connection, quest_query)[0]

    # The first value returned is the id of the quest, which we don't want to
    # parse
    quest = QuestInfo(*query_return[1:])
    return quest


def create_tables() -> None:
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
    execute_query(connection, create_quests_table)

    create_stickies_table = """
  CREATE TABLE IF NOT EXISTS stickies (
    "channel_id" INTEGER UNIQUE,
    "message_id" INTEGER UNIQUE
  );
  """
    execute_query(connection, create_stickies_table)


def create_quest(id: int, quest_info: QuestInfo) -> None:
    """Adds a quest to the db.

    Args:
        id (int): The message id the quest is linked to in both the database, and discord.
        quest_info (QuestInfo): The information to store in the database.
    """
    quest_add = f"""
  INSERT INTO
    quests (
      id, quest_title, contractor,
      description, reward,
      embed_colour, thread_id,
      quest_role_id, pin_message_id
    )
  VALUES
    ({id}, "{quest_info.quest_title}", "{quest_info.contractor}",
    "{quest_info.description}", "{quest_info.reward}",
    "{quest_info.embed_colour}", {quest_info.thread_id},
    {quest_info.quest_role_id}, {quest_info.pin_message_id});
  """
    execute_query(connection, quest_add)


def remove_quest_by_title(quest_title: str) -> None:
    """Remove a quest from the db given a quest title.

    Args:
        quest_title (str): The title of the quest to remove.
    """
    quest_del = f"DELETE FROM quests WHERE quest_title = '{quest_title}'"
    execute_query(connection, quest_del)


def remove_quest(id: int) -> None:
    """Remove a quest from the db given an id.

    Args:
        id (int): The id of the quest to remove.
    """
    quest_del = f"DELETE FROM quests WHERE id = '{id}'"
    execute_query(connection, quest_del)


def create_sticky(channel_id: int, message_id: int) -> None:
    """Adds a new sticky to the database.

    Args:
        channel_id (int): The discord Channel id of the message.
        message_id (int): The id of the message itself.
    """
    sticky_add = f"""
  INSERT INTO
    stickies (channel_id, message_id)
  VALUES
    ('{channel_id}', '{message_id}');
  """
    execute_query(connection, sticky_add)


def del_sticky(channel_id: int):
    """Remove a sticky from the db given a channel id

    Args:
        channel_id (int): The Id of the channel to remove the sticky from
    """
    sticky_del = f"DELETE FROM stickies WHERE id = '{channel_id}'"
    execute_query(connection, sticky_del)


global connection
connection = create_connection("db.sqlite")


if __name__ == "__main__":
    create_tables()

    # This is all setup for migrating from the old .dat system, and will be removed once the migration is over
    # TODO
    if (input("connect to discord and send pin messages?") == "y"):
        import main
        from main import bot
        from dotenv import load_dotenv
        from os import environ
        import pickle
        import asyncio
        from cogs.quest_handler import QuestInfo
        import db_handler as db

        load_dotenv()
        token = environ["TOKEN"]

        @bot.listen()
        async def on_ready():
            with open(f'QUESTS.dat', 'rb') as quests:
                QUESTS = pickle.load(quests)
            await bot.wait_until_ready()
            for id in QUESTS:
                obj: QuestInfo = QUESTS[id]
                print(obj.quest_title)
                print(obj.thread_id)
                if obj.quest_title == "aa" or obj.thread_id == 1019875727824396290:
                    print("skipping")
                    continue
                print("------------------------")
                print(bot.get_channel(1002356135816343632))
                print(obj.thread_id)
                print(
                    bot.get_channel(1002356135816343632).get_thread(
                        obj.thread_id))
                message = await bot.get_channel(1002356135816343632).get_thread(obj.thread_id).send(content="This is a temp pin that should be changed soon")
                await bot.get_channel(1002356135816343632).get_thread(obj.thread_id).get_partial_message(message.id).pin()
                obj.pin_message_id = message.id
                db.add_quest(obj)
        bot.run(token)
