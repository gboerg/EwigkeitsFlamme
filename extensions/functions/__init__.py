import json

from interactions import Extension


class Function(Extension):
    def __init__(self, bot):
        print("Extension loaded: Function Module")


    def save_to_json(self, data, filename):
        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)  # Speichere die Events in die Datei
            print(f"✅ Daten erfolgreich in {filename} gespeichert.")
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Events: {e}")

    def load_events(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        except json.decoder.JSONDecodeError:
            print(f" Fehler beim Laden der JSON-Datei. Starte mit neuer Liste.")
            return []

    #def update_events(self, data, file_path):



    def create_event(self, guild_id, event_id, command_sender, event_title, event_description, event_time,
                     event_duration, event_channel, location, image):
        try:
            # Sicherstellen, dass die Tabelle existiert
            create_table_query = """
            CREATE TABLE IF NOT EXISTS events (
                guild_id INTEGER NOT NULL,
                id INTEGER PRIMARY KEY,
                command_sender_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                time TEXT NOT NULL,
                duration INTEGER,
                channel_id INTEGER,
                location_type TEXT,
                location_metadata TEXT,
                cover_image TEXT
            );
            """
            self.db.connect_sqlite('bot.db', create_table_query)  # Tabelle erstellen, falls sie nicht existiert

            # Query für das Einfügen eines neuen Events
            insert_query = """
            INSERT INTO events (guild_id, id, title, description, time, duration, channel_id, location_type, location_metadata, cover_image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """

            # Parameter für das Event
            params = (
                guild_id,
                event_id,
                event_title,
                event_description,
                event_time,
                event_duration,
                event_channel.id if event_channel else None,
                "channel" if event_channel else "custom",
                location,
                image,
            )

            # Event einfügen
            self.db.connect_sqlite('bot.db', insert_query, params)
            logging.info(f"✅ Event '{event_title}' für Guild '{guild_id}' erstellt von {command_sender.name}.")
        except Exception as e:
            logging.error(f"❌ Fehler beim Erstellen des Events: {e}")

    def delete_event(self, guild_id, event_id):
        guild_id_str = str(guild_id)  # Sicherstellen, dass die Guild-ID ein String ist

        # Prüfen, ob die Guild-ID in self.events existiert
        if guild_id_str not in self.events:
            logging.info(f"❌ Guild-ID {guild_id_str} not found")
            return False

        # Zugriff auf die Event-Liste für die Guild-ID
        guild_events = self.events[guild_id_str]
        if not isinstance(guild_events, list):  # Sicherstellen, dass wir eine Liste erhalten
            logging.info(f"❌ Expected {guild_id_str} but got {type(guild_events)}")
            return False

        # Event anhand der ID suchen und entfernen
        event_to_remove = next((e for e in guild_events if str(e.get("id")) == str(event_id)), None)
        if event_to_remove:
            guild_events.remove(event_to_remove)  # Entfernen des Events aus der Liste
            logging.info(f"✅ Event {event_id} erfolgreich gelöscht.")

            # Persistiere die Änderungen
            self.events[guild_id_str] = guild_events  # Aktualisiere die Liste in self.events
            self.save_events()
            return True

        logging.info(f"❌ Event {event_id} nicht gefunden.")
        return False

    def validate_guild_events(self, guild_id):
        try:
            self.reload_events()

            if not guild_id:
                return []
            return [event for event in self.events.get(str(guild_id), [])]  # Greift auf Events der Guild zu
        except Exception as e:
            logging.info(f"Fehler bei der Eingabe: {e}")
            return []

    def get_event_location(self, event, guild):
        if event.get("channel_id") is None:
            return event["location_metadata"]["location"] if event.get("location_metadata") else "Unbekannter Standort"
        else:
            channel = guild.get_channel(int(event["channel_id"]))
            return channel.name if channel else "Unbekannter Kanal"

    def reload_events(self):
        """Lädt die Events erneut aus der JSON-Datei."""
        try:
            if not os.path.exists(self.events_file):
                logging.info(f"❌ Fehler: Datei {self.events_file} existiert nicht.")
                self.events = defaultdict(list)  # Standardmäßig ein defaultdict, falls Fehler auftreten
                return

            with open(self.events_file, 'r', encoding='utf-8') as file:
                self.events = json.load(file)

            logging.info("✅ Events erfolgreich geladen!")
        except json.JSONDecodeError as e:
            print(f"❌ Fehler beim Dekodieren der JSON-Daten: {e}")
            self.events = defaultdict(list)  # Fallback
        except Exception as e:
            print(f"❌ Fehler beim Laden der Events: {e}")
            self.events = defaultdict(list)  # Fallback


    def update_events(self, event_id, updates):
        """Aktualisiert ein bestehendes Event in der lokalen Datenbank."""
        for guild_events in self.events.values():
            for event in guild_events:
                if event["id"] == event_id:
                    event.update(updates)
                    break
        self.save_events()
        self.reload_events()  # Aktualisiere die Event-Liste nach dem Speichern

    def load_events(self):
        try:
            with open(self.events_file, "r", encoding="utf-8") as file:
                events = json.load(file)
            # Wenn Events geladen werden, sicherstellen, dass es ein defaultdict ist
            if not isinstance(events, dict):
                events = defaultdict(list, events)
            return events
        except (FileNotFoundError, json.JSONDecodeError):
            return defaultdict(list)  # Falls Datei nicht existiert oder Fehler auftritt


    def save_events(self):
        try:
            # Wandelt das defaultdict in ein reguläres dict um, um es zu speichern
            with open(self.events_file, "w", encoding="utf-8") as file:
                json.dump(dict(self.events), file, indent=4, ensure_ascii=False)  # Speichern der Events
            logging.info(f"✅ Events erfolgreich in {self.events_file} gespeichert.")
        except Exception as e:
            logging.info(f"❌ Fehler beim Speichern der Events: {e}")
