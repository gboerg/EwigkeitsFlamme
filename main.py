from datetime import datetime, timedelta
import logging
import os
import sqlite3
import logging as l


from dotenv import load_dotenv
from interactions import Client, Guild, Intents, listen
import interactions
from database import cursor, conn

logging.basicConfig(
    format='[%(asctime)s | %(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)



# Initialize Bot with Required Intents
bot = Client(
    intents=Intents.ALL
)

# def delete_unused_events(self, event_id: str):
#     delete_query = """
#     DELETE FROM all_guilds
#     WHERE guild_id = ?;
#     """

#     try:
#         cursor.execute(delete_query, (event_id, ))
#         conn.commit()
#         l.info(f"Inactive Event {event_id} was removed because it was deleted in original guild")

#     except Exception as e: 
#         l.info(f"Error removing unused / inactive events because: {e}")


# async def try_fetch_each_guild_event(self, guild: interactions.Guild, guild_id: Client):

#     try:
#         for guild_ids in guild_id.guilds:
#             await guild.list_scheduled_events(guild_ids)

            
#             delete_unused_events("")
#     except Exception as e:
#         l.info(f"Unable to check events on guild given")
# def get_each_guild_from_all_guilds_table(self, guild_id):
#     select_query = """
#     SELECT * FROM all_guilds WHERE guild_id = ?
#     """
#     params = (guild_id, )
#     try:
#         cursor.execute(select_query, params)
#         return cursor.fetchall()
#     except Exception as e:
#         l.error(f"Couuldn't get all guilds {e}")

# def get_all_event_ids_from_events_table(self, event_id):
#     select_query = """
#     SELECT * FROM events WHERE id = ?;
#     """
#     params = (event_id, )
#     try:
#         cursor.execute(select_query, params)
#         return cursor.fetchall()
#     except Exception as e:
#         l.error(f"Couldn't get Events {e}")

    



# async def create_guild_list(guild_id: int, guild_name: str):
#     insert_query = """
#     INSERT INTO all_guilds (guild_id, guild_name)
#     VALUES (?, ?)
#     """
#     params = (guild_id, guild_name)
#     try: 
#         cursor.execute(insert_query, params)
#         conn.commit()
#         l.info(f"DATABASE ENTRY for: {guild_id} | {guild_name} successfully created")
#     except Exception as e:
#         l.error(f"ERROR: No Entry of all guild could be made: {e}")
    

# @listen("ready")  # CHANGED FROM "startup" TO "ready"
# async def on_ready_get_guilds():
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS all_guilds (
#             guild_id INTEGER PRIMARY KEY,
#             guild_name TEXT           
#         );
#     """)
    

#     # Access guilds through the bot instance
#     for guild in bot.guilds:
#         await create_guild_list(guild.id, guild.name)
#         l.info(f"{guild.id} and {guild.name} ")

@listen()
async def on_startup():
    # memes = datetime.now()  - timedelta(minutes=5)
    logging.info("Bot is ready")
    # l.info(f"Die Derzeitige Zeit minus 5min {memes}")

#Load Database
# try:
#     bot.load_extension(f"database.database")
#     logging.info("Loaded database")
# except Exception as e:
#     logging.error(f"Failed to load database: {e}")


# try:
#     bot.load_extension(f"extensions.bot.event")
#     logging.info("Event in Bot/Extensions was loaded succcessfully")
# except Exception as e:
#     logging.error(f"Failed to load Extension Bot/event {e}")


# Load Extensions
extensions = ["misc", "moderator", "twitch", "bot", "member"]
for extension in extensions:
    try:
        bot.load_extension(f"extensions.{extension}")
        logging.info(f"Loaded extension {extension}")
    except Exception as e:
        logging.error(f"Failed to load extension {extension}: {e}")

# Load environment variables and start the bot
load_dotenv()
bot.start(os.getenv("DISCORD_TOKEN"))
