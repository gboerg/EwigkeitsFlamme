import json
from shutil import ExecError
from types import NoneType
from typing import Optional
from interactions import Extension, Task, IntervalTrigger, listen
from interactions import Extension, listen, Message, Guild, SlashCommand, SlashContext
import aiofiles
from interactions.api.events import MessageCreate
from interactions.api.events.processors import GuildEvents
import aiofiles
import logging as l 
from database import conn, cursor


class Member(Extension):
    def __init__(self, bot):
        self.bot = bot
        l.info("[MEMBER | ] : BEFORE SQL DATABASE")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                guild_id INTEGER,
                user_id INT,
                messages INT,
                average_length INT,
                shortest_message_length INT,
                longest_message_length INT,
                first_message_at TEXT,
                joined_at TEXT,
                PRIMARY KEY(guild_id, user_id)
            );
        """)
        conn.commit()

        l.info("[MEMBER | ] : AFTER SQL DATABASE")

 
    def setup(bot):
        Member(bot)
        





    def get_user(self, guild_id, user_id):
        """Fragt die "USERS" SQL Datenbank nach dem User und der zugehörigen Gilde ab"""
        query = """
        SELECT * FROM users WHERE guild_id = ? AND user_id = ?; 
        """

        params = (
            guild_id, user_id
        )

        try:
            cursor.execute(query, params)
            # return cursor.fetchall()
            return cursor.fetchone()
            
        except Exception as e:
            l.error(f"failed to get user {e}")

        

    async def create_user(self, guild_id: int, user_id: int, messages: int, 
                        average_length: float, shortest_message_length: int, 
                        longest_message_length: int, first_message_at: str, 
                        joined_at: str):
        """Erstelle einen User in der SQL Datenbank"""
        insert_query = """
        INSERT INTO users (
            guild_id, 
            user_id, 
            messages, 
            average_length, 
            shortest_message_length, 
            longest_message_length, 
            first_message_at, 
            joined_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            guild_id, 
            user_id, 
            messages, 
            average_length, 
            shortest_message_length, 
            longest_message_length, 
            first_message_at, 
            joined_at
        )

        try:
            cursor.execute(insert_query, params)
            conn.commit()
            l.info(f"[MEMBER]: {user_id} was successfully saved")
        except Exception as e:
            l.error(f"[MEMBER]: Unable to create user: {e}")

    async def update_user(self, guild_id: int, user_id: int, messages: int, average_length: float, shortest_message_length: int, longest_message_length: int):
        """Aktualisiert die Benutzerdaten"""
        update_query = """
        UPDATE users
        SET 
            messages = ?,
            average_length = ?,
            shortest_message_length = ?,
            longest_message_length = ?
        WHERE guild_id = ? AND user_id = ?
        """

        params = (
            messages,
            average_length,
            shortest_message_length,
            longest_message_length,
            guild_id,
            user_id
        )

        try:
            cursor.execute(update_query, params)
            conn.commit()
            l.info(f"[MEMBER | DB] Update for Userprofile successful")
        except Exception as e:
            l.error(f"[MEMBER | DB] Couldn't update Member Database profile: {e}")


    # async def on_archivement(self, guild_id: str, author_id: str, author_name: str, level:int):
    #     l.info("Archivement Tracked successfully")



    async def on_level_up(self, guild_id: str, author_id: str, author_name: str, level: int):
        level_up_channel = 1307233623564488767
        guild = await self.bot.fetch_guild(guild_id)
        channel = guild.get_channel(level_up_channel)
        # author_id 

        if channel and level == 1:
            await channel.send(f"🎉 **{author_name}** {author_id} ist der Flamme näher gekommen 🎉 Und hat eine Flamme dazugewonnen")

        elif channel and level == 2:
            await channel.send(f"🎉 **{author_name}** {author_id} ist der Flamme näher gekommen 🎉 Und hat {level} Flammen dazugewonnen")

        else:
            await channel.send(f"🎉 **{author_name}** {author_id} ist der Flamme näher gekommen 🎉 Und hat {level} Flammen dazugewonnen")


    @listen()
    async def on_message_create(self, event: MessageCreate):
        message = event.message

        guild = message.guild
        guild_id = guild.id


        author_id = message.author.id
        author_name = message.author.username

        average_message_length = len(message.content)



        if message.author.bot:
            return
        
        if not guild:
            return
        
        
        user = self.get_user(guild_id, author_id)
        
        # brauche ich hier ein for users in user? damit es genau klappt? | Profil wird auf Nachricht für die UserID angelegt aber: die logik das geschaut wird ob der user bereits existiert funktioniert nicht 
        if not user:
            # joined_at = message.author.joined_at.isoformat()
            # first_message_at = message.created_at.isoformat()
            await self.create_user(guild_id, author_id, 1, average_message_length, 22, 22, message.created_at.isoformat(), message.author.joined_at.isoformat())
            # await self.create_user(guild_id, author_id, 1, average_message_length, 1, message.created_at.isoformat(), 2, message.author.joined_at.isoformat())
            l.info("Nutzer Profil pro Gilde erstellt")

            
        if user:
            current_avg = user["average_length"]
            current_messages = user["messages"]
            messages = current_messages + 1
            new_avg = (current_avg * current_messages + len(message.content)) / messages
            # for user in users: Das vielleicht
            # average_message_length = 23
            await self.update_user(guild_id, author_id, messages, new_avg, None, None)
            l.info("Nachrichten Anzahl um 1 erhöht")

            if current_messages == 1:
                l.info(f"Gesammtnachrichten von {current_messages} erreicht Nutzer: {author_name}")
                await self.on_level_up(guild_id, author_id, author_name, 1)

            elif current_messages == 96:
                l.info("LevelUP (Level2)")
                await self.on_level_up(guild_id, author_id, author_name, 2)

            elif current_messages == 120 and average_message_length >= 15:
                l.info("next level reached")
                await self.on_level_up(guild_id, author_id, author_name, 3)

            elif current_messages == 170 and average_message_length >= 30:
                l.info("Even next")




    # @listen()
    # async def on_message_create(self, event: MessageCreate):
    #     message = event.message
        
    #     if message.author.bot:
    #         return
        
    #     # Zuerst prüfen, ob die Nachricht von einem Server kommt
    #     if not message.guild:
    #         return  # Keine Guild = DM-Nachricht, überspringen
        
    #     # Erst NACH der Guild-Prüfung die IDs holen
    #     guild = message.guild
    #     guild_id = guild.id
    #     author_id = message.author.id
        
    #     # Existenz-Check korrekt durchführen
    #     existing_user = self.get_user(guild_id, author_id)
        
    #     if not existing_user:
    #         # Neuer User
    #         await self.create_user(
    #             guild_id=guild_id,
    #             user_id=author_id,
    #             messages=1,
    #             average_length=len(message.content),
    #             joined_at=message.author.joined_at.isoformat() if message.author.joined_at else None,
    #             first_message_at=message.created_at.isoformat()
    #         )
    #     else:
    #         # Existierender User
    #         # current_messages = existing_user[0]["messages"]
    #         current_messages = existing_user["messages"]
    #         new_messages = current_messages + 1
            
    #         # Durchschnitt neu berechnen
    #         current_avg = existing_user["average_length"] #or 0
    #         new_avg = (current_avg * current_messages + len(message.content)) / new_messages
            
    #         await self.update_user(
    #             guild_id=guild_id,
    #             user_id=author_id,
    #             messages=new_messages,
    #             average_length=new_avg
    #         )










            

                

        

    # @listen()
    # async def on_message_create(self, event: MessageCreate):
    #     message = event.message
    #     if message.author.bot:
    #         return
        
    #     guild = message.guild
    #     if not guild:
    #         return
        
    #     guild_id = guild.id
    #     author = message.author
    #     author_id = author.id

    #     exisiting = self.get_user(guild_id, author_id)
    #     if not exisiting:
    #         # 
    #         await self.create_user(guild_id, author_id, 1)
    #         l.info(f"[MEMBER | LEVELING] New user {author_id} created in {guild_id}")
    #     else:
    #         current_messages = exisiting[0][2]
    #         new_messages = current_messages + 1

    #         await self.update_user(guild_id, author_id, new_messages)
    #         l.info(f"[MEMBER] Updated user {author_id} in guild {guild_id} to {new_messages} messages")











        # if guild_id not in self.get_user:
        #     # self.users[guild_id] = {}
        #     await self.create_user(guild_id, author_id)


        # if author_id not in self.users[guild_id]:
        #     self.users[guild_id][author_id] = {
        #         "name": author_name,
        #         "messages": 0
        #     }

        # if author_id not in self.get_user(guild_id, author_id):
        #     await self.create_user(guild_id, author_id, 0, 3, 30, 30)
        #     l.info(f"User Profile of {author_id} in {guild_id} saved and stored")

        # if author_id in self.get_user(guild_id, author_id):
        #     await self.update_user(guild_id, author_id, 1, 2, "hi_2", "hi_3" )

        # if self.users[guild_id][author_id]["messages"] == 100:
        #     await self.on_level_up(guild_id, author_id, author_name)


        # self.update_user(guild_id, author_id, messages =+ 1)

        # self.users[guild_id][author_id]["messages"] += 1

        # print(f"Nachrichtenzahl für {author_name} ({author_id}) in Gilde {guild_id}: {self.users[guild_id][author_id]['messages']}")







    # # def create_users(self, guild_id, member_id, member_name):

    # def load_users(self):
    #     try:
    #         with open(self.users_file, "r") as file:
    #             return json.load(file)  # Load the JSON data
    #     except FileNotFoundError:
    #         return {}  # Start with an empty dictionary if the file does not exist
    #     except json.JSONDecodeError:
    #         print("❌ Fehler beim Laden der JSON-Datei. Starte mit leerer Liste.")
    #         return {}

    # async def save_users(self):
    #     try:
    #         async with aiofiles.open(self.users_file, "w", encoding="utf-8") as file:
    #             await file.write(json.dumps(self.users, indent=4, ensure_ascii=False))
    #         print(f"✅ Events erfolgreich in {self.users_file} gespeichert.")
    #     except Exception as e:
    #         print(f"❌ Fehler beim Speichern der Events: {e}")

    # @Task.create(IntervalTrigger(minutes=60))
    # async def get_all_guild_members(self):
    #     for guild in self.bot.guilds:
    #         member_names = [member.username for member in guild.humans]
    #         user_list = "\n".join(member_names)  # Benutzer pro Zeile

    #         print(f"Guild: {guild.name} (ID: {guild.id}), Membercount: {len(member_names)}")
    #         print(f"Members:\n{user_list}")

    #         # Speichere die Daten in der JSON-Datei
    #         self.users[guild.id] = {
    #             "guild_name": guild.name,
    #             "member_count": len(member_names),
    #             "members": member_names,  # Liste für die JSON-Datei
    #         }

    #     await self.save_users()

    # @listen()
    # async def on_startup(self):
    #     print("Starting up and initializing member fetch task...")
    #     self.get_all_guild_members.start()
