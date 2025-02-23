from interactions import Extension

class Autoevent(Extension):
    pass


'''
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

class AutoEventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.create_scheduled_event.start()  # Starte den automatischen Task

    # Dieser Task wird beim Starten des Bots ausgeführt und erstellt das Event
    @tasks.loop(count=1)  # Die Schleife läuft nur einmal
    async def create_scheduled_event(self):
        # Beispiel: Erstelle ein Event für den geplanten Stream in 5 Minuten
        guild = self.bot.get_guild(1307233623564488764)  # Hier die Guild-ID anpassen

        # Geplantes Event für den Stream erstellen (in 5 Minuten)
        event_time = datetime.utcnow() + timedelta(minutes=5)

        try:
            # Erstelle das geplante Event
            event = await guild.create_scheduled_event(
                name="Geplanter Stream",
                description="Ein geplanter Stream für den Ewigkeitsflamme-Kanal.",
                start_time=event_time,
                end_time=event_time + timedelta(hours=2),  # Dauer des Events (2 Stunden)
                privacy_level=discord.ScheduledEventPrivacyLevel.guild_only,
                entity_type=discord.ScheduledEventEntityType.external,  # Externes Event für Streaming
            )

            print(f"Geplantes Event 'Geplanter Stream' wurde für {event_time.strftime('%Y-%m-%d %H:%M')} erstellt!")
        except Exception as e:
            print(f"Fehler beim Erstellen des Events: {e}")

    # Die Funktion sorgt dafür, dass der Task beim Starten des Bots ausgeführt wird
    @create_scheduled_event.before_loop
    async def before_create_event(self):
        await self.bot.wait_until_ready()  # Warte, bis der Bot online ist

# Cog registrieren
async def setup(bot):
    await bot.add_cog(AutoEventCog(bot))
'''