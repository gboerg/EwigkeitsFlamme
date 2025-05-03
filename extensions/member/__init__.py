from datetime import datetime
from email import message
from enum import member
from genericpath import exists
import logging as l
from math import perm
import os
from queue import Empty
import threading
from time import sleep
import time
from types import NoneType
from typing import Optional

from easy_pil import Editor, Font
from interactions import Embed, AutocompleteContext, BaseContext, Button, ButtonStyle, ChannelType, Client, ComponentContext, Extension, File, Guild, Message, OptionType, PermissionOverwrite, Permissions, Reaction, ReactionUsers, SlashCommand, SlashContext, check, component_callback, listen, slash_command, slash_option, StringSelectMenu, StringSelectOption
import interactions
from interactions.api.events import MessageCreate, Component
import pytz

from database import conn, cursor

class Member(Extension):
    def __init__(self, bot):
        self.bot = bot
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
                PRIMARY KEY(guild_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS tickets (
                guild_id INTEGER,
                user_id INT,
                total_ticket_count INT,
                ticket_channel_id INT,
                claim_channel_id INT,
                closed_channel_id INT,
                stuff_member_id INT
            );
        """)
        conn.commit()
        l.info("[MEMBER] SQL table ready.")


    def setup(bot):
        Member(bot)
    
    async def create_ticket(self, guild_id: int, user_id: int, total_ticket_count:int, ticket_channel_id: int, claim_channel_id: Optional[int] = None, closed_channel_id: Optional[int] = None, stuff_member_id: Optional[int] = None):
        """ [SQL] [TICKETS] : Create or update ticket in DB """
        insert_query = """
            INSERT INTO tickets (
                guild_id, user_id, total_ticket_count, ticket_channel_id, claim_channel_id, closed_channel_id, stuff_member_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            guild_id,
            user_id,
            total_ticket_count,
            ticket_channel_id,
            claim_channel_id,
            closed_channel_id,
            stuff_member_id
        )

        try:
            cursor.execute(insert_query, params)
            conn.commit()
            l.info(f"[TICKET | DB] Ticket created or updated for user {user_id}. Total tickets: {total_ticket_count}")
        except Exception as e:
            l.error(f"[TICKET | DB] Error during ticket creation: {e}")

    async def update_ticket(self, guild_id: int, user_id: int, total_ticket_count: Optional [int] = None, ticket_channel_id: Optional[int] = None, claim_channel_id: Optional[int] = None, closed_channel_id: Optional[int] = None, stuff_member_id: Optional[int] = None):
        try:

            tickets = await self.get_ticket_user(guild_id, user_id) 
            if not tickets: 
                l.warning(f"[TICKETS | DB] Tried to update non existing ticket {user_id}")
                return
            
            total_ticket_count = total_ticket_count if total_ticket_count is not None else tickets["total_ticket_count"]
            ticket_channel_id = ticket_channel_id if ticket_channel_id is not None else tickets["ticket_channel_id"]
            claim_channel_id = claim_channel_id if claim_channel_id is not None else tickets["claim_channel_id"]
            closed_channel_id = closed_channel_id if closed_channel_id is not None else tickets["closed_channel_id"]

            """
            [TICKET | DB] Updatet das Ticket mit den mitgegebenen Parametern - wenn kein Parameter mitgegeben wird  
            """
            
            update_query = """
                UPDATE tickets 
                SET total_ticket_count = ?,
                    ticket_channel_id = ?,
                    claim_channel_id = ?,
                    closed_channel_id = ?,
                    stuff_member_id = ?
                WHERE guild_id = ? AND user_id = ?;
                """
            params = (total_ticket_count, ticket_channel_id, claim_channel_id, closed_channel_id, stuff_member_id, guild_id, user_id)
            cursor.execute(update_query, params)
            conn.commit()

        except Exception as e:
            l.error(f"[TICKETS | DB] Error during ticket update {e}")


    async def get_ticket_user(self, guild_id: int, user_id: int):
        """SQL: Fetch user by guild and ID"""
        try:
            cursor.execute("SELECT * FROM tickets WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            return cursor.fetchone()

        except Exception as e:
            l.error(f"[TICKET | DB] Error fetching user: {e}")
            return None
        

    async def get_ticket_by_guild(self, guild_id: int):
        """Get all tickets in a guild where the comment was invoked in"""
        try:
            cursor.execute("SELECT * FROM tickets WHERE guild_id = ?", (guild_id, ))
            return cursor.fetchone()
            row = cursor.fetchone()
            # if row:
            #     return {
            #         "guild_id": row[0],
            #         "user_id": row[1],
            #         "total_ticket_count": row[2],
            #         "ticket_channel_id": row[3],
            #         "claim_channel_id": row[4],
            #         "stuff_member_id": row[5]
            #     }
            # return None
        except Exception as e:
            l.error(f"[TICKET | DB] Error fetching ticket by guild: {e}")
            return None




    async def get_ticket_by_any_channel(self, guild_id: int, channel_id: int):
        try:
            l.info(f"[DEBUG] Suche Ticket mit guild_id={guild_id}, channel_id={channel_id}")
            cursor.execute("""
                SELECT * FROM tickets
                WHERE guild_id = ? AND (ticket_channel_id = ? OR claim_channel_id = ?)
            """, (guild_id, channel_id, channel_id))
            row = cursor.fetchone()
            if row:
                l.info(f"[DEBUG] Ticket gefunden: {row}")
                return {
                    "guild_id": row[0],
                    "user_id": row[1],
                    "total_ticket_count": row[2],
                    "ticket_channel_id": row[3],
                    "claim_channel_id": row[4],
                    "closed_channel_id": row[5],
                    "stuff_member_id": row[6]
                }
            l.warning("[DEBUG] Kein Ticket gefunden mit diesem Channel.")
            return None
        except Exception as e:
            l.error(f"[TICKET | DB] Error fetching ticket by any channel: {e}")
            return None


    # =====================================

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
    

    @slash_command(
        name="ticket",
        description="central ticket comment - Here you can create or close a ticket",
        # group_name="create",
        # group_description="create",
        
    )
    async def ticket(self, ctx: SlashContext):
        pass


    def create_ticket_buttons(self):
        ticket_close = Button(
            disabled=False,
            custom_id="ticket_close",
            style=ButtonStyle.BLURPLE,
            label="Close Ticket",
        )

        ticket_close_confirm = Button(
            custom_id="ticket_close_confirm",
            style=ButtonStyle.DANGER,
            label="Ticket Schließen"
        )

        ticket_close_cancel = Button(
            custom_id="ticket_close_cancel",
            style=ButtonStyle.GREEN,
            label="Ticket Nicht Schließen"
        )

        ticket_fb = StringSelectMenu(
            "Ja", "Nein", "Andere",
            placeholder="Wurde dein Anliegen gelöst",
            min_values=1,
            max_values=1,
            custom_id="ticket_fb",
        )

        ticket_claim = Button(
            custom_id="claim_ticket",
            style=ButtonStyle.GREEN,
            label="Claim Ticket",
        )

        ticket_release = Button(
            custom_id="ticket_release",
            style=ButtonStyle.GREY,
            label="Let Someone else takeover",
        )

        ticket_reopen = Button(
            custom_id="ticket_reopen",
            style=ButtonStyle.BLUE,
            label="Reopen Ticket",
        )

        return {
            "ticket_close": ticket_close,
            "ticket_close_confirm": ticket_close_confirm,
            "ticket_close_cancel": ticket_close_cancel,
            "ticket_claim": ticket_claim,
            "ticket_fb" : ticket_fb,
            "ticket_release": ticket_release,
            "ticket_reopen": ticket_reopen

        }

    async def ensure_ticket_categories(self, guild):
        categories = {}
        existing = {c.name: c for c in guild.channels if c.type == ChannelType.GUILD_CATEGORY}

        required = {
            "tickets": {
                "overwrites": [
                    PermissionOverwrite(
                        id=guild.id,
                        type=0,  # 0 = Role (Guild)
                        deny=Permissions.VIEW_CHANNEL
                    )
                ]
            },
            "claim-tickets": {
                "overwrites": [
                    PermissionOverwrite(
                        id=guild.id,
                        type=0,
                        deny=Permissions.VIEW_CHANNEL
                    )
                ]
            },
            "closed-tickets": {
                "overwrites": [
                    PermissionOverwrite(
                        id=guild.id,
                        type=0,
                        deny=Permissions.VIEW_CHANNEL
                    )
                ]
            },
        }

        if "tickets":
            l.info(f"Ticket")

        for name, opts in required.items():
            if name in existing:
                categories[name] = existing[name]
            else:
                cat = await guild.create_category(name=name)
                await cat.edit(permission_overwrites=opts["overwrites"])
                categories[name] = cat

        return categories

    @ticket.subcommand(
        sub_cmd_name="create",
        sub_cmd_description="create a ticket",
    )
    # @slash_option(
    #     name="issue",
    #     description="the issue you having - Or reason of the ticket",
    #     opt_type=OptionType.STRING,
    #     required=True
    # )
    async def createTicket(self, ctx: SlashContext):
        await ctx.defer(ephemeral=True)
        try:
            guild = ctx.guild
            if not guild:
                await ctx.send("Dieser Befehl funktioniert nur in einem Server.")
                return

            categories = await self.ensure_ticket_categories(guild)
            ticket_cat = categories["tickets"]
            c_ticket_cat = categories["claim-tickets"]
            closed_ticket_cat = categories["closed-tickets"]

            member = ctx.member.user.username
            safe_name = member.lower().replace(" ", "-")
            ticket_name = f"{safe_name}-ticket"
            c_ticket_name = f"claim-{safe_name}-ticket"




            # Existierendes Ticket prüfen
            for channel in guild.channels:
                if channel.name == ticket_name:
                    await ctx.send(f"Du hast bereits ein Ticket: <#{channel.id}>")
                    return

            overwrite = PermissionOverwrite.for_target(ctx.author)
            overwrite.add_allows(Permissions.VIEW_CHANNEL)

            ticket = await guild.create_text_channel(name=ticket_name, category=ticket_cat)
            await ticket.edit_permission(overwrite=overwrite)
            claim = await guild.create_text_channel(name=c_ticket_name, category=c_ticket_cat)

            await ctx.send(f"Dein Ticket wurde erstellt: <#{ticket.id}>")

            buttons = self.create_ticket_buttons()
            ticket_close = buttons["ticket_close"]
            ticket_claim = buttons["ticket_claim"]
            ticket_release = buttons["ticket_release"]
            ticket_fb = buttons["ticket_fb"]
            ticket_reopen = buttons["ticket_reopen"]

            await ticket.send(
                "Willkommen! Ein Teammitglied wird sich bald bei dir melden.\nNutze den Button unten, um das Ticket zu schließen.",
                components=[ticket_close]
            )
            
            ticket_claim_message = (
                Embed(
                    title=f"Ticket Anfrage von {member}",
                    description=f"Klicke auf den Button, um das Ticket zu übernehmen.",
                    color="#008000"
                )
                .add_field(
                    name="Sobald das Ticket übernommen wurde, wird der Benutzer benachrichtigt.",
                    value="TICKET SYSTEM"
                )
            )

            # await claim.send("Klicke auf den Button, um das Ticket zu übernehmen.", components=[ticket_claim])
            # await claim.send(f"Benutzeranfrage von **{member}**")
            # await claim.send("Sobald das Ticket übernommen wurde, wird der Benutzer benachrichtigt.")

            await claim.send(embed=ticket_claim_message, components=[ticket_claim, ticket_release])
            total_ticket_count = await self.get_ticket_user(guild_id=guild.id, user_id=ctx.author_id)

            if total_ticket_count is None:
                # Es gibt noch keinen Eintrag → erstes Ticket
                ttc = 1
                await self.create_ticket(
                    guild_id=guild.id,
                    user_id=ctx.author_id,
                    total_ticket_count=ttc,
                    ticket_channel_id=ticket.id,
                    claim_channel_id=claim.id
                )
            else:
                # Es gibt schon einen Eintrag → hochzählen
                ttc = total_ticket_count["total_ticket_count"] + 1
                await self.update_ticket(
                    guild_id=guild.id,
                    user_id=ctx.author_id,
                    total_ticket_count=ttc,
                    ticket_channel_id=ticket.id,
                    claim_channel_id=claim.id
                )


        except Exception as e:
            await ctx.send(f"Fehler beim Erstellen des Tickets: `{e}`")






    @listen(Component)
    async def on_component(self, event: Component):
        ctx = event.ctx
        guild = ctx.guild
        await ctx.defer()
        buttons = self.create_ticket_buttons()
        ticket_reopen = buttons["ticket_reopen"]
        ticket_fb = buttons["ticket_fb"]
        ticket_close_confirm = buttons["ticket_close_confirm"]
        ticket_close_cancel = buttons["ticket_close_cancel"]

        l.info(f"[DEBUG] ctx.channel.id = {ctx.channel.id} | ctx.custom_id = {ctx.custom_id}")

        # Suche das Ticket per Ticket- oder Claim-Channel
        ticket_data = await self.get_ticket_by_any_channel(guild_id=guild.id, channel_id=ctx.channel.id)

        if ticket_data is None:
            await ctx.send("Fehler: Ticket nicht gefunden.")
            return

        # Channels aus DB holen
        try:
            ticket_channel = await guild.fetch_channel(ticket_data["ticket_channel_id"])
            claim_channel = await guild.fetch_channel(ticket_data["claim_channel_id"])
        except Exception as e:
            await ctx.send(f"Fehler beim Laden der Ticket-Kanäle: {e}")
            return

        ttc = ticket_data["total_ticket_count"]

        # Rollenberechtigungen setzen
        overwrite = PermissionOverwrite.for_target(ctx.author)
        overwrite.add_allows(Permissions.VIEW_CHANNEL)
        overwrite.add_denies(Permissions.SEND_MESSAGES)

        # Kategorien abrufen
        categories = await self.ensure_ticket_categories(guild)
        closed_ticket_cat = categories["closed-tickets"]

        match ctx.custom_id:
            case "ticket_fb":
                await ticket_channel.send("✅ Feedback wurde abgegeben.")


            case "ticket_close":
                await ticket_channel.send("Möchtest du dein Ticket wirklich schließen?")
                # await ticket_channel.edit(
                #     parent_id=closed_ticket_cat,
                #     name=(f"closed-{ticket_channel.name}-{ttc}")
                # )
                # await ticket_channel.edit_permission(overwrite=overwrite)
                # await ctx.message.edit(components=[])
                await ctx.send(components=[ticket_close_confirm, ticket_close_cancel])
                await ctx.send(components=ticket_fb)

            case "ticket_close_confirm":
                await ticket_channel.send("📪 Ticket wurde geschlossen.")
                await ticket_channel.edit(
                    parent_id=closed_ticket_cat,
                    name=(f"closed-{ticket_channel.name}-{ttc}")
                )
                await ticket_channel.edit_permission(overwrite=overwrite)
                await ctx.message.edit(components=[])
                await ticket_channel.send("Ticket wurde geschlossen - Mit deinem Feedback können wir wachsen")
                await ctx.send("Ein Admin kann das Ticket hier wieder öffnen:", components=ticket_reopen)

            case "ticket_close_cancel":
                await ticket_channel.send("Ticket wurde nicht geschlossen")

            case "claim_ticket":
                if ticket_data["stuff_member_id"] is None:
                    ticket_user = ticket_data["user_id"]
                    await self.update_ticket(guild_id=guild.id, user_id=ticket_user, stuff_member_id=ctx.member.id)
                    await ticket_channel.send(f"🎫 Ticket wurde von {ctx.member.display_name} übernommen.")
                    await ctx.send(f"Ticket erfolgreich von {ctx.member.user.username} übernommen.")
                    return
                
            case "ticket_reopen":
                await ctx.send("Das Ticket ist jetzt wieder geöffnet")


                try: 
                    stuff_member = await guild.fetch_member(ticket_data["stuff_member_id"])
                except Exception as e:
                    await ctx.send(f"ERROR: {e}")

                if ticket_data["stuff_member_id"] == ctx.member.id:
                    await ctx.send(f"DU '{stuff_member}' hast das Ticket bereits übernommen")
                    return
                elif ticket_data["stuff_member_id"] != ctx.member.id:
                    await ctx.send(f"Das Ticket wurde von {stuff_member} bereits übernommen")
                    return
                
            case "ticket_release":
                await ctx.send("TICKET RELEASE ACTION TRIGGERD | NO FUNCTION YET")

            case _:
                await ctx.send("Unbekannte Aktion.")


    #     pass
    @ticket.subcommand(
        sub_cmd_name="delete",
        sub_cmd_description="delete a ticket"
    )

    @slash_option(
        name="ticket_id",
        description="Which ticket you want to delete",
        opt_type=OptionType.STRING,
        required=False,
        # autocomplete=True
    )
    async def deleteTicket(self, ctx: SlashContext):
        try:
            await ctx.defer(ephemeral=True)

            guild = ctx.guild
            if not guild:
                await ctx.send("Guild Only")
                return
            
            member = ctx.member.user.username
            safe_name = member.lower().replace(" ", "-")
            ticket_name = f"{safe_name}-ticket"
            for channel in guild.channels:
                if channel and channel.name == ticket_name:
                    tchannel = await guild.fetch_channels()
                    ch= [channel.id for channel in tchannel if ticket_name in channel.name]
                    ch_id = ch[0]
                    l.info(f" list result of ticket_ch : {ch_id}")
                    # ticket_id = [channel.id for channel in ticket_ch]
                    ticket_ch = await guild.fetch_channel(ch_id)
                    # await channel.edit()
                    await guild.delete_channel(ticket_ch)
                    l.info(f"[TICKET] {channel.id}")
                    await ctx.send("ticket successfully closed")
                    break
            else:
                await ctx.send("ticket doesn't exist")

                
            
        


        except Exception as e:
            await ctx.send(f"Error during ticket deletion {e}")
    #TODO: create autocomplete function for the user/ticket which needs to be deleted or 
    # @ticket.autocomplete("channel")
    # async def autocomplete_ticket_channel(self, ctx: AutocompleteContext):
    #     try:

    # @listen
    # async def ticket_react_delete(self, event: ReactionUsers):
            
    @ticket.subcommand(
        sub_cmd_name="close",
        sub_cmd_description="close a ticket"
    )
    @slash_option(
        name="ticket_id",
        description="id or name of the ticket you want to remove (empty = you[if you have a ticket])",
        opt_type=OptionType.STRING,
        required=False
    )
    async def close_ticket(self, ctx: SlashContext):
        await ctx.defer(ephemeral=True)
        try:
            guild = ctx.guild 
            if not guild:
                await ctx.send("Guild Only")
                return
            
        except Exception as e:
            await ctx.send(f"Error during ticket closure: {e}")

    