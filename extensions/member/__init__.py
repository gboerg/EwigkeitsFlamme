from datetime import datetime
from email import message
from enum import member
from genericpath import exists
import logging as l
from math import perm
import os
from queue import Empty
from datetime import datetime
import threading
from time import sleep
import time
from types import NoneType
from typing import Optional

from easy_pil import Editor, Font
from interactions import ActionRow, Embed, AutocompleteContext, BaseContext, Button, ButtonStyle, ChannelType, Client, ComponentContext, Extension, File, Guild, Message, OptionType, PermissionOverwrite, Permissions, Reaction, ReactionUsers, SlashCommand, SlashContext, check, component_callback, listen, slash_command, slash_option, StringSelectMenu, StringSelectOption
import interactions
from interactions.api.events import MessageCreate, Component
import pytz
import asyncio

from database import conn, cursor

class Member(Extension):
    def __init__(self, bot):
        self.bot = bot
        self.claim_channel_lock = asyncio.Lock()
        bot.load_extension("extensions.member.tickets")
        l.info("[MEMBER] Initializing SQL database...")
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                guild_id INTEGER,
                user_id INT,
                messages INT,
                average_length FLOAT,
                shortest_message_length INT,
                longest_message_length INT,
                current_level INT,
                xp_needed INT,
                first_message_at TEXT,
                joined_at TEXT,
                wants_tracking TEXT, /* YES / NO / Partial*/
                partial_tracking_count INT, /* NUMBER FROM 1-?(10) - Depends on how much tracking the user wants or in bots case functionality */
                tracking_allow_scope TEXT, /* YES = Bot uses decision on all guilds where the user and bot is in | NO =Previous decision want tracking and partial tracking_count only on guild */ 
                PRIMARY KEY(guild_id, user_id)
            );
        """)
        conn.commit()
        l.info("[MEMBER] SQL table ready.")


    def setup(bot):
        Member(bot)
    

    def get_user(self, guild_id: int, user_id: int):
        """SQL: Fetch user by guild and ID"""
        try:
            cursor.execute("SELECT * FROM users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            return cursor.fetchone()
        except Exception as e:
            l.error(f"[MEMBER] Error fetching user: {e}")
            return None

    async def create_user(self, guild_id: int, user_id: int, messages: int, average_length: float, shortest_message_length: int, longest_message_length: int, current_level: int, xp_needed: int, first_message_at: str, joined_at: str):
        """SQL: [MEMBER | DB ] Create a user in table"""


        try:
            cursor.execute("""
                INSERT INTO users (
                    guild_id, user_id, messages, average_length,
                    shortest_message_length, longest_message_length,
                    current_level, xp_needed, first_message_at, joined_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guild_id, user_id, messages, average_length,
                shortest_message_length, longest_message_length,
                current_level, xp_needed, first_message_at, joined_at
            ))
            conn.commit()
            l.info(f"[TICKET | DB] Created user {user_id} in guild {guild_id}")

        except Exception as e:
            l.error(f"[TICKET | DB] Error creating user: {e}")

    async def update_user(self, guild_id: int, user_id: int, messages: Optional[int] = None, average_length: Optional[float] = None, shortest_message_length: Optional[int] = None, longest_message_length: Optional[int] = None, current_level: Optional[int] = None, xp_needed: Optional[int] = None):
        try:
            user = self.get_user(guild_id, user_id)
            if not user:
                l.warning(f"[MEMBER] Tried to update non-existing user {user_id}")
                return
            
            messages = messages if messages is not None else user["messages"]
            average_length = average_length if average_length is not None else user["average_length"]
            shortest_message_length = shortest_message_length if shortest_message_length is not None else user["shortest_message_length"]
            longest_message_length = longest_message_length if longest_message_length is not None else user["longest_message_length"]
            current_level = current_level if current_level is not None else user["current_level"]
            xp_needed = xp_needed if xp_needed is not None else user["xp_needed"]



            cursor.execute("""
                UPDATE users SET
                    messages = ?, average_length = ?,
                    shortest_message_length = ?, longest_message_length = ?,
                    current_level = ?, xp_needed = ?
                WHERE guild_id = ? AND user_id = ?
            """, (
                messages, average_length, shortest_message_length,
                longest_message_length, current_level, xp_needed,
                guild_id, user_id
            ))
            conn.commit()
            l.info(f"[MEMBER] Updated user {user_id} in guild {guild_id}")
        except Exception as e:
            l.error(f"[MEMBER] Error updating user: {e}")

    async def on_level_up(self, guild_id: int, author_id: int, author_name: str, level: int):
        level_up_channel = 1307233623564488767
        guild = await self.bot.fetch_guild(guild_id)
        channel = guild.get_channel(level_up_channel)

        if channel:
            await channel.send(f"🎉 **{author_name}** ({author_id}) hat einen Flammensplitter gefunden Und hat somit {level} erreicht! 🎉")

    @listen()
    async def on_message_create(self, event: MessageCreate):
        message = event.message

        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        author_id = message.author.id
        author_name = message.author.username
        msg_length = len(message.content)

        user = self.get_user(guild_id, author_id)

        if not user:
            await self.create_user(
                guild_id=guild_id,
                user_id=author_id,
                messages=1,
                average_length=msg_length,
                shortest_message_length=msg_length,
                longest_message_length=msg_length,
                current_level=0,
                xp_needed=10,
                first_message_at=message.created_at.isoformat(),
                joined_at=message.author.joined_at.isoformat()
            )
            return

        # Calculate new values
        messages = user["messages"] + 1
        new_avg = (user["average_length"] * user["messages"] + msg_length) / messages
        new_shortest = min(user["shortest_message_length"], msg_length)
        new_longest = max(user["longest_message_length"], msg_length)

        await self.update_user(
            guild_id=guild_id,
            user_id=author_id,
            messages=messages,
            average_length=new_avg,
            shortest_message_length=new_shortest,
            longest_message_length=new_longest
        )

        # Level up logic
        if messages == 3:
            await self.on_level_up(guild_id, author_id, author_name, "kleine Flamme")
            await self.update_user(guild_id=guild_id, user_id=author_id, current_level=1)

        elif messages == 96:
            await self.on_level_up(guild_id, author_id, author_name, 2)
        elif messages == 120 and new_avg >= 15:
            await self.on_level_up(guild_id, author_id, author_name, 3)
        elif messages == 170 and new_avg >= 30:
            await self.on_level_up(guild_id, author_id, author_name, 4)


    @slash_command(
        name = "user",
        description= "Command regarding the user"
    )
    async def user(self, ctx: SlashContext):
        pass

    # def check_permissions():
    #     async def predicate(ctx: BaseContext):
    #         return ctx.author.has_role("1362031370851061781")
    #     return check(predicate)
        

    @user.subcommand(
        sub_cmd_name="card",
        sub_cmd_description="Usercard options"
    )
    @slash_option(
        name="user",
        description="Select the user for the card (Default = YOU)",
        opt_type=OptionType.USER,
        required=False,
    )
    # def create_image(self, member, guild):

        
    async def create_card(
        self,
        ctx: SlashContext                                                                                           
    ):
        temp_path = None

        try:
            await ctx.defer(ephemeral=True)

            # member = ctx.author
            

            guild = ctx.guild
            if not guild:
                await ctx.send(f"Guild Only")
                return
            
            # user = self.get_user(guild.id, member.id)
            # if ctx.kwargs and user is None:
            #     await ctx.send("Userprofile doesn't exist yet")
            #     return
                

            
            
            
            if not ctx.kwargs:
                member = ctx.author

                user = self.get_user(guild.id, member.id)
                l.info(f"If Not ctx.kwargs {user} and {member}")
                l.info(f"user = {user!r} | type: {type(user)}")

                if user is None:
                    await ctx.send("Userprofile doesn't exist yet")
                    # temp_path = None
                    # raise 
                    return
                # if temp_path is not None and os.path.exists(temp_path):
                #     return
                else:  
                    l.info(f" DIE USER ID: {member.id}")
                    user_messages = user["messages"]
                    user_first_message_raw = user["first_message_at"]
                    user_join_raw = user["joined_at"]
                    level = user["current_level"]

                    user_first_message = datetime.fromisoformat(user_first_message_raw).strftime("%d.%m.%Y %H:%M")
                    user_join = datetime.fromisoformat(user_join_raw).strftime("%d.%m.%Y %H:%M")
                    


                    # Gernerieren der Usercard 
                    default_user_card = "assets/images/usercard.jpg"



                    background = Editor(default_user_card)
                    poppins = Font.poppins(size=100, variant="bold")
                    poppins_small = Font.poppins(size=50, variant="light")

                    background.text((300, 400), f"Die Karte der Flamme wurde gefertigt für:", color="white", font=poppins)
                    background.text((300, 550), f"{member}", color="white", font=poppins)
                    background.text((300, 800), f"Dein derzeitiges Level: {level}", color="white", font=poppins_small)
                    background.text((300, 1500), f"Du hast insgesammt {user_messages} Nachrichten gesendet", color="white", font=poppins_small)
                    background.text((300, 1600), f"Du bist dem Server {guild.name} am {user_join} beigreteten und hast deine erste Nachricht* am {user_first_message} gesendet", color="white", font=poppins_small)
                    
                    

                    temp_path = "new__usercard.jpg"    
                    background.image = background.image.convert("RGB")
                    background.image.save(temp_path, "JPEG")
                    file = File(temp_path)

                    await ctx.send(files=[file])
                    return
            
            
            
            # check if member has permissions to create a usercard for any user | Or Test Role in dev case

            member = ctx.kwargs["user"]
            if member:
                if ctx.author.has_role("1362031370851061781") or ctx.author == member:
                    user = self.get_user(guild.id, member.id)
                    l.info(f"user = {user!r} | type: {type(user)}")

                    if user is None:
                        await ctx.send("Userprofile doesn't exist yet")
                        return
                    

                    l.info(f" DIE USER ID: {member.id}")
                    user_messages = user["messages"]
                    user_first_message_raw = user["first_message_at"]
                    user_join_raw = user["joined_at"]
                    level = user["current_level"]

                    user_first_message = datetime.fromisoformat(user_first_message_raw).strftime("%d.%m.%Y %H:%M")
                    user_join = datetime.fromisoformat(user_join_raw).strftime("%d.%m.%Y %H:%M")
                    


                    # Gernerieren der Usercard 
                    default_user_card = "assets/images/usercard.jpg"



                    background = Editor(default_user_card)
                    poppins = Font.poppins(size=100, variant="bold")
                    poppins_small = Font.poppins(size=50, variant="light")

                    background.text((300, 400), f"Die Karte der Flamme wurde gefertigt für:", color="white", font=poppins)
                    background.text((300, 550), f"{member}", color="white", font=poppins)
                    background.text((300, 800), f"Dein derzeitiges Level: {level}", color="white", font=poppins_small)
                    background.text((300, 1500), f"Du hast insgesammt {user_messages} Nachrichten gesendet", color="white", font=poppins_small)
                    background.text((300, 1600), f"Du bist dem Server {guild.name} am {user_join} beigreteten und hast deine erste Nachricht* am {user_first_message} gesendet", color="white", font=poppins_small)
                    
                    

                    temp_path = "new__usercard.jpg"    
                    background.image = background.image.convert("RGB")
                    background.image.save(temp_path, "JPEG")
                    file = File(temp_path)

                    await ctx.send(files=[file])
                    return
                else:
                    await ctx.send(f"You do not have permission to create a user card for {member}")
                    return

            


        except Exception as e:
            await ctx.send(f"[USERCARD] Something went wrong {e}")

        finally:

            if  temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    
