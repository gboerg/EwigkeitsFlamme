import json
from enum import member

from interactions import Extension, listen
from interactions.api.events import MemberAdd

from extensions.bot import event


class Event(Extension):
    def __init__(self, bot):
        self.bot = bot
        self.users_file = "database/users.json"  # Datei für die Speicherung
        self.users = self.load_users()  # Lade Events beim Start
        print("Extension geladen: Event")


        def load_users(self):
            try:
                with open(self.users_file, encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                return []
            except json.decoder.JSONDecodeError:
                print("❌ Fehler beim Laden der JSON-Datei. Starte mit leerer Liste.")
                return []

        @listen
        async def on_member_join(self, event: MemberAdd):
            member = event.member
            guild = event.guild

            self.users.append({})
