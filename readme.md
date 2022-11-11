# Nat 1 Fred, the discord bot
### Purpose:
This is a discord bot written in Python that runs the quest system, and acts as a dice bot in my dnd discord server. He also has features to handle a preconfigured sticky message, as well as the functionality to handle an archive role on reactions.

### Code, and system:
A lot of these systems are incredibly hacked together, but at least it works, and it's moderately commented to boot. Fred runs with the discord.py library, and the main.py file is naturally the entrypoint. For first time setup, run db_handler.py to set up the database. All the functions work on the discord.py cog system, and files in the cogs folders are read and loaded in the main program. Finally we have the sqlite database, which can be accessed using the db_handler class, which itself uses the sqlite3 library.

### Usage:
This codebase uses the license, so feel free to use it yourself (if you go through the pain to read all this code you really deserve it). Any and all comments and updates/upgrades are welcome! I'm working on this all alone, so development might be incredibly sporadic.
