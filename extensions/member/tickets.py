from datetime import datetime, timedelta
import logging as l
from time import sleep
from typing import Optional

from interactions import ActionRow, Embed, Button, ButtonStyle, ChannelType, Extension, Message, OptionType, PermissionOverwrite, Permissions, SlashContext, listen, slash_command, slash_option, StringSelectMenu
from interactions.api.events import Component
import asyncio

import pytz

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
                ticket_count INT,
                ticket_request_time INT,
                ticket_channel_id INT,
                bot_message_id INT,
                ticket_channel_feedback_id INT,
                ticket_message_id INT,
                ticket_archive_id INT,
                claim_channel_id INT,
                closed_channel_id INT,
                stuff_member_id INT,
                claim_message_id INT,
                claim_confirm_message_id INT,
                is_ticket_active INT,
                ticket_feedback TEXT
            );
        """)
        conn.commit()
        l.info("[TICKETS] SQL table ready.")

    async def create_ticket(self, guild_id: int, user_id: int, ticket_count:int, ticket_request_time: int, ticket_channel_id: int, bot_message_id: Optional[int] = None, ticket_channel_feedback_id : Optional[int] = None, ticket_message_id: Optional[int] = None, ticket_archive_id: Optional[int] = None, claim_channel_id: Optional[int] = None, closed_channel_id: Optional[int] = None, stuff_member_id: Optional[int] = None, claim_message_id: Optional[int]= None, claim_confirm_message_id: Optional[int] = None, is_ticket_active: Optional[int] = None, ticket_feedback: Optional[str] = None):
        """ [SQL] [TICKETS] : Create or update ticket in DB """
        insert_query = """
            INSERT INTO tickets (
                guild_id, user_id, ticket_count, ticket_request_time,
                ticket_channel_id, bot_message_id, ticket_channel_feedback_id, ticket_message_id,
                ticket_archive_id, claim_channel_id, closed_channel_id, stuff_member_id,
                claim_message_id, claim_confirm_message_id, is_ticket_active, ticket_feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        params = (
            guild_id,
            user_id,
            ticket_count,
            ticket_request_time,
            ticket_channel_id,
            bot_message_id,
            ticket_channel_feedback_id,
            ticket_message_id,
            ticket_archive_id,
            claim_channel_id,
            closed_channel_id,
            stuff_member_id,
            claim_message_id,
            claim_confirm_message_id,
            is_ticket_active,
            ticket_feedback
        )


        try:
            cursor.execute(insert_query, params)
            conn.commit()
            l.info(f"[TICKET | DB] Ticket created or updated for user {user_id}. Total tickets: {ticket_count}")
        except Exception as e:
            l.error(f"[TICKET | DB] Error during ticket creation: {e}")


    async def user_has_active_ticket(self, guild_id: int, user_id: int) -> bool:
        cursor.execute("""
            SELECT 1 FROM tickets 
            WHERE guild_id = ? AND user_id = ? AND is_ticket_active = 1
            LIMIT 1
        """, (guild_id, user_id))
        result = cursor.fetchone()
        return result is not None
    
    async def get_active_ticket_for_user(self, guild_id: int, user_id: int):
        cursor.execute("""
            SELECT * FROM tickets
            WHERE guild_id = ? AND user_id = ? AND is_ticket_active = 1
            ORDER BY ticket_count DESC
            LIMIT 1
        """, (guild_id, user_id))
        return cursor.fetchone()

    async def get_next_ticket_number(self, guild_id: int, user_id: int) -> int:
        cursor.execute("""
            SELECT MAX(ticket_count) FROM tickets
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id))
        result = cursor.fetchone()
        return (result[0] + 1) if result and result[0] is not None else 1
    
    async def update_ticket(self, guild_id: int, user_id: int, ticket_count: int, ticket_request_time: Optional[int] = None, ticket_channel_id: Optional[int] = None, bot_message_id: Optional[int] = None, ticket_channel_feedback_id: Optional[int] = None, ticket_message_id: Optional[int] = None, ticket_archive_id: Optional[int] = None, claim_channel_id: Optional[int] = None, closed_channel_id: Optional[int] = None, stuff_member_id: Optional[int] = None, claim_message_id: Optional[int] = None, claim_confirm_message_id: Optional[int] = None, is_ticket_active: Optional[int] = None, ticket_feedback: Optional[str] = None):
            try:
                cursor.execute("""
                    SELECT * FROM tickets
                    WHERE guild_id = ? AND user_id = ? AND ticket_count = ?
                """, (guild_id, user_id, ticket_count))
                ticket = cursor.fetchone()
                if not ticket:
                    l.warning(f"[TICKETS | DB] Tried to update non-existing ticket {user_id}#{ticket_count}")
                    return

                ticket_request_time = ticket_request_time if ticket_request_time is not None else ticket[3]
                ticket_channel_id = ticket_channel_id if ticket_channel_id is not None else ticket[4]
                bot_message_id = bot_message_id if bot_message_id is not None else ticket[5]
                ticket_channel_feedback_id = ticket_channel_feedback_id if ticket_channel_feedback_id is not None else ticket[6]
                ticket_message_id = ticket_message_id if ticket_message_id is not None else ticket[7]
                ticket_archive_id = ticket_archive_id if ticket_archive_id is not None else ticket[8]
                claim_channel_id = claim_channel_id if claim_channel_id is not None else ticket[9]
                closed_channel_id = closed_channel_id if closed_channel_id is not None else ticket[10]
                stuff_member_id = stuff_member_id if stuff_member_id is not None else ticket[11]
                claim_message_id = claim_message_id if claim_message_id is not None else ticket[12]
                claim_confirm_message_id = claim_confirm_message_id if claim_confirm_message_id is not None else ticket[13]
                is_ticket_active = is_ticket_active if is_ticket_active is not None else ticket[14]
                ticket_feedback = ticket_feedback if ticket_feedback is not None else ticket[15]

                update_query = """
                    UPDATE tickets 
                    SET ticket_request_time = ?,
                        ticket_channel_id = ?,
                        bot_message_id = ?,
                        ticket_channel_feedback_id = ?,
                        ticket_message_id = ?,
                        ticket_archive_id = ?,
                        claim_channel_id = ?,
                        closed_channel_id = ?,
                        stuff_member_id = ?,
                        claim_message_id = ?,
                        claim_confirm_message_id = ?,
                        is_ticket_active = ?,
                        ticket_feedback = ?
                    WHERE guild_id = ? AND user_id = ? AND ticket_count = ?;
                """
                params = (ticket_request_time, ticket_channel_id, bot_message_id, ticket_channel_feedback_id, ticket_message_id, ticket_archive_id, claim_channel_id, closed_channel_id, stuff_member_id, claim_message_id, claim_confirm_message_id, is_ticket_active, ticket_feedback, guild_id, user_id, ticket_count)
                cursor.execute(update_query, params)
                conn.commit()
                l.info(f"[TICKET | DB] Ticket updated for user {user_id}#{ticket_count} with is_ticket_active={is_ticket_active}")

            except Exception as e:
                l.error(f"[TICKETS | DB] Error during ticket update: {e}")


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

    async def get_active_ticket_for_user(self, guild_id: int, user_id: int):
        cursor.execute("""
            SELECT * FROM tickets
            WHERE guild_id = ? AND user_id = ? AND is_ticket_active = 1
            ORDER BY ticket_count DESC
            LIMIT 1
        """, (guild_id, user_id))
        return cursor.fetchone()

    async def get_ticket_by_any_channel(self, guild_id: int, channel_id: int):
            try:
                l.info(f"[DEBUG] Suche Ticket mit guild_id={guild_id}, channel_id={channel_id}")
                cursor.execute("""
                    SELECT * FROM tickets
                    WHERE guild_id = ? AND (ticket_channel_id = ? OR claim_channel_id = ?)
                """, (guild_id, channel_id, channel_id))
                rows = cursor.fetchone()
                l.info(f"ROWS: {rows}")
                return rows
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
            placeholder="Wurde dein Anliegen gelöst?",
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
            # Prüfen, ob bereits ein aktives Ticket existiert
            if await self.user_has_active_ticket(guild.id, ctx.author_id):
                await ctx.send("❗ Du hast bereits ein aktives Ticket.")
                return

            # Kategorien vorbereiten
            claim_channel_data = await self.ensure_claim_channel(guild)
            claim_channel = claim_channel_data["claim_channel"]

            categories = await self.ensure_ticket_categories(guild)
            ticket_cat = categories["tickets"]

            # Channelnamen vorbereiten
            member = ctx.member.user.username
            safe_name = member.lower().replace(" ", "-")
            ticket_name = f"{safe_name}-ticket"

            # Falls Channel schon existiert (unwahrscheinlich bei neuer Nummer), abbrechen
            for channel in guild.channels:
                if channel.name == ticket_name:
                    await ctx.send(f"⚠️ Du hast bereits ein Ticket: <#{channel.id}>")
                    return

            # Berechtigungen setzen
            overwrite = PermissionOverwrite.for_target(ctx.author)
            overwrite.add_allows(Permissions.VIEW_CHANNEL)

            # Channel erstellen
            ticket = await guild.create_text_channel(name=ticket_name, category=ticket_cat)
            await ticket.edit_permission(overwrite=overwrite)

            await ctx.send(f"✅ Dein Ticket wurde erstellt: <#{ticket.id}>")

            # UI-Komponenten
            buttons = self.create_ticket_buttons()
            ticket_close = buttons["ticket_close"]
            ticket_reopen = buttons["ticket_reopen"]
            ticket_claim = buttons["ticket_claim"]
            ticket_release = buttons["ticket_release"]
            berlin_tz = pytz.timezone("Europe/Berlin")
            now_berlin = datetime.now(berlin_tz)
            now = int(now_berlin.timestamp())
            issue = ctx.kwargs["issue"]

            # Embed im Ticket-Channel
            embed_ticket = (
                Embed(
                    title=f"🎟️ Ticket für {member}",
                    description=f"Du hast folgendes gemeldet:\n\n**{issue}**\n\nBitte habe etwas Geduld.\nSollte sich innerhalb 4 Tagen niemand bei dir melden wird das Problem an das Modteam eskaliert",
                )
                .add_field(name="⏰ Erstellt am", value=f"<t:{now}:f>")
            )
            ticket_message = await ticket.send(embed=embed_ticket, components=[ticket_close, ticket_reopen])
            await ticket_message.pin()

            # Embed im Claim-Channel
            embed_claim = (
                Embed(
                    title=f"📥 Neues Ticket von {member}",
                    description="Klicke unten, um dieses Ticket zu übernehmen.",
                )
                .add_field(name="Problem", value=issue)
                .add_field(name="Zeitpunkt", value=f"<t:{now}:f>")
            )
            claim_message = await claim_channel.send(embed=embed_claim, components=[ticket_claim, ticket_release])

            # Ticketnummer berechnen
            next_ticket_number = await self.get_next_ticket_number(guild.id, ctx.author_id)

            # Eintrag in die Datenbank
            await self.create_ticket(
                guild_id=guild.id,
                user_id=ctx.author_id,
                ticket_count=next_ticket_number,
                ticket_request_time=now,
                ticket_channel_id=ticket.id,
                ticket_message_id=ticket_message.id,
                claim_channel_id=claim_channel.id,
                claim_message_id=claim_message.id,
                is_ticket_active=1
            )

        except Exception as e:
            await ctx.send(f"Fehler beim Erstellen des Tickets: `{e}`")






    @listen(Component)
    async def on_component(self, event: Component):
        ctx = event.ctx
        guild = ctx.guild
        await ctx.defer(edit_origin=True)

        if not guild:
            await ctx.send("Nur in einem Server nutzbar.")
            return

        buttons = self.create_ticket_buttons()
        ticket_data = await self.get_ticket_by_any_channel(guild.id, ctx.channel.id)
        if not ticket_data:
            await ctx.send("Fehler: Kein Ticket zu diesem Channel gefunden.")
            return

        user_id = ticket_data[1]
        ticket_channel = await guild.fetch_channel(ticket_data[4])
        claim_channel = await guild.fetch_channel(ticket_data["claim_channel_id"])
        ticket_msg_id = ticket_data[7]
        bot_msg_id = ticket_data[6]
        second_fb_id = ticket_data ["bot_message_id"]
        claim_msg_id = ticket_data["claim_message_id"]
        claim_msg = await claim_channel.fetch_message(claim_msg_id) if claim_msg_id else None
        ticket_msg = await ticket_channel.fetch_message(ticket_msg_id) if ticket_msg_id else None
        bot_msg = await ticket_channel.fetch_message(bot_msg_id) if bot_msg_id else None
        second_fb = await ticket_channel.fetch_message(second_fb_id) if second_fb_id else None
        user = await guild.fetch_member(user_id)
        berlin_tz = pytz.timezone("Europe/Berlin")
        now_berlin = datetime.now(berlin_tz)
        now = int(now_berlin.timestamp())

        match ctx.custom_id:
            case "ticket_close":
                if bot_msg is not None:
                    await ctx.send("Es gibt bereits eine Schließen-Abfrage.")
                    return
                embed_ticket_close = Embed(title="Möchtest du dein Ticket wirklich schließen?")
                close_prompt = await ticket_channel.send(
                    embed=embed_ticket_close,
                    components=[
                        ActionRow(buttons["ticket_fb"]),
                        ActionRow(
                            buttons["ticket_delete_confirm"],
                            buttons["ticket_close_confirm"],
                            buttons["ticket_close_cancel"]
                        )
                    ]
                )
                ticket_data = await self.get_active_ticket_for_user(guild.id, user_id)
                if ticket_data:
                    ticket_count = ticket_data[2]  # Index 2 ist ticket_count
                    await self.update_ticket(
                        guild_id=guild.id,
                        user_id=user_id,
                        ticket_count=ticket_count,
                        ticket_channel_feedback_id=close_prompt.id
                    )

            case "ticket_fb":
                content = ctx.values[0]
                await ticket_channel.send(f"✅ Feedback wurde abgegeben: {content}", delete_after=5)

                prefixes = ["✅-", "❌-", "❔-"]
                base_name = ticket_channel.name
                for prefix in prefixes:
                    if base_name.startswith(prefix):
                        base_name = base_name[len(prefix):]
                        break

                new_name = {
                    "Ja": f"✅-{base_name}",
                    "Nein": f"❌-{base_name}",
                    "Andere": f"❔-{base_name}"
                }.get(content, base_name)
                await ticket_channel.edit(name=new_name)
                # Feedback wurde gesetzt → neuer Prefix ist enthalten
                has_prefix = any(new_name.startswith(p) for p in prefixes)

                category = await self.ensure_ticket_categories(guild)
                if bot_msg and ticket_channel.parent_id == category["closed-tickets"].id and has_prefix:
                    await bot_msg.delete()

                if second_fb and ticket_channel.parent_id == category["closed-tickets"].id and has_prefix:
                    await second_fb.edit(components=[])
                    await second_fb.edit(components=                        
                        ActionRow(
                            buttons["ticket_delete_confirm"],
                            buttons["ticket_reopen"]
                        ))
                    
                ticket_data = await self.get_active_ticket_for_user(guild.id, user_id)
                if ticket_data:
                    ticket_count = ticket_data[2]  # Index 2 ist ticket_count
                    await self.update_ticket(
                        guild_id=guild.id,
                        user_id=user_id,
                        ticket_count=ticket_count,
                        ticket_feedback= content
                    )


            case "ticket_close_confirm":
                await claim_msg.delete()
                await ticket_msg.edit(components=[])

                prefixes = ["✅-", "❌-", "❔-"]
                current_name = ticket_channel.name
                has_feedback_prefix = any(current_name.startswith(p) for p in prefixes)

                # Base-Name ermitteln
                if has_feedback_prefix:
                    base_name = current_name
                else:
                    base_name = current_name
                    for prefix in prefixes:
                        if current_name.startswith(prefix):
                            base_name = current_name[len(prefix):]
                            break

                # Entferne doppeltes "-closed"
                if base_name.endswith("-closed"):
                    base_name = base_name[: -len("-closed")]
                if user:
                    new_perms = PermissionOverwrite.for_target(user)
                    if new_perms:
                        new_perms.add_allows(Permissions.VIEW_CHANNEL)
                        new_perms.add_denies(Permissions.SEND_MESSAGES)
                        await ticket_channel.edit_permission(overwrite=new_perms)
                    else:
                        l.warning(f"[TICKETS] Konnte keine PermissionOverwrite für {user} erzeugen.")
                else:
                    l.warning(f"[TICKETS] User mit ID {user_id} konnte nicht gefunden werden.")



                await self.update_ticket(
                    guild_id=guild.id,
                    user_id=user_id,
                    ticket_count=ticket_data[2],  # <--- auch hier!
                    is_ticket_active=0
                )

                await ticket_channel.edit(
                    name=f"{base_name}-{ticket_data[2]}-closed",
                    parent_id=(await self.ensure_ticket_categories(guild))["closed-tickets"].id,
                )



                user_mention = (await guild.fetch_member(user_id)).mention
                closing_mention = ctx.member.mention

                if ctx.author.id == user_id:
                    notice = f"📪 Ticket wurde geschlossen. Vielen Dank, {user_mention}!"
                else:
                    notice = f"🔒 Ticket wurde von {closing_mention} archiviert."
                await ticket_channel.send(notice)


                # if new_feedback:
                #     # await self.update_ticket(
                #     #     guild_id=guild.id,
                #     #     user_id=user_id,
                #     #     ticket_count=ticket_data[2],  # <--- auch hier!
                #     #     is_ticket_active=0,
                #     #     bot_message_id=new_feedback.id
                #     # )
                #     fb_2nd_chance_timer_time = int((now_berlin+ timedelta(minutes=2)).timestamp()) 
                #     fb_2nd_chance_timer = await ticket_channel.send(f"⏳ Timer gestartet – Die Möglichkeit Feedback zu geben endet am <t:{fb_2nd_chance_timer_time}:t> (<t:{fb_2nd_chance_timer_time}:R>)")
                #     await asyncio.sleep(120)
                #     await ticket_msg.edit(components=[])
                #     await ticket_msg.edit(components=[                        
                #         ActionRow(
                #             buttons["ticket_delete_confirm"],
                #             buttons["ticket_reopen"]
                #         )])
                #     await fb_2nd_chance_timer.delete()


                if has_feedback_prefix:
                    await ticket_msg.edit(components=[
                        ActionRow(
                            buttons["ticket_delete_confirm"],
                            buttons["ticket_reopen"]
                        )
                    ])

                if not has_feedback_prefix:
                    new_feedback = await ticket_msg.edit(components=[
                        ActionRow(
                            buttons["ticket_fb"]
                        ),
                        ActionRow(
                            buttons["ticket_delete_confirm"],
                            buttons["ticket_reopen"]
                        )
                    ])
                    await self.update_ticket(
                        guild_id=guild.id,
                        user_id=user_id,
                        ticket_count=ticket_data[2],  # <--- auch hier!
                        is_ticket_active=0,
                        bot_message_id=new_feedback.id
                    )


                # Feedback-Prompt löschen, falls vorhanden
                if bot_msg:
                    await bot_msg.delete()

                # if second_fb:
                #     await second_fb.edit(components=[])
                #     await second_fb.edit(components=                        
                #         ActionRow(
                #             buttons["ticket_delete_confirm"],
                #             buttons["ticket_reopen"]
                #         ))


                    




            case "ticket_close_cancel":
                if bot_msg:
                    await bot_msg.delete()

            case "ticket_delete_confirm":
                await claim_msg.delete()
                await ticket_channel.send("🔒 Ticket wird gelöscht...")
                await asyncio.sleep(3)
                await ticket_channel.delete()
                await self.update_ticket(
                    guild_id=guild.id,
                    user_id=user_id,
                    ticket_count=ticket_data[2],  # <--- auch hier!
                    is_ticket_active=0
                )
            case "claim_ticket":
                if not ctx.member or not ctx.member.user:
                    await ctx.send("❗ Fehler: Kein Mitglied gefunden.")
                    return

                staff_member_id = ctx.author.id
                staff_member_name = ctx.author.user.username
                ticket_owner = await guild.fetch_member(user_id)
                
                # Berechtigungen für Staff setzen
                overwrite = PermissionOverwrite.for_target(ctx.author)
                overwrite.add_allows(Permissions.VIEW_CHANNEL, Permissions.SEND_MESSAGES)
                await ticket_channel.edit_permission(overwrite=overwrite)
                

                await ticket_channel.send(
                    f"🎫 Ticket wurde von {ctx.author.mention} übernommen. {ticket_owner.mention}, du wirst bald Unterstützung erhalten."
                )

                await self.update_ticket(
                    guild_id=guild.id,
                    user_id=user_id,
                    ticket_count=ticket_data[2],  # wichtig
                    stuff_member_id=staff_member_id
                )

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

    