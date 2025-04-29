from calendar import c
import logging
import logging as l
import os
from datetime import datetime, timedelta
from http.client import responses
from numbers import Number
import typing
import urllib.request
from typing import Optional, Union

import aiohttp
import interactions
# import pandas
import pytz
from easy_pil import Editor, Font
from interactions import (
    Client,
    Extension,
    Guild,
    IntervalTrigger,
    ScheduledEvent,
    SlashContext,
    Task,
    slash_command,
    Permissions,
    slash_option,
    OptionType,
    ChannelType, AutocompleteContext, ScheduledEventType, File, listen, User, )
from interactions.api.events import GuildScheduledEventCreate, GuildScheduledEventUpdate, GuildScheduledEventDelete
from interactions.client.utils import to_image_data
import urllib

# from database.database import SQLDatabase
from database import cursor, conn


class Event(Extension):
    def __init__(self, bot):
        l.info("Pre Image and URL")
        self.save_path = None
        self.image_url = None
        logging.info("Extension loaded: Event1")
        logging.info("Extension loaded: Event2")
        self.bot = bot
        logging.info("Extension loaded: Event3")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                sender INT,
                title TEXT NOT NULL,
                description TEXT,
                time TEXT NOT NULL,
                duration INTEGER,
                channel_id INTEGER,
                location TEXT,
                cover_image_link TEXT,
                is_deleted TEXT
            );
        """)
        logging.info("Extension loaded: Event4")
        conn.commit()
        logging.info("Extension loaded: Event5")
    def setup(bot):
        Event(bot)
    
    @listen()
    async def on_startup(self):
        await self.delete_expired_events()

    # def insert_event_image(self, guild_id, event_id, image_id):
    #     query = """
    #     INSERT INTO events (guild_id, id, cover_image_id)
    #     VALUES (?, )
    #     """

    def update_event_image_link(self, image_link, event_id, guild_id):
        """
        Aktuallisiert das Event Bild bzw. dessen Link in der Datenbank 
        """

        query = """
        UPDATE events
        SET cover_image_link = ? 
        WHERE id = ? AND guild_id = ?
        """

        params = (image_link, event_id, guild_id)

        try: 
            conn.execute(query, params)
            conn.commit()

        except Exception as e:
            l.error(f"[EVENTS | DB] Couldn't update Image Link in Database: {e}")

    def get_event_image_link(self, guild_id, event_id, image_link):
        """
        Sucht die Jewahlige Guilde nach guild_id durch ob das Event event_id existiert - Hier wird auch mit nach dem cover_image_link gesucht
        """

        query = """
        SELECT * FROM events WHERE guild_id = ? AND id = ? AND cover_image_link= ?; 
        """

        params = (guild_id, event_id, image_link)
        try:
            conn.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            l.error(f"Couldn't check Events based on Image: {e}")

    @Task.create(IntervalTrigger(minutes=1))
    def delete_expired_events(self):
        try:
            cutoff_time = datetime.now() - timedelta(hours=48)
            l.info(f"EVENT AUTO FLAG DELETE: CUTOFFTIME IS: {cutoff_time}")
            # cutoff_time = datetime.now() - timedelta(hours=30)
            # duration_expired = 
            expired_events = self.get_expired_events(cutoff_time)

            for event in expired_events:
                self.soft_delete(event['id'])
                logging.info(f"Event {event} was flagged as deleted")
                
        except Exception as e:
            logging.error(f"Event deletion error: {e}")

    def soft_delete(self, event_id):
        """
        Setzt den "is_deletet" Status auf 1 was bedeutet, dass das Event zwar in der Datenbank gespeichert bleibt aber dem User und somit der Gilde
        nicht mehr angezeigt wird

        """

        query = """
        UPDATE events
        SET is_deleted = 1
        WHERE id = ?
        """
        try:
            cursor.execute(query, (event_id, ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            l.error(f"Softdeletion Error")
            raise


    def get_expired_events(self, cutoff_time):
        """

        """
        select_query = """
        SELECT * FROM events WHERE time < ? AND is_deleted = 0; 
        """

        params = (cutoff_time, )
        try: 
            cursor.execute(select_query, params)
            return cursor.fetchall()
        except Exception as e:
            l.error(f"Datenbankfehler: {e}")
            raise


    def get_events(self, guild_id):
        """
        Holt alle Events für eine bestimmte Guild.
        """
        select_query = """
        SELECT * FROM events WHERE guild_id = ? AND is_deleted = 0;
        """
        params = (guild_id, )
        try:
            cursor.execute(select_query, params)
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Couldn't get Events based on {guild_id} : {e}")

    # def get_event_id(self, event_id):
    #     """
    #     Sucht unabhänig von der Guilde nach einem Event | Nicht zu empfehlen da alle Events geladen werden müssen
    #     """
    #     select_query = """
    #     SELECT * FROM events WHERE event_id = ?;
    #     """
    #     params = (event_id)
    #     try:
    #         cursor.execute(select_query, params)
    #     except Exception as e:
    #         logging.error(f"Couldn't get Events based on {event_id} : {e}")


    async def delete_event(self, event_id: str):
        """
        Löscht ein Event aus der Datenbank entgültig
        """
        delete_query = """
        DELETE FROM events 
        WHERE id = ?;
        """


        try:
            cursor.execute(delete_query, (event_id,))
            conn.commit()
            logging.info(f"Event {event_id} removed from Database successfully")

        except Exception as e:
            logging.error(f"Error couldn't delete {event_id} because {e}")
        

    async def create_event(self, guild_id: int, event_id: int, sender_id: int, event_title: str, event_description: str, event_time, event_duration, event_channel, location: str, cover_image_link: str, is_deleted: str):
        """
        Fügt ein Event in die Datenbank ein.
        """
        insert_query = """
        INSERT INTO events (guild_id, id, sender, title, description, time, duration, channel_id, location, cover_image_link, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            guild_id, event_id, sender_id, event_title, event_description, event_time, event_duration,
            event_channel.id if event_channel else None, location, cover_image_link, is_deleted
        )
        try:
            cursor.execute(insert_query, params)
            conn.commit()
            logging.info(f"Event {event_id} erfolgreich in der Datenbank gespeichert.")
        except Exception as e:
            logging.error(f"Fehler beim Speichern des Events {event_id}: {e}")

    async def update_event(self, event_id, event_title: Optional[str] = None, event_description: Optional[str] = None, event_time: Optional[str] = None, event_duration: Optional[str] = None, event_channel: Optional[int] = None, location: Optional[str] = None, cover_image_link: Optional[str] = None, is_deleted: Optional[str] = None):
        """
        Updatet das Event nach allen Parametern
        """


        update_query = """
        UPDATE events
        SET title = ?,
            description = ?,
            time = ?,
            duration = ?,
            channel_id = ?,
            location = ?,
            cover_image_link = ?,
            is_deleted = ?
        WHERE id = ?;
        """

        # event_channel_value = str(params[4]) if params[4] is not None else None
        # event_location_value = str(params[5]) if params[5] is not None else None

        # params = (
        #     event_title, event_description, event_time, event_duration, event_channel, location, event_id
        # )

        try:

            event_channel = event_channel.id if isinstance(event_channel, interactions.GuildChannel) else event_channel
            
            params = (
            event_title, event_description, event_time, event_duration, event_channel, location, cover_image_link, is_deleted, event_id
        )
            # cursor.execute(update_query, (*params[:4], event_channel, *params[5:]))
            cursor.execute(update_query, params)
            conn.commit()

        except Exception as e:
            logging.info(f"Error updating Event {event_id} because {e}")

    def get_event_location(self, event, guild):
        if event.get("channel_id") is None:
            return event["location_metadata"]["location"] if event.get("location_metadata") else "Unbekannter Standort"
        else:
            channel = guild.get_channel(int(event["channel_id"]))
            return channel.name if channel else "Unbekannter Kanal" 


    @listen()
    async def on_event_delete(self, event: GuildScheduledEventDelete):
        try:
            event_id = str(event.scheduled_event.id)  # Event-ID als String
            # event_id = event.scheduled_event.id  # Event-ID als String
            # logging.info(f"Event-ID {event_id} wird gelöscht.")
            self.soft_delete(event_id)
            # await self.delete_event(event_id)

        except Exception as e:
            logging.info(f"❌ Fehler beim Verarbeiten von on_event_delete: {e}")




    @listen()
    async def on_event_created(self, event: GuildScheduledEventCreate):
        
        event_id = event.scheduled_event.id
        guild_id = event.scheduled_event.guild.id




        try:
            default_event_image = "assets/images/custom_event.jpg"
            is_deleted = "0"



            # events = self.get_events(guild_id)
            # if not events:
            #     await ctx.send(choices=[])  
            #     return

            # event_suggestions = [
            #     {
            #         "name": f"{event['title']} (ID: {event['id']})",
            #         "value": str(event['id'])  
            #     }
            #     for event in events
            # ]




            # on_ec_default = self.get_event_image_link(guild_id, event_id, default_event_image)
            
            # if on_ec_default:
                

            # on_ec = self.get_events(guild_id)
            # if not on_ec:
            #     # await ctx.send(choices=[])  
            #     # return

            # for event in on_ec:

                






            # TODO: TRY CATCH
            # cover_asset_created = event.scheduled_event.cover
            # await cover_asset_created.save("cover_image_before.jpg")
            # cover_url_created = cover_asset_created.url
            # l.info(f"[EVENT / IMAGE LOGIC] {cover_url_created}")
            # save_path = f"assets/images/download/{event_title.replace(' ', '_')}.jpg"
            # self.download_image(cover_url_created, save_path)
            
            sender_id = (await event.scheduled_event.creator).id
            event_title = event.scheduled_event.name
            event_description = event.scheduled_event.description or "Keine Beschreibung vorhanden"
            event_time = event.scheduled_event.start_time.isoformat()
            event_duration = (event.scheduled_event.end_time - event.scheduled_event.start_time).seconds if event.scheduled_event.end_time else None
            location = getattr(event.scheduled_event, "location", "Kein Standort angegeben")
            event_channel = await event.scheduled_event.fetch_channel() if event.scheduled_event.fetch_channel else None
            event_location = location or (event_channel.name if event_channel else "Kein Standort")

            # Zeitzone und Startzeit umwandeln
            utc_time = datetime.fromisoformat(event_time)
            local_timezone = pytz.timezone("Europe/Berlin")
            start_time = utc_time.astimezone(local_timezone)

            # Header-Bild erstellen
            background = Editor(default_event_image)
            poppins = Font.poppins(size=300, variant="bold")
            poppins_small = Font.poppins(size=200, variant="light")

            # Text auf dem Bild hinzufügen
            background.text((2085, 700), f"Was?: {event_title}", color="white", font=poppins, align="center")
            background.text((2085, 1000), f"Wann?: {start_time.strftime('%d-%m-%Y %H:%M')}", color="white", font=poppins_small, align="center")
            background.text((2085, 1300), f"Wo?: {event_location}", color="white", font=poppins_small, align="center")


            temp_path = "new_custom_event.jpg"
            background.image = background.image.convert("RGB")
            background.image.save(temp_path, "JPEG")
            file = File(temp_path)

            # Event bearbeiten, um das neue Cover-Bild zu setzen
            await event.scheduled_event.edit(cover_image=file)

            await self.create_event(guild_id, event_id, sender_id, event_title, event_description, start_time, event_duration, event_channel, event_location, self.image_url if self.image_url else default_event_image, is_deleted)


            # # Temporäre Datei für das neue Header-Bild speichern
            # temp_path = self.save_path
            # background.image = background.image.convert("RGB")
            # background.image.save(temp_path, "JPEG")
            # file = File(temp_path)

            # # Event bearbeiten, um das neue Cover-Bild zu setzen
            # await event.scheduled_event.edit(cover_image=file)

            # await self.create_event(guild_id, event_id, sender_id, event_title, event_description, start_time, event_duration, event_channel, event_location, is_deleted)
        except Exception as e:
            print(f"Failed to create expected Event: {event_id} ERROR: {e}")

        finally:
            # Temporäre Datei aufräumen
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @listen()
    async def on_event_updated(self, event: GuildScheduledEventUpdate):
        event_id = event.after.id
        guild_id = event.after.guild.id
        logging.info(f"Event Updated: {guild_id}: {event_id}")

        # if (await event.after.creator).bot:
        #     logging.info(f"Ignored update for event '{event.after.name}' (ID: {event.after.id}) in guild '{event.after.guild.id}' because it was triggered by a bot.")
        #     return

    
        try:
            # cover_asset_before = event.before.cover
            
            # await cover_asset_before.save("cover_image_before.jpg")
            # cover_url_before = cover_asset_before.url
            # l.info(f"[EVENT | IMAGE LOGIC | ON_UPDATED]  {cover_url_before}")
            # save_path = f"assets/images/download/{event_title.replace(' ', '_')}.jpg"
            # self.download_image(cover_url_before, save_path)
            # cover_asset_after
            before_channel_id = await event.before.fetch_channel() if event.before.fetch_channel else None
            after_channel_id = await event.after.fetch_channel() if event.before.fetch_channel else None
            

            # test = await event.after.cover.fetch()
            # test.


            
            if all([
                event.before.name == event.after.name,
                event.before.description == event.after.description,
                event.before.start_time == event.after.start_time,
                event.before.end_time == event.after.end_time,
                getattr(event.before, "location", None) == getattr(event.after, "location", None),
                # Add channel/entity type checks
                event.before.entity_type == event.after.entity_type,
                before_channel_id == after_channel_id,
                # event.before.cover == event.after.cover

            ]):
                logging.warning(f"No relevant changes detected, skipping update")
                return
            
            default_event_image = "assets/images/custom_event.jpg"
            is_deleted = "0"
            # Event-Informationen abrufen 
            event_title = event.after.name
            event_time = event.after.start_time.isoformat()
            event_description = event.after.description or "Keine Beschreibung vorhanden"
            event_duration = (event.after.end_time - event.after.start_time).seconds if event.after.end_time else None
            location = getattr(event.after, "location", "Kein Standort angegeben")
            new_location = event.after.location
            event_channel = await event.after.fetch_channel() if event.after.fetch_channel else None
            logging.info(f"Given event channel: {event_channel}")
            event_location = location or (event_channel.name if event_channel else None)


            # time conversion
            utc_time = datetime.fromisoformat(event_time)
            local_timezone = pytz.timezone("Europe/Berlin")
            start_time = utc_time.astimezone(local_timezone)

            # Header-Bild erstellen
            background = Editor(default_event_image)
            poppins = Font.poppins(size=300, variant="bold")
            poppins_small = Font.poppins(size=200, variant="light")

            # Text auf dem Bild hinzufügen
            background.text((2085, 700), f"Was?: {event_title}", color="white", font=poppins, align="center")
            background.text((2085, 1000), f"Wann?: {start_time.strftime('%d-%m-%Y %H:%M')}", color="white",
                            font=poppins_small, align="center")
            background.text((2085, 1300), f"Wo?: {event_location}", color="white", font=poppins_small, align="center")

            # Temporäre Datei für das neue Header-Bild speichern
            temp_path = "assets/images/new_custom_event.jpg"
            background.image = background.image.convert("RGB")
            background.image.save(temp_path, "JPEG")
            file = File(temp_path)

            # Event bearbeiten, um das neue Cover-Bild zu setzen
            # logging.info(f"BEFORE Updated event '{event_title}' ({event_id}) in guild '{guild_id}' with a new cover image.")
            await event.after.edit(cover_image=file)
            logging.info(f"AFTER Updated event '{event_title}' ({event_id}) in guild '{guild_id}' with a new cover image.")
            await self.update_event(event_id, event_title, event_description, start_time, event_duration, event_channel, new_location, self.image_url if self.image_url else default_event_image, is_deleted)

        except Exception as e:
            print(f"Fehler beim Bearbeiten des Events {event_id}: {e}")

        finally:
            # Temporäre Datei aufräumen
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # TEST ALLES ÜBER DIESEM COMMENT GEHT

    @slash_command(
        name="event",
        description="Verwalte geplante Events",
        default_member_permissions=Permissions.MANAGE_EVENTS,
    )
    async def event(self, ctx: SlashContext):
        pass  # Container-Befehl für Subcommands | ist wichtig wegen dem event.subcommand wegen zugehörigkeit


    def download_image(self, url: str, save_path: str):
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            urllib.request.urlretrieve(url, save_path)
        except Exception as e:
            l.error(f"Download failed: {e}")
            raise


    @event.subcommand(
        sub_cmd_name="add",
        sub_cmd_description="Erstellt ein geplantes Event",
    )
    @slash_option(
        name="event_title",
        description="Titel des Events",
        opt_type=OptionType.STRING,
        required=True,
    )
    @slash_option(
        name="event_description",
        description="Beschreibung des Events",
        opt_type=OptionType.STRING,
        required=True,
    )
    @slash_option(
        name="event_time",
        description="Startzeit des Events (Format: DD-MM-YYYY HH:MM)",
        opt_type=OptionType.STRING,
        required=True,
    )
    @slash_option(
        name="event_duration",
        description="Dauer des Events in Minuten",
        opt_type=OptionType.INTEGER,
        required=True,
    )
    @slash_option(
        name="voice_channel",
        description="Voice-Channel für das Event (nur bei internem Standort)",
        opt_type=OptionType.CHANNEL,
        channel_types=[ChannelType.GUILD_VOICE],
        required=False,
    )
    @slash_option(
        name="external_location",
        description="Externer Link oder Ort des Events (nur bei externem Standort)",
        opt_type=OptionType.STRING,
        required=False,
    )
    @slash_option(
        name="cover_image",
        description="Füge hier den link ein zu einem Bild welches du Downloaden möchtest (jpg only!)",
        opt_type=OptionType.STRING,
        required=False,
    )
    async def add_event(
        self,
        ctx: SlashContext,
        event_title: str,
        event_description: str,
        event_time: str,
        event_duration: int,
        # location_type: str,
        voice_channel= None,
        external_location=None,
        cover_image: str = None,
    ):
        try:
            await ctx.defer(ephemeral=True)
            self.save_path = None
            self.image_url = None

            local_timezone = pytz.timezone("Europe/Berlin")
            start_time = datetime.strptime(event_time, "%d-%m-%Y %H:%M")
            start_time = local_timezone.localize(start_time)
            start_time = start_time.astimezone(pytz.UTC)
            end_time = start_time + timedelta(minutes=event_duration)

            guild = ctx.guild
            if not guild:
                await ctx.send("Events are guilds only - Please execute in guild with given permissions")
                return
            
            # Fix 2: Dynamischer Dateipfad mit Event-Titel
            if cover_image:
                self.image_url = cover_image if cover_image else "assets/images/custom_event.jpg"
                self.save_path = f"assets/images/download/{event_title.replace(' ', '_')}.jpg"
                self.download_image(cover_image, self.save_path)  # Fix 3: Korrekter Methodenaufruf
                l.info(f"Cover image saved to {self.save_path}")
            


            if voice_channel and external_location:
                await ctx.send("Combined optioned are not allowed")
                return
            elif voice_channel:
                channel = voice_channel.id
                entity_type = 2

                await guild.create_scheduled_event(
                    name = event_title,
                    event_type = entity_type,
                    start_time = start_time,
                    end_time = end_time,
                    description = event_description,
                    channel_id = channel,
                    privacy_level = 2,
                    cover_image= self.save_path

                )
                await ctx.send(f"Event {event_title} was created and stored in SQL:Database")
            else:
                entity_type = 3
                channel = None
                await guild.create_scheduled_event(
                    name = event_title,
                    event_type = entity_type,
                    start_time = start_time,
                    end_time = end_time,
                    description = event_description,
                    external_location= external_location, 
                    privacy_level = 2,
                    cover_image= self.save_path  
                )
                await ctx.send(f"Event {event_title} was created and stored in SQL:Database")

        except Exception as e:
            await ctx.send(f"Event creation error: {e}")
            logging.error(f"EVENT CREATION ERROR: {e}")


# code functional above 


    
    @event.subcommand(
        sub_cmd_name="remove",
        sub_cmd_description="Entfernt ein bestehendes Event",
    )
    @slash_option(
        name="event_id",
        description="ID des Events, das entfernt werden soll",
        opt_type=OptionType.STRING,
        required=True,
        autocomplete=True,
    )
    async def remove_event(self, ctx: SlashContext, event_id: str):
        ctx.defer(ephemeral=True)
        try:
            # Zugriff auf die Guild
            guild = ctx.guild
            if not guild:
                await ctx.send("❌ Fehler: Gilde konnte nicht abgerufen werden.")
                return
    
            # Versuche, das Event anhand der ID zu holen
            event = await guild.fetch_scheduled_event(event_id, force=True)

            if not event:
                await ctx.send(f"❌ Event mit ID `{event_id}` wurde nicht gefunden.")
                return
    
            # Lösche das Event auf Discord
            await event.delete()
    
            # Entferne das Event aus der internen Datenstruktur
            if self.soft_delete(event_id):
                await ctx.send(f"{event_id} was successfully deleted")
            # if self.soft_delete(event_id):
            #     await ctx.send(f"🚮 Event **{event.name}** mit **{event_id}** wurde erfolgreich entfernt!")
            # else:
            #     await ctx.send(f"❌ Event **{event_id}** konnte nicht aus der Datenbank entfernt werden.")
    
        except Exception as e:
            await ctx.send(f"❌ Fehler beim Entfernen des Events: {e}")







    @remove_event.autocomplete("event_id")
    async def autocomplete_event_id(self, ctx: AutocompleteContext):
        try:
            guild = ctx.guild
            guild_id = ctx.guild_id



            if not guild:
                await ctx.send(choices=[]) 
                return
        
            events = self.get_events(guild_id)
            if not events:
                await ctx.send(choices=[])  
                return

            event_suggestions = [
                {
                    "name": f"{event['title']} (ID: {event['id']})",
                    "value": str(event['id'])  
                }
                for event in events
            ]
            
            await ctx.send(choices=event_suggestions[:25])  # Verwende ctx.send für die Antwort
        except Exception as e:
            print(f"Fehler beim Autocomplete: {e}")
            await ctx.send(choices=[])  # Stelle sicher, dass wir eine leere Antwort senden, wenn ein Fehler auftritt
    
    #code functional

    @event.subcommand(
        sub_cmd_name="list",
        sub_cmd_description="Listet alle geplanten Events auf",
    )
    @slash_option(
        name="all_events",
        description="Liste alle Events auf",
        opt_type=OptionType.BOOLEAN,
        required=False,
    )
    async def list_event(self, ctx: SlashContext, all_events: bool = False):
        await ctx.defer(ephemeral=True)
        guild = ctx.guild

        events = await Guild.list_scheduled_events(guild)

        event_list = []
        for event in events:
            event_info = f"**Event-ID:** '{event.id}' | **NAME:** {event.name}"
            event_list.append(event_info)

        if event_list:
            await ctx.send("\n".join(event_list))
        else:
            await ctx.send("No Events :(")

# code functional above 

    @event.subcommand(
        sub_cmd_name="update",
        sub_cmd_description="Aktualisiert ein bestehendes Event",
    )
    @slash_option(
        name="event_id",
        description="ID des Events, das aktualisiert werden soll",
        opt_type=OptionType.STRING,
        required=True,
        autocomplete=True,
    )
    @slash_option(
        name="event_title",
        description="Neuer Titel des Events",
        opt_type=OptionType.STRING,
        required=False,
    )
    @slash_option(
        name="event_description",
        description="Neue Beschreibung des Events",
        opt_type=OptionType.STRING,
        required=False,
    )
    @slash_option(
        name="event_time",
        description="Neue Startzeit des Events (Format: DD-MM-YYYY HH:MM)",
        opt_type=OptionType.STRING,
        required=False,
    )
    @slash_option(
        name="event_duration",
        description="Neue Dauer des Events in Minuten",
        opt_type=OptionType.INTEGER,
        required=False,
    )
    # @slash_option(
    #     name="end_time",
    #     description="Neue Endzeit für das geplannte Event",

    #     required=False,

    # )
    @slash_option(
        name="voice_channel",
        description="Neuer Voice-Channel für das Event (nur bei internem Standort)",
        opt_type=OptionType.CHANNEL,
        channel_types=[ChannelType.GUILD_VOICE],
        required=False,
    )
    @slash_option(
        name="external_location",
        description="Neuer externer Link oder Ort des Events (nur bei externem Standort)",
        opt_type=OptionType.STRING,
        required=False,
    )
    @slash_option(
        name="cover_image",
        description="Neues Bild für das Event (URL oder Datei)",
        opt_type=OptionType.STRING,
        required=False,
    )
    async def updateEvent(self, ctx: SlashContext, event_id: str, event_title=None, event_description=None,
                        event_time=None, event_duration=None, voice_channel=None,
                        external_location=None, cover_image=None):
        try:

            guild = ctx.guild


            event = await guild.fetch_scheduled_event(event_id)
            if event_time:
                local_timezone = pytz.timezone("Europe/Berlin")
                start_time = datetime.strptime(event_time, "%d-%m-%Y %H:%M")
                start_time = local_timezone.localize(start_time)
                start_time = start_time.astimezone(pytz.UTC)
                end_time = start_time + timedelta(minutes=event_duration)
            else:
                start_time = None
                end_time = None
            

            if not event:
                return
            if not guild:
                return


            update_kwargs = {}

            if event_title:
                update_kwargs['name'] = event_title
                self.update_event(event_id=event, event_title=event_title)
                # l.info(f"await se.edit(self, name=event_title)")

            if event_description:
                update_kwargs['description'] = event_description
            
            if event_time:
                update_kwargs['start_time'] = event_time

            if voice_channel and external_location:
                await ctx.send("Cannot specify both voice channel and external location.")
                return
            elif voice_channel:
                channel = voice_channel.id
                entity_type = 2
                await event.edit(channel_id=channel, event_type=entity_type)
            elif external_location:
                entity_type = 3
                channel = None
                await event.edit(event_type=entity_type, external_location=external_location, start_time=start_time, end_time=end_time)
                ctx.send("External location updated successfully")

            if update_kwargs:
                await event.edit(**update_kwargs)
                await ctx.send(f"Update für {update_kwargs} komplett")
            else:
                await ctx.send("?- ELSE STATMENT SOMEHOW TRIGGERD")


        except Exception as e:
            await ctx.send(f"[EVENT | UPDATE | SLASHCOMMAND] {e}")
            l.error(f"[EVENT | UPDATE | SLASHCOMMAND] Unable to update Event: {e}")
            

    @updateEvent.autocomplete("event_id")
    async def autocomplete_event_id(self, ctx: AutocompleteContext):
        try:
            guild = ctx.guild
            # guild_id = ctx.guild_id



            if not guild:
                await ctx.send(choices=[]) 
                return
        
            events = self.get_events(guild.id)
            if not events:
                await ctx.send(choices=[])  
                return

            event_suggestions = [
                {
                    "name": f"{event['title']} (ID: {event['id']})",
                    "value": str(event['id'])  
                }
                for event in events
            ]
            
            await ctx.send(choices=event_suggestions[:25])  # Verwende ctx.send für die Antwort
        except Exception as e:
            print(f"Fehler beim Autocomplete: {e}")
            await ctx.send(choices=[])  # Stelle sicher, dass wir eine leere Antwort senden, wenn ein Fehler auftritt
    
    # ===================================================================================
    # @update_event.autocomplete("event_title")
    # async def autocomplete_event_title(self, ctx: AutocompleteContext):
    #     self.reload_events()
    #     try:
    #         guild_id = ctx.guild_id
    #         if not guild_id:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         events = self.validate_guild_events(guild_id)
    #         if not events:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         event_suggestions = [
    #             {
    #                 "name": f"Was: {event['title']}",
    #                 "value": event["title"]
    #             }
    #             for event in events
    #         ]
    #         await ctx.send(choices=event_suggestions[:25])
    #     except Exception as e:
    #         print(f"Fehler beim Autocomplete: {e}")
    #         await ctx.send(choices=[])
    # 
    # 
    # @update_event.autocomplete("event_description")
    # async def autocomplete_event_description(self, ctx: AutocompleteContext):
    #     self.reload_events()
    #     try:
    #         guild_id = ctx.guild_id
    #         if not guild_id:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         events = self.validate_guild_events(guild_id)
    #         if not events:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         event_suggestions = [
    #             {
    #                 "name": f"Was: {event['description']}",
    #                 "value": event["description"]
    #             }
    #             for event in events
    #         ]
    #         await ctx.send(choices=event_suggestions[:25])
    #     except Exception as e:
    #         print(f"Fehler beim Autocomplete: {e}")
    #         await ctx.send(choices=[])
    # 
    # 
    # @update_event.autocomplete("event_time")
    # async def autocomplete_event_time(self, ctx: AutocompleteContext):
    #     self.reload_events()
    #     try:
    #         guild_id = ctx.guild_id
    #         if not guild_id:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         events = self.validate_guild_events(guild_id)
    #         if not events:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         event_suggestions = [
    #             {
    #                 "name": f"Was: {event['time']}",
    #                 "value": event["time"]
    #             }
    #             for event in events
    #         ]
    #         await ctx.send(choices=event_suggestions[:25])
    #     except Exception as e:
    #         print(f"Fehler beim Autocomplete: {e}")
    #         await ctx.send(choices=[])
    # 
    # @update_event.autocomplete("event_duration")
    # async def autocomplete_event_duration(self, ctx: AutocompleteContext):
    #     self.reload_events()
    #     try:
    #         guild_id = ctx.guild_id
    #         if not guild_id:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         events = self.validate_guild_events(guild_id)
    #         if not events:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         event_suggestions = [
    #             {
    #                 "name": f"Was: {event['duration']}",
    #                 "value": event["duration"]
    #             }
    #             for event in events
    #         ]
    #         await ctx.send(choices=event_suggestions[:25])
    #     except Exception as e:
    #         print(f"Fehler beim Autocomplete: {e}")
    #         await ctx.send(choices=[])
    # 
    # @update_event.autocomplete("external_location")
    # async def autocomplete_event_location(self, ctx: AutocompleteContext):
    #     self.reload_events()
    #     try:
    #         guild_id = ctx.guild_id
    #         if not guild_id:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         events = self.validate_guild_events(guild_id)
    #         if not events:
    #             await ctx.send(choices=[])
    #             return
    # 
    #         event_suggestions = [
    #             {
    #                 "name": event["location_metadata"]["location"],
    #                 "value": event["location_metadata"]["location"]
    #             }
    #             for event in events
    #             if event.get("location_metadata") and "location" in event["location_metadata"]
    #         ]
    #         await ctx.send(choices=event_suggestions[:25])
    #     except Exception as e:
    #         print(f"Fehler beim Autocomplete: {e}")
    #         await ctx.send(choices=[])




# import json
# import os
# from datetime import datetime, timedelta
# from http.client import responses
# from extensions.functions import Function
# import aiohttp
# import pytz
# from PIL import ImageFont, ImageDraw, Image
# from crescent import event
# from easy_pil import Editor, Font
# from interactions import (
#     Extension,
#     SlashContext,
#     slash_command,
#     Permissions,
#     slash_option,
#     OptionType,
#     ChannelType, AutocompleteContext, ScheduledEventType, File, listen, ScheduledEvent, IntervalTrigger,
# )
# from interactions.api.events import GuildScheduledEventCreate, GuildScheduledEventUpdate, GuildScheduledEventDelete
# from interactions.client.utils import to_image_data
# from interactions.models.internal.tasks import task


# class Event(Extension):
#     def __init__(self, bot):
#         self.bot = bot
#         self.events_file = "database/events.json"  # Datei für die Speicherung
#         self.events = self.load_events()  # Lade Events beim Start
#         print("Extension geladen: Event")


#     def validate_guild_events(self, guild_id):
#         try:
#             self.reload_events()

#             if not guild_id:
#                 return []
#             return [event for event in self.events if event.get("guild_id") == guild_id]
#         except Exception as e:
#             print(f"Fehler bei der Eingabe: {e}")
#             return []

#     def get_event_location(self, event, guild):
#         if event.get("channel_id") is None:
#             return  event["location_metadata"]["location"] if event.get("location_metadata") else "Unbekannter Standort"
#         else:
#             channel = guild.get_channel(int(event["channel_id"]))
#             return channel.name if channel else "Unbekannter Kanal"


#     def reload_events(self):
#         """Lädt die Events erneut aus der JSON-Datei."""
#         try:
#             with open('database/events.json', 'r', encoding='utf-8') as file:
#                 self.events = json.load(file)
#         except Exception as e:
#             print(f"❌ Fehler beim Laden der Events: {e}")
#             self.events = []

#     def update_events(self, event_id, updates):
#         """Aktualisiert ein bestehendes Event in der lokalen Datenbank."""
#         for event in self.events:
#             if event["id"] == event_id:
#                 event.update(updates)
#                 break
#         self.save_events()
#         self.reload_events()  # Aktualisiere die Event-Liste nach dem Speichern

#     def load_events(self):
#         try:
#             with open(self.events_file, "r") as file:
#                 return json.load(file)  # Lade die Events aus der Datei
#         except FileNotFoundError:
#             return []  # Falls Datei nicht existiert, starte mit leerer Liste
#         except json.JSONDecodeError:
#             print("❌ Fehler beim Laden der JSON-Datei. Starte mit leerer Liste.")
#             return []

#     def save_events(self):
#         try:
#             with open(self.events_file, "w", encoding="utf-8") as file:
#                 json.dump(self.events, file, indent=4, ensure_ascii=False)  # Speichere die Events in die Datei
#             print(f"✅ Events erfolgreich in {self.events_file} gespeichert.")
#         except Exception as e:
#             print(f"❌ Fehler beim Speichern der Events: {e}")

#     @listen()
#     async def on_event_delete(self, event: GuildScheduledEventDelete):
#         try:
#             # Find the event in self.events using its ID
#             event_id = event.scheduled_event.id
#             event_to_delete = next((e for e in self.events if e["id"] == event_id), None)

#             if event_to_delete:
#                 # Remove the event from self.events
#                 self.events.remove(event_to_delete)
#                 self.save_events()  # Persist changes to the database
#                 print(f"Event {event_id} wurde erfolgreich aus der Datenbank gelöscht.")
#             else:
#                 print(f"Event {event_id} wurde nicht in der Datenbank gefunden.")

#         except Exception as e:
#             print(f"Fehler beim Löschen des Events {event_id}: {e}")

#     @listen()
#     async def on_event_created(self, event: GuildScheduledEventCreate):
#         event_id = event.scheduled_event.id
#         guild_id = event.scheduled_event.guild.id

#         try:
#             # Event-Informationen abrufen
#             event_title = event.scheduled_event.name
#             event_description = event.scheduled_event.description or "Keine Beschreibung vorhanden"
#             event_time = event.scheduled_event.start_time.isoformat()
#             event_duration = (
#                         event.scheduled_event.end_time - event.scheduled_event.start_time).seconds if event.scheduled_event.end_time else None
#             location = getattr(event.scheduled_event, "location", "Kein Standort angegeben")
#             event_channel = await event.scheduled_event.fetch_channel() if event.scheduled_event.fetch_channel else None
#             event_location = location or (event_channel.name if event_channel else "Kein Standort")

#             # Zeitzone und Startzeit umwandeln
#             utc_time = datetime.fromisoformat(event_time)
#             local_timezone = pytz.timezone("Europe/Berlin")
#             start_time = utc_time.astimezone(local_timezone)

#             # Header-Bild erstellen
#             background = Editor("assets/images/custom_event.jpg")
#             poppins = Font.poppins(size=300, variant="bold")
#             poppins_small = Font.poppins(size=200, variant="light")

#             # Text auf dem Bild hinzufügen
#             background.text((2085, 700), f"Was?: {event_title}", color="white", font=poppins, align="center")
#             background.text((2085, 1000), f"Wann?: {start_time.strftime('%d-%m-%Y %H:%M')}", color="white",
#                             font=poppins_small, align="center")
#             background.text((2085, 1300), f"Wo?: {event_location}", color="white", font=poppins_small, align="center")

#             # Temporäre Datei für das neue Header-Bild speichern
#             temp_path = "new_custom_event.jpg"
#             background.image = background.image.convert("RGB")
#             background.image.save(temp_path, "JPEG")
#             file = File(temp_path)

#             # Event bearbeiten, um das neue Cover-Bild zu setzen
#             await event.scheduled_event.edit(cover_image=file)

#             # Event-Daten in self.events speichern
#             self.events.append({
#                 "guild_id": event.scheduled_event.guild.id,
#                 "id": event_id,
#                 "title": event_title,
#                 "description": event_description,
#                 "time": event_time,
#                 "duration": event_duration,
#                 "channel_id": event_channel.id if event_channel else None,
#                 "location_type": "channel" if event_channel else "custom",
#                 "location_metadata": location,
#                 "cover_image": temp_path,
#             })
#             self.save_events()  # Speichert die Events persistiert, wenn save_events korrekt implementiert ist
#             self.reload_events()  # Lädt Events erneut, falls erforderlich

#         except Exception as e:
#             print(f"Fehler beim Bearbeiten des Events {event_id}: {e}")

#         finally:
#             # Temporäre Datei aufräumen
#             if os.path.exists(temp_path):
#                 os.remove(temp_path)

#     @listen()
#     async def on_event_updated(self, event: GuildScheduledEventUpdate):
#         event_id = event.after.id

#         try:
#             # Event-Informationen abrufen
#             event_title = event.after.name
#             event_time = event.after.start_time.isoformat()
#             location = getattr(event.after, "location", "Kein Standort angegeben")
#             event_channel = await event.after.fetch_channel() if event.after.fetch_channel else None
#             event_location = location or (event_channel.name if event_channel else None)

#             utc_time = datetime.fromisoformat(event_time)
#             local_timezone = pytz.timezone("Europe/Berlin")
#             start_time = utc_time.astimezone(local_timezone)

#             # Header-Bild erstellen
#             background = Editor("assets/images/custom_event.jpg")
#             poppins = Font.poppins(size=300, variant="bold")
#             poppins_small = Font.poppins(size=200, variant="light")

#             # Text auf dem Bild hinzufügen
#             background.text((2085, 700), f"Was?: {event_title}", color="white", font=poppins, align="center")
#             background.text((2085, 1000), f"Wann?: {start_time.strftime('%d-%m-%Y %H:%M')}", color="white",
#                             font=poppins_small, align="center")
#             background.text((2085, 1300), f"Wo?: {event_location}", color="white", font=poppins_small, align="center")

#             # Temporäre Datei für das neue Header-Bild speichern
#             temp_path = "new_custom_event.jpg"
#             background.image = background.image.convert("RGB")
#             background.image.save(temp_path, "JPEG")
#             file = File(temp_path)

#             # Event bearbeiten, um das neue Cover-Bild zu setzen
#             await event.after.edit(cover_image=file)

#         except Exception as e:
#             print(f"Fehler beim Bearbeiten des Events {event_id}: {e}")

#         finally:
#             # Temporäre Datei aufräumen
#             if os.path.exists(temp_path):
#                 os.remove(temp_path)

#     @slash_command(
#         name="event",
#         description="Verwalte geplante Events",
#         default_member_permissions=Permissions.MANAGE_EVENTS,
#     )
#     async def event(self, ctx: SlashContext):
#         pass  # Container-Befehl für Subcommands

#     @event.subcommand(
#         sub_cmd_name="add",
#         sub_cmd_description="Erstellt ein geplantes Event",
#     )
#     @slash_option(
#         name="event_title",
#         description="Titel des Events",
#         opt_type=OptionType.STRING,
#         required=True,
#     )
#     @slash_option(
#         name="event_description",
#         description="Beschreibung des Events",
#         opt_type=OptionType.STRING,
#         required=True,
#     )
#     @slash_option(
#         name="event_time",
#         description="Startzeit des Events (Format: DD-MM-YYYY HH:MM)",
#         opt_type=OptionType.STRING,
#         required=True,
#     )
#     @slash_option(
#         name="event_duration",
#         description="Dauer des Events in Minuten",
#         opt_type=OptionType.INTEGER,
#         required=True,
#     )
#     @slash_option(
#         name="location_type",
#         description="Typ des Standorts (Intern oder Extern)",
#         opt_type=OptionType.STRING,
#         choices=[
#             {"name": "Intern (Voice-Channel)", "value": "internal"},
#             {"name": "Extern (Link)", "value": "external"},
#         ],
#         required=True,
#     )
#     @slash_option(
#         name="voice_channel",
#         description="Voice-Channel für das Event (nur bei internem Standort)",
#         opt_type=OptionType.CHANNEL,
#         channel_types=[ChannelType.GUILD_VOICE],
#         required=False,
#     )
#     @slash_option(
#         name="external_location",
#         description="Externer Link oder Ort des Events (nur bei externem Standort)",
#         opt_type=OptionType.STRING,
#         required=False,
#     )
#     async def add_event(
#         self,
#         ctx: SlashContext,
#         event_title: str,
#         event_description: str,
#         event_time: str,
#         event_duration: int,
#         location_type: str,
#         voice_channel=None,
#         external_location=None,
#         cover_image="assets/images/custom_event.jpg"
#     ):
#         try:
#             await ctx.defer(ephemeral=True)

#             # Lokale Zeitzone definieren (z. B. Europe/Berlin)
#             local_timezone = pytz.timezone("Europe/Berlin")

#             # Konvertiere event_time zu einem datetime-Objekt im Format DD-MM-YYYY HH:MM
#             start_time = datetime.strptime(event_time, "%d-%m-%Y %H:%M")
#             start_time = local_timezone.localize(start_time)  # Lokale Zeitzone hinzufügen
#             start_time = start_time.astimezone(pytz.UTC)  # In UTC konvertieren

#             # Berechne die Endzeit
#             end_time = start_time + timedelta(minutes=event_duration)
#             # Zugriff auf die Guild
#             guild = ctx.guild
#             if not guild:
#                 await ctx.send("❌ Fehler: Gilde konnte nicht abgerufen werden.")
#                 return

#             # Standortdaten basierend auf Auswahl
#             if location_type == "internal":
#                 if not voice_channel:
#                     await ctx.send("❌ Bitte wähle einen Voice-Channel für ein internes Event.")
#                     return
#                 entity_type = 2  # VOICE
#                 location_metadata = None
#                 location_channel_id = voice_channel.id
#             elif location_type == "external":
#                 if not external_location:
#                     await ctx.send("❌ Bitte gib einen externen Link für ein externes Event an.")
#                     return
#                 entity_type = 3  # EXTERNAL
#                 location_metadata = {"location": external_location}
#                 location_channel_id = None
#             else:
#                 await ctx.send("❌ Ungültiger Standorttyp ausgewählt.")
#                 return

#             # API-Endpunkt und Header
#             url = f"https://discord.com/api/v10/guilds/{guild.id}/scheduled-events"
#             headers = {
#                 "Authorization": f"Bot {self.bot.http.token}",
#                 "Content-Type": "application/json",
#             }
#             # Daten für das Event
#             payload = {
#                 "name": event_title,
#                 "description": event_description,
#                 "scheduled_start_time": start_time.isoformat(),
#                 "scheduled_end_time": end_time.isoformat(),
#                 "entity_type": entity_type,
#                 "privacy_level": 2,  # GUILD_ONLY
#                 "image": to_image_data(cover_image) if cover_image else None,
#             }

#             # Zusätzliche Metadaten basierend auf dem Standorttyp
#             if entity_type == 3:  # EXTERNAL
#                 payload["entity_metadata"] = location_metadata
#             elif entity_type == 2:  # VOICE
#                 payload["channel_id"] = location_channel_id

#             # HTTP-Anfrage mit aiohttp
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(url, headers=headers, json=payload) as response:
#                     response_data = await response.json()

#                     if not response.status in {200, 201} and "id" in response_data:
#                         await ctx.send(
#                             f"❌ Fehler beim Erstellen des Events: {response.status} | {response_data}"
#                         )
#                         return # Event Nicht Erstellt


#                     self.events.append({"guild_id": guild.id,
#                                         "id": response_data["id"],
#                                         "title": event_title,
#                                         "description": event_description,
#                                         "time": event_time,
#                                         "duration": event_duration,
#                                         "channel_id": location_channel_id,
#                                         "location_type": location_type,
#                                         "location_metadata": location_metadata,
#                                         "cover_image": cover_image,
#                                         })

#                     #Function.save_events()
#                     self.save_events()  # Speichere die Liste nach der Änderung
#                     await ctx.send(
#                         f"🎉 Event '{event_title}' wurde erfolgreich erstellt für {start_time.astimezone(local_timezone).strftime('%d-%m-%Y %H:%M')} (lokale Zeit)!"
#                     )


#         except Exception as e:
#             await ctx.send(f"❌ Fehler beim Erstellen des Events: {e}")

#     @event.subcommand(
#         sub_cmd_name="remove",
#         sub_cmd_description="Entfernt ein bestehendes Event",
#     )
#     @slash_option(
#         name="event_id",
#         description="ID des Events, das entfernt werden soll",
#         opt_type=OptionType.STRING,
#         required=True,
#         autocomplete=True,
#     )
#     async def remove_event(self, ctx: SlashContext, event_id: str):
#         try:
#             # Zugriff auf die Guild
#             guild = ctx.guild
#             if not guild:
#                 await ctx.send("❌ Fehler: Gilde konnte nicht abgerufen werden.")
#                 return

#             # Versuche, das Event anhand der ID zu holen
#             event = await guild.fetch_scheduled_event(event_id, force=True)
#             if not event:
#                 await ctx.send(f"❌ Event mit ID `{event_id}` wurde nicht gefunden.")
#                 return

#             # Lösche das Event
#             await event.delete()
#             self.events = [e for e in self.events if e["id"] != event_id]  # Entferne aus der internen Liste
#             self.save_events()  # Speichere die Liste nach der Änderung

#             await ctx.send(f"🚮 Event **{event.name}** mit **{event_id}** wurde erfolgreich entfernt!")
#         except Exception as e:
#             await ctx.send(f"❌ Fehler beim Entfernen des Events: {e}")

#     @remove_event.autocomplete("event_id")
#     async def autocomplete_event_id(self, ctx: AutocompleteContext):
#         self.reload_events()
#         try:
#             guild_id = ctx.guild_id
#             if not guild_id:
#                 await ctx.send(choices=[])  # Wenn keine Guild-ID vorhanden ist, sende leere Vorschläge zurück
#                 return

#             # Hole alle Events für die Guild
#             events = self.validate_guild_events(guild_id)
#             if not events:
#                 await ctx.send(choices=[])  # Wenn keine Events vorhanden sind, sende leere Vorschläge zurück
#                 return


#             # Erstelle eine Liste von Event-Suggestions
#             event_suggestions = [
#                 {
#                     "name": f"Was: {event['title']} | Wann: {event['time']} | Wo: {self.get_event_location(event, self.bot.get_guild(guild_id))} | ID: {event['id']}",
#                     "value": event["id"]  # Der Wert, der bei der Auswahl zurückgegeben wird
#                 }
#                 for event in events
#             ]

#             # Gebe maximal 25 Vorschläge zurück
#             await ctx.send(choices=event_suggestions[:25])  # Verwende ctx.send für die Antwort
#         except Exception as e:
#             print(f"Fehler beim Autocomplete: {e}")
#             await ctx.send(choices=[])  # Stelle sicher, dass wir eine leere Antwort senden, wenn ein Fehler auftritt

#     @event.subcommand(
#         sub_cmd_name="list",
#         sub_cmd_description="Listet alle geplanten Events auf",
#     )
#     @slash_option(
#         name="all_events",
#         description="Liste alle Events auf",
#         opt_type=OptionType.BOOLEAN,
#         required=False,
#     )
#     async def list_event(self, ctx: SlashContext, all_events: bool = False):
#         try:
#             await ctx.defer(ephemeral=True)
#             guild = ctx.guild
#             if not guild:
#                 await ctx.send("❌ Fehler: Gilde konnte nicht abgerufen werden.")
#                 return

#             # Discord-API-Endpunkt für geplante Events
#             url = f"https://discord.com/api/v10/guilds/{guild.id}/scheduled-events"
#             headers = {
#                 "Authorization": f"Bot {self.bot.http.token}",
#             }

#             # Events von der API abrufen
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(url, headers=headers) as response:
#                     if response.status != 200:
#                         await ctx.send(
#                             f"❌ Fehler beim Abrufen der Events: {response.status} {responses[response.status]}"
#                         )
#                         return
#                     events = await response.json()

#             if not events:
#                 await ctx.send("❌ Es gibt keine geplanten Events.")
#                 return

#             # Filtern der Events
#             events_to_show = events if all_events else events[:5]

#             # Nachrichten-String erstellen
#             event_list = "\n".join(
#                 f"**{event['name']}** - **{event['id']}** - {event['scheduled_start_time']}"
#                 for event in events_to_show
#             )
#             total_events = len(events)
#             await ctx.send(
#                 f"🗓️ **Geplante Events ({'alle' if all_events else 'Top 5'})**:\n\n{event_list}\n\nInsgesamt: {total_events} Events."
#             )
#         except Exception as e:
#             await ctx.send(f"❌ Fehler beim Auflisten der Events: {e}")

#     @event.subcommand(
#         sub_cmd_name="update",
#         sub_cmd_description="Aktualisiert ein bestehendes Event",
#     )
#     @slash_option(
#         name="event_id",
#         description="ID des Events, das aktualisiert werden soll",
#         opt_type=OptionType.STRING,
#         required=True,
#         autocomplete=True,
#     )
#     @slash_option(
#         name="event_title",
#         description="Neuer Titel des Events",
#         opt_type=OptionType.STRING,
#         required=False,
#     )
#     @slash_option(
#         name="event_description",
#         description="Neue Beschreibung des Events",
#         opt_type=OptionType.STRING,
#         required=False,
#     )
#     @slash_option(
#         name="event_time",
#         description="Neue Startzeit des Events (Format: DD-MM-YYYY HH:MM)",
#         opt_type=OptionType.STRING,
#         required=False,
#     )
#     @slash_option(
#         name="event_duration",
#         description="Neue Dauer des Events in Minuten",
#         opt_type=OptionType.INTEGER,
#         required=False,
#     )
#     @slash_option(
#         name="location_type",
#         description="Neuer Typ des Standorts (Intern oder Extern)",
#         opt_type=OptionType.STRING,
#         choices=[
#             {"name": "Intern (Voice-Channel)", "value": "internal"},
#             {"name": "Extern (Link)", "value": "external"},
#         ],
#         required=False,
#     )
#     @slash_option(
#         name="voice_channel",
#         description="Neuer Voice-Channel für das Event (nur bei internem Standort)",
#         opt_type=OptionType.CHANNEL,
#         channel_types=[ChannelType.GUILD_VOICE],
#         required=False,
#     )
#     @slash_option(
#         name="external_location",
#         description="Neuer externer Link oder Ort des Events (nur bei externem Standort)",
#         opt_type=OptionType.STRING,
#         required=False,
#     )
#     @slash_option(
#         name="cover_image",
#         description="Neues Bild für das Event (URL oder Datei)",
#         opt_type=OptionType.STRING,
#         required=False,
#     )
#     async def update_event(self, ctx: SlashContext, event_id: str, event_title=None, event_description=None,
#                            event_time=None, event_duration=None, location_type=None, voice_channel=None,
#                            external_location=None, cover_image=None):
#         try:
#             await ctx.defer(ephemeral=True)

#             # Zugriff auf die Guild
#             guild = ctx.guild
#             if not guild:
#                 await ctx.send("❌ Fehler: Gilde konnte nicht abgerufen werden.")
#                 return

#             # Event holen
#             event = await guild.fetch_scheduled_event(event_id, force=True)
#             if not event:
#                 await ctx.send(f"❌ Event mit ID `{event_id}` wurde nicht gefunden.")
#                 return

#             # JSON-Dateipfad sicherstellen
#             file_path = 'database/events.json'
#             if not os.path.exists(file_path):
#                 os.makedirs(os.path.dirname(file_path), exist_ok=True)
#                 with open(file_path, 'w', encoding='utf-8') as file:
#                     json.dump([], file)

#             # Lade die Event-Datenbank
#             with open(file_path, 'r+', encoding='utf-8') as file:
#                 event_data = json.load(file)

#             # Suche das Event in der lokalen Datenbank
#             db_event = next((e for e in event_data if e["id"] == event_id), None)
#             if not db_event:
#                 await ctx.send(f"❌ Event mit ID `{event_id}` wurde nicht in der lokalen Datenbank gefunden.")
#                 return

#             # Änderungen vorbereiten
#             update_data = {}
#             new_data = {}

#             # Titel und Beschreibung
#             if event_title and db_event.get("title") != event_title:
#                 update_data["name"] = event_title
#                 new_data["title"] = {"old": db_event.get("title"), "new": event_title}
#                 db_event["title"] = event_title
#             if event_description and db_event.get("description") != event_description:
#                 update_data["description"] = event_description
#                 new_data["description"] = {"old": db_event.get("description"), "new": event_description}
#                 db_event["description"] = event_description

#             # Zeit und Dauer
#             start_time = None
#             if event_time:
#                 try:
#                     start_time = datetime.strptime(event_time, "%d-%m-%Y %H:%M").replace(tzinfo=pytz.UTC)
#                     update_data["start_time"] = start_time
#                     new_data["time"] = {"old": db_event.get("time"), "new": event_time}
#                     db_event["time"] = event_time
#                 except ValueError:
#                     await ctx.send("❌ Fehler: Ungültiges Zeitformat. Bitte nutze das Format 'DD-MM-YYYY HH:MM'.")
#                     return

#             if event_duration:
#                 try:
#                     duration_minutes = int(event_duration)
#                     if not start_time:
#                         start_time = datetime.strptime(db_event.get("time"), "%d-%m-%Y %H:%M").replace(tzinfo=pytz.UTC)
#                     end_time = start_time + timedelta(minutes=duration_minutes)
#                     update_data["end_time"] = end_time
#                     new_data["duration"] = {"old": db_event.get("duration"), "new": f"{event_duration} Minuten"}
#                     db_event["duration"] = event_duration
#                     db_event["end_time"] = end_time.strftime("%d-%m-%Y %H:%M")
#                 except ValueError:
#                     await ctx.send("❌ Fehler: Ungültige Dauer. Bitte gib die Dauer in Minuten an.")
#                     return

#             # Cover-Bild
#             if cover_image:
#                 old_cover = db_event.get("cover_image")
#                 update_data["cover_image"] = cover_image
#                 new_data["cover_image"] = {"old": old_cover, "new": cover_image}
#                 db_event["cover_image"] = cover_image

#             # Typwechsel zwischen intern und extern
#             if location_type == "external":
#                 if not external_location:
#                     await ctx.send("❌ Fehler: Für externe Events muss ein externer Link angegeben werden.")
#                     return
#                 old_channel_id = db_event.get("channel_id")
#                 db_event["location_type"] = "external"
#                 db_event["location_metadata"] = {"location": external_location}
#                 db_event.pop("channel_id", None)

#                 update_data["event_type"] = ScheduledEventType.EXTERNAL
#                 update_data["channel_id"] = None
#                 update_data["external_location"] = external_location

#                 new_data["location_type"] = {"old": "internal", "new": "external"}
#                 new_data["location"] = {"old": old_channel_id, "new": external_location}

#             elif location_type == "internal":
#                 if not voice_channel:
#                     await ctx.send("❌ Fehler: Für interne Events muss ein Voice-Channel angegeben werden.")
#                     return
#                 old_location = db_event.get("location_metadata", {}).get("location", None)
#                 db_event["location_type"] = "internal"
#                 db_event["channel_id"] = voice_channel.id
#                 db_event["location_metadata"] = None

#                 update_data["event_type"] = ScheduledEventType.VOICE
#                 update_data["channel_id"] = voice_channel.id

#                 new_data["location_type"] = {"old": "external", "new": "internal"}
#                 new_data["channel_id"] = {"old": None, "new": voice_channel.id}
#                 new_data["channel_name"] = {"old": old_location, "new": voice_channel.name}

#             # Änderungen anwenden
#             await event.edit(**update_data)

#             # Lokale Datenbank aktualisieren
#             with open(file_path, 'r+', encoding='utf-8') as file:
#                 file.seek(0)
#                 json.dump(event_data, file, indent=4, ensure_ascii=False)
#                 file.truncate()

#             # Ausgabe der Änderungen
#             changes = "\n".join([f"{key}: {values['old']} -> {values['new']}" for key, values in new_data.items()])
#             await ctx.send(
#                 f"🔄 Event **{event.name}** wurde erfolgreich aktualisiert! \n\n Änderungen: \n {changes}"
#             )

#             # Lokale Events neu laden (für Autocomplete)
#             self.reload_events()

#         except Exception as e:
#             await ctx.send(f"❌ Fehler beim Aktualisieren des Events: {e}")

#     @update_event.autocomplete("event_id")
#     async def autocomplete_event_id(self, ctx: AutocompleteContext):
#         self.reload_events()
#         try:
#             guild_id = ctx.guild_id
#             if not guild_id:
#                 await ctx.send(choices=[])
#                 return

#             events = self.validate_guild_events(guild_id)
#             if not events:
#                 await ctx.send(choices=[])
#                 return

#             event_suggestions = [
#                 {
#                     "name": f"Was: {event['title']} | ID: {event['id']}",
#                     "value": event["id"]
#                 }
#                 for event in events
#             ]
#             await ctx.send(choices=event_suggestions[:25])
#         except Exception as e:
#             print(f"Fehler beim Autocomplete: {e}")
#             await ctx.send(choices=[])

#     @update_event.autocomplete("event_title")
#     async def autocomplete_event_title(self, ctx: AutocompleteContext):
#         self.reload_events()
#         try:
#             guild_id = ctx.guild_id
#             if not guild_id:
#                 await ctx.send(choices=[])
#                 return

#             events = self.validate_guild_events(guild_id)
#             if not events:
#                 await ctx.send(choices=[])
#                 return

#             event_suggestions = [
#                 {
#                     "name": f"Was: {event['title']}",
#                     "value": event["title"]
#                 }
#                 for event in events
#             ]
#             await ctx.send(choices=event_suggestions[:25])
#         except Exception as e:
#             print(f"Fehler beim Autocomplete: {e}")
#             await ctx.send(choices=[])


#     @update_event.autocomplete("event_description")
#     async def autocomplete_event_description(self, ctx: AutocompleteContext):
#         self.reload_events()
#         try:
#             guild_id = ctx.guild_id
#             if not guild_id:
#                 await ctx.send(choices=[])
#                 return

#             events = self.validate_guild_events(guild_id)
#             if not events:
#                 await ctx.send(choices=[])
#                 return

#             event_suggestions = [
#                 {
#                     "name": f"Was: {event['description']}",
#                     "value": event["description"]
#                 }
#                 for event in events
#             ]
#             await ctx.send(choices=event_suggestions[:25])
#         except Exception as e:
#             print(f"Fehler beim Autocomplete: {e}")
#             await ctx.send(choices=[])


#     @update_event.autocomplete("event_time")
#     async def autocomplete_event_time(self, ctx: AutocompleteContext):
#         self.reload_events()
#         try:
#             guild_id = ctx.guild_id
#             if not guild_id:
#                 await ctx.send(choices=[])
#                 return

#             events = self.validate_guild_events(guild_id)
#             if not events:
#                 await ctx.send(choices=[])
#                 return

#             event_suggestions = [
#                 {
#                     "name": f"Was: {event['time']}",
#                     "value": event["time"]
#                 }
#                 for event in events
#             ]
#             await ctx.send(choices=event_suggestions[:25])
#         except Exception as e:
#             print(f"Fehler beim Autocomplete: {e}")
#             await ctx.send(choices=[])

#     @update_event.autocomplete("event_duration")
#     async def autocomplete_event_duration(self, ctx: AutocompleteContext):
#         self.reload_events()
#         try:
#             guild_id = ctx.guild_id
#             if not guild_id:
#                 await ctx.send(choices=[])
#                 return

#             events = self.validate_guild_events(guild_id)
#             if not events:
#                 await ctx.send(choices=[])
#                 return

#             event_suggestions = [
#                 {
#                     "name": f"Was: {event['duration']}",
#                     "value": event["duration"]
#                 }
#                 for event in events
#             ]
#             await ctx.send(choices=event_suggestions[:25])
#         except Exception as e:
#             print(f"Fehler beim Autocomplete: {e}")
#             await ctx.send(choices=[])

#     @update_event.autocomplete("external_location")
#     async def autocomplete_event_location(self, ctx: AutocompleteContext):
#         self.reload_events()
#         try:
#             guild_id = ctx.guild_id
#             if not guild_id:
#                 await ctx.send(choices=[])
#                 return

#             events = self.validate_guild_events(guild_id)
#             if not events:
#                 await ctx.send(choices=[])
#                 return

#             event_suggestions = [
#                 {
#                     "name": event["location_metadata"]["location"],
#                     "value": event["location_metadata"]["location"]
#                 }
#                 for event in events
#                 if event.get("location_metadata") and "location" in event["location_metadata"]
#             ]
#             await ctx.send(choices=event_suggestions[:25])
#         except Exception as e:
#             print(f"Fehler beim Autocomplete: {e}")
#             await ctx.send(choices=[])


# def setup(bot):
#     Event(bot)
