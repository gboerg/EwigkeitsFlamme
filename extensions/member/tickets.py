from datetime import datetime
import logging as l
from datetime import datetime
from time import sleep
from typing import Optional

from interactions import ActionRow, Embed, Button, ButtonStyle, ChannelType, Extension, Message, OptionType, PermissionOverwrite, Permissions, SlashContext, listen, slash_command, slash_option, StringSelectMenu
from interactions.api.events import Component
import asyncio

from database import conn, cursor

class Tickets(Extension):
    def __init__(self, bot):
        self.bot = bot
        self.claim_channel_lock = asyncio.Lock()
        l.info("[TICKETS] Initializing SQL database...")
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS tickets (
                guild_id INTEGER,
                user_id INT,
                total_ticket_count INT,
                ticket_request_time INT,
                ticket_channel_id INT,
                ticket_message_id INT,
                ticket_archive_id INT,
                claim_channel_id INT,
                closed_channel_id INT,
                stuff_member_id INT,
                claim_message_id INT,
                claim_confirm_message_id INT,
                ticket_reopen_id INT,
                ticket_reopen_archive INT,
                tickt_reopen_stuff_id INT,
                ticket_reopen_confirm INT,
                total_active_tickets INT
            );
        """)
        conn.commit()
        l.info("[TICKETS] SQL table ready.")

    async def create_ticket(self, guild_id: int, user_id: int, total_ticket_count:int, ticket_request_time: int, ticket_channel_id: int, ticket_message_id: Optional[int] = None, ticket_archive_id: Optional[int] = None, claim_channel_id: Optional[int] = None, closed_channel_id: Optional[int] = None, stuff_member_id: Optional[int] = None, claim_message_id: Optional[int]= None, claim_confirm_message_id: Optional[int] = None):
        """ [SQL] [TICKETS] : Create or update ticket in DB """
        insert_query = """
            INSERT INTO tickets (
                guild_id, user_id, total_ticket_count, ticket_request_time, ticket_channel_id, ticket_message_id, ticket_archive_id, claim_channel_id, closed_channel_id, stuff_member_id, claim_message_id, claim_confirm_message_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            guild_id,
            user_id,
            total_ticket_count,
            ticket_request_time,
            ticket_channel_id,
            ticket_message_id,
            ticket_archive_id,
            claim_channel_id,
            closed_channel_id,
            stuff_member_id,
            claim_message_id,
            claim_confirm_message_id
        )

        try:
            cursor.execute(insert_query, params)
            conn.commit()
            l.info(f"[TICKET | DB] Ticket created or updated for user {user_id}. Total tickets: {total_ticket_count}")
        except Exception as e:
            l.error(f"[TICKET | DB] Error during ticket creation: {e}")

    async def update_ticket(self, guild_id: int, user_id: int, total_ticket_count: Optional [int] = None, ticket_request_time: Optional [int] = None, ticket_channel_id: Optional[int] = None, ticket_message_id: Optional[int] = None, ticket_archive_id: Optional[int] = None, claim_channel_id: Optional[int] = None, closed_channel_id: Optional[int] = None, stuff_member_id: Optional[int] = None, claim_message_id: Optional[int] = None, claim_confirm_message_id: Optional[int] = None):
        try:

            tickets = await self.get_ticket_user(guild_id, user_id) 
            if not tickets: 
                l.warning(f"[TICKETS | DB] Tried to update non existing ticket {user_id}")
                return
            
            total_ticket_count = total_ticket_count if total_ticket_count is not None else tickets["total_ticket_count"]
            ticket_request_time = ticket_request_time if ticket_request_time is not None else tickets["ticket_request_time"]
            ticket_channel_id = ticket_channel_id if ticket_channel_id is not None else tickets["ticket_channel_id"]
            claim_channel_id = claim_channel_id if claim_channel_id is not None else tickets["claim_channel_id"]
            closed_channel_id = closed_channel_id if closed_channel_id is not None else tickets["closed_channel_id"]
            # claim_message_id = claim_message_id if claim_message_id is not None else tickets["claim_message_id"]

            """
            [TICKET | DB] Updatet das Ticket mit den mitgegebenen Parametern - wenn kein Parameter mitgegeben wird  
            """
            
            update_query = """
                UPDATE tickets 
                SET total_ticket_count = ?,
                    ticket_request_time = ?,
                    ticket_channel_id = ?,
                    ticket_message_id = ?,
                    ticket_archive_id = ?,
                    claim_channel_id = ?,
                    closed_channel_id = ?,
                    stuff_member_id = ?,
                    claim_message_id = ?,
                    claim_confirm_message_id = ?
                WHERE guild_id = ? AND user_id = ?;
                """
            params = (total_ticket_count, ticket_channel_id, ticket_message_id, ticket_archive_id, claim_channel_id, closed_channel_id, stuff_member_id, claim_message_id, claim_confirm_message_id, guild_id, user_id)
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
                    "ticket_request_time": row[3],
                    "ticket_channel_id": row[4],
                    "ticket_message_id": row[5],
                    "ticket_archive_id": row[6],
                    "claim_channel_id": row[7],
                    "closed_channel_id": row[8],
                    "stuff_member_id": row[9],
                    "claim_message_id": row[10],
                    "claim_confirm_message_id": row[11]
                }
            l.warning("[DEBUG] Kein Ticket gefunden mit diesem Channel.")
            return None
        except Exception as e:
            l.error(f"[TICKET | DB] Error fetching ticket by any channel: {e}")
            return None
    @slash_command(
            name="ticket",
            description="central ticket comment - Here you can create or close a ticket",
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
        ticket_delete_confirm = Button(
            custom_id="ticket_delete_confirm",
            style=ButtonStyle.DANGER,
            label="Löschen"
        )
        ticket_close_confirm = Button(
            custom_id="ticket_close_confirm",
            style=ButtonStyle.GREY,
            label="Archivieren"
        )

        ticket_close_cancel = Button(
            custom_id="ticket_close_cancel",
            style=ButtonStyle.GREEN,
            label="Abbrechen"
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
            label="Claim",
        )

        ticket_release = Button(
            custom_id="ticket_release",
            style=ButtonStyle.GREY,
            label="unClaim",
        )

        ticket_reopen = Button(
            custom_id="ticket_reopen",
            style=ButtonStyle.GREEN,
            label="ReOpen",
        )

        return {
            "ticket_close": ticket_close,
            "ticket_delete_confirm": ticket_delete_confirm,
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
            "ticket-feeback": {
                "overwrites": [
                    PermissionOverwrite(
                        id=guild.id,
                        type=0,
                        deny=Permissions.VIEW_CHANNEL
                    )
                ]
            }
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
        
    async def ensure_claim_channel(self, guild):
        async with self.claim_channel_lock:
            # Prüfe: existiert die Kategorie "claim-tickets"?
            category = next((c for c in guild.channels if c.type == ChannelType.GUILD_CATEGORY and c.name == "claim-tickets"), None)

            if category is None:
                # Kategorie erstellen
                category = await guild.create_category(name="claim-tickets")
                await category.edit(permission_overwrites=[
                    PermissionOverwrite(
                        id=guild.id,
                        type=0,
                        deny=Permissions.VIEW_CHANNEL
                    )
                ])

            # Prüfe: existiert der Textchannel "claim-tickets"?
            text_channel = next((c for c in guild.channels if c.type == ChannelType.GUILD_TEXT and c.name == "claim-tickets"), None)

            if text_channel:
                # Falls der Channel existiert, aber nicht in der richtigen Kategorie ist → verschieben
                if text_channel.parent_id != category.id:
                    await text_channel.edit(parent_id=category.id)
                return { "claim_channel": text_channel }

            # Channel noch nicht da → erstellen
            claim_channel = await guild.create_text_channel(name="claim-tickets", category=category)
            await claim_channel.edit(permission_overwrites=[
                PermissionOverwrite(
                    id=guild.id,
                    type=0,
                    deny=Permissions.VIEW_CHANNEL
                )
            ])

            return { "claim_channel": claim_channel }

    @ticket.subcommand(
        sub_cmd_name="create",
        sub_cmd_description="create a ticket",
    )
    @slash_option(
        name="issue",
        description="the issue you having - Or reason of the ticket",
        opt_type=OptionType.STRING,
        required=True
    )
    async def createTicket(self, ctx: SlashContext):
        await ctx.defer(ephemeral=True)
        guild = ctx.guild
        if not guild:
            await ctx.send("Dieser Befehl funktioniert nur in einem Server.")
            return

        try:
            # Kategorien und Channels
            claim_channel_data = await self.ensure_claim_channel(guild)
            claim_channel = claim_channel_data["claim_channel"]

            categories = await self.ensure_ticket_categories(guild)
            ticket_cat = categories["tickets"]

            member = ctx.member.user.username
            safe_name = member.lower().replace(" ", "-")
            ticket_name = f"{safe_name}-ticket"

            for channel in guild.channels:
                if channel.name == ticket_name:
                    await ctx.send(f"Du hast bereits ein Ticket: <#{channel.id}>")
                    return

            # Berechtigungen
            overwrite = PermissionOverwrite.for_target(ctx.author)
            overwrite.add_allows(Permissions.VIEW_CHANNEL)

            # Channel erstellen
            ticket = await guild.create_text_channel(name=ticket_name, category=ticket_cat)
            await ticket.edit_permission(overwrite=overwrite)

            await ctx.send(f"Dein Ticket wurde erstellt: <#{ticket.id}>")

            # Komponenten
            buttons = self.create_ticket_buttons()
            ticket_close = buttons["ticket_close"]
            ticket_claim = buttons["ticket_claim"]
            ticket_release = buttons["ticket_release"]
            ticket_fb = buttons["ticket_fb"]
            ticket_reopen = buttons["ticket_reopen"]

            now = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            issue = ctx.kwargs["issue"]

            ticket_message = None
            claim_message = None

            # Nachricht im Ticket-Channel
            try:
                embed_ticket = (
                    Embed(
                        title=f"Vielen Dank, dass du unser Ticket System nutzt {member} \nWenn das Problem nicht mehr besteht - Nutze den Button unten, um das Ticket zu schließen",
                        description=f"Du hast uns folgendes Problem mitgeteilt:\n\n**{issue}**\n\nSollte sich etwas daran ändern, kannst du uns das hier im Chat mitteilen",
                    )
                    .add_field(
                        name=f"Anfrage gestellt um {now}",
                        value="Bitte habe etwas Geduld. Nach 4 Tagen erfolgt ggf. automatische Eskalation an das Modteam.",
                    )
                )

                ticket_message = await ticket.send(embed=embed_ticket, components=[ticket_close, ticket_reopen])
                await ticket_message.pin()
            except Exception as e:
                await ctx.send(f"Fehler beim Senden der Ticketnachricht: `{e}`")
                return

            # Nachricht im Claim-Channel
            try:
                embed_claim = (
                    Embed(
                        title=f"Ticket-Anfrage von {member}",
                        description="Klicke auf den Button, um das Ticket zu übernehmen.",
                    )
                    .add_field(name="Benutzermeldung", value=issue)
                    .add_field(name="Info", value="Sobald das Ticket übernommen wurde, wird der Benutzer benachrichtigt.")
                    .add_field(name="Anfrage gestellt am", value=now)
                )

                claim_message = await claim_channel.send(embed=embed_claim, components=[ticket_claim, ticket_release])
            except Exception as e:
                await ctx.send(f"Fehler beim Senden in den Claim-Channel: `{e}`")
                return

            # Datenbankeintrag
            ticket_msg_id = ticket_message.id if ticket_message else None
            claim_msg_id = claim_message.id if claim_message else None

            ticket_count = await self.get_ticket_user(guild.id, ctx.author_id)
            ttc = (ticket_count["total_ticket_count"] + 1) if ticket_count else 1

            if ticket_count is None:
                await self.create_ticket(
                    guild_id=guild.id,
                    user_id=ctx.author_id,
                    total_ticket_count=ttc,
                    ticket_channel_id=ticket.id,
                    ticket_message_id=ticket_msg_id,
                    claim_channel_id=claim_channel.id,
                    claim_message_id=claim_msg_id,
                    claim_confirm_message_id=None  # kann später ergänzt werden
                )
            else:
                await self.update_ticket(
                    guild_id=guild.id,
                    user_id=ctx.author_id,
                    total_ticket_count=ttc,
                    ticket_channel_id=ticket.id,
                    ticket_message_id=ticket_msg_id,
                    claim_channel_id=claim_channel.id,
                    claim_message_id=claim_msg_id
                )

        except Exception as e:
            await ctx.send(f"Fehler beim Erstellen des Tickets: `{e}`")






    @listen(Component)
    async def on_component(self, event: Component):
        ctx = event.ctx
        guild = ctx.guild
        
        buttons = self.create_ticket_buttons()
        ticket_reopen = buttons["ticket_reopen"]
        ticket_fb = buttons["ticket_fb"]
        ticket_close_confirm = buttons["ticket_close_confirm"]
        ticket_close_cancel = buttons["ticket_close_cancel"]
        ticket_delete_confirm = buttons["ticket_delete_confirm"]


        l.info(f"[DEBUG] ctx.channel.id = {ctx.channel.id} | ctx.custom_id = {ctx.custom_id}")

        # Suche das Ticket per Ticket- oder Claim-Channel
        ticket_data = await self.get_ticket_by_any_channel(guild_id=guild.id, channel_id=ctx.channel.id)
        get_user_name = ticket_data["user_id"]
        user = await guild.fetch_member(get_user_name)
        user_m = user.mention


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





        get_message_id = await self.get_ticket_by_any_channel(guild_id=guild.id, channel_id=ctx.channel.id)
        l.info(f"Claim user id = {get_message_id}")

        claim_m_id = get_message_id["claim_message_id"]
        ticket_m_id = get_message_id["ticket_channel_id"]
        claimed_c_id = get_message_id["claim_confirm_message_id"]

        claim_message_id = claim_channel.get_message(claim_m_id)
        ticket_m_id = ticket_channel.get_message(ticket_m_id)
        claimed_confirm_m_id = claim_channel.get_message(claimed_c_id)



        match ctx.custom_id:




            case "ticket_close":
                self.to_delete = await ticket_channel.send(content="Möchtest du dein Ticket wirklich schließen", components=[
                    ActionRow(ticket_fb),
                    ActionRow(ticket_delete_confirm, ticket_close_confirm, ticket_close_cancel)
                    ]
                )

            case "ticket_fb":
                await ctx.defer()
                content = ctx.kwargs
                await ticket_channel.send(f"✅ Feedback wurde abgegeben. {content}")

            case "ticket_close_cancel":
                await self.to_delete.delete()
                delayed_info_delete= await ticket_channel.send("Ticket wurde nicht geschlossen")
                await sleep(10)
                await delayed_info_delete.delete()
                    

            case "ticket_close_confirm":
                await ctx.defer()

                if ctx.author.id == ticket_data["user_id"]:
                    await ticket_channel.send(f"📪 Ticket wurde geschlossen. \nvielen Dank {user_m}, dass du unser Ticket System genutzt hast")

                elif ctx.member.has_permission(Permissions.KICK_MEMBERS):
                    await ticket_channel.send(f"Ticket wurde von {ctx.member.mention} archiviert")

                await ticket_channel.edit(
                    parent_id=closed_ticket_cat,
                    name=(f"closed-{ticket_channel.name}-{ttc}")
                )

                await ticket_channel.edit_permission(overwrite=overwrite)
                await ctx.message.edit(components=[])

                await claimed_confirm_m_id.delete()
                await claim_message_id.delete()

                
            case "ticket_delete_confirm":
                # await ctx.defer()


                if ctx.author.id == ticket_data["user_id"]:


                    await ticket_channel.send(f"Vielen Dank {user_m}, dieser Channel wird in Kürze gelöscht und nicht Archiviert \nSolltest du in Zukunft wieder hilfe benötigen kannst du mit: **/ticket create 'dein problem'** wieder ein Ticket eröffnen \nKehre nun wieder zurück uns bis zum nächsten mal {user}")
                    sleep(20)
                    await ticket_channel.delete()
                    await claim_message_id.delete()
                    await claimed_confirm_m_id.delete()
                    # await claim_channel.delete()
                #DATABASE decrease ticket count and delete last ticket 
                elif ctx.member.has_permission(Permissions.MANAGE_CHANNELS):
                    await ticket_channel.send("🔒 Ticket wurde vom Teammitglied gelöscht")
                    sleep(6)
                    await ticket_channel.delete()
                    await claim_message_id.delete()
                    await claimed_confirm_m_id.delete()
                    # await claim_channel.delete()




                
            case "ticket_reopen":
                await ctx.defer()
                if not ctx.member.has_permission(Permissions.KICK_MEMBERS):
                    await ctx.send(f"Hallo {user.mention}, Nur ein ein Teammitglied kann das Ticket erneut öffnen")
                    return
                await ticket_channel.add_permission(Permissions.SEND_MESSAGES)
                await ctx.send("Das Ticket ist jetzt wieder geöffnet")


                
            #  IN CLAIM CHANNEL  
            case "claim_ticket":
                await ctx.defer()
                if ticket_data["stuff_member_id"] is None:
                    ticket_member = ticket_data["user_id"]
                    member = await guild.fetch_member(ticket_member)



                    ticket_user = ticket_data["user_id"]
                    mention_ticket_user = await guild.fetch_member(ticket_user)
                    mm = mention_ticket_user


                    self.ticket_open_message.add_field(
                        name=f"Ticket wurde übernommen von:",
                        value=f"{ctx.member}"
                    )
                    # await self.ticket_message.edit(embed=self.ticket_open_message)
                    # await ticket_channel.send(f"{mm}, dein Ticket wurde übernommen")
                    claimed = await ticket_channel.send(f"🎫 Hallo {mm.mention}, dein Ticket wurde von {ctx.member.mention} übernommen.")
                    await claimed.pin()
                    claimed_confirm = await ctx.send(f"Ticket erfolgreich von {ctx.member.user.username} übernommen.")
                    await self.update_ticket(guild_id=guild.id, user_id=ticket_user, stuff_member_id=ctx.member.id, ticket_message_id=ticket_m_id, claim_message_id=claim_m_id, claim_confirm_message_id=claimed_confirm.id)
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
                await ctx.defer()
                await ctx.send("TICKET RELEASE ACTION TRIGGERD | NO FUNCTION YET")

            case _:
                await ctx.defer()
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

    