import asyncio
import logging
from turtledemo.penrose import start

from interactions import Extension, SlashContext, slash_command, Permissions, IntervalTrigger, Task, listen
from interactions.api.events import discord


class VoiceJoin(Extension):
    def __init__(self, bot):
        self.bot = bot
        logging.info("Extension loaded: VoiceJoin")

    @slash_command(name="join", description="Tritt dem Voice-Channel des Benutzers bei", default_member_permissions=Permissions.ADMINISTRATOR)
    async def join(self, ctx: SlashContext, channel: str = None):
        if ctx.author.voice:
            channelname = ctx.author.voice.channel.name
            await ctx.defer(ephemeral=True)
            await ctx.send(f'Trete " **{channelname}** " bei...')
            await ctx.author.voice.channel.connect()
            self.auto_leave_if_empty.start()
        else:
            await ctx.defer(ephemeral=True)
            await ctx.send("Du bist in keinem Voice-Channel.")
            if ctx.send():
                await ctx.edit("Du bist in keinem Voice-Channel.")

    @Task.create(IntervalTrigger(seconds=10))
    async def auto_leave_if_empty(self):
        for guild in self.bot.guilds:
            if guild.voice_state:  # Prüfen, ob der Bot in einem Voice-Channel ist
                channel_id = guild.voice_state.channel
                channel = await self.bot.fetch_channel(channel_id)
                if channel and len(channel.voice_members) <= 1 :  # Nur der Bot ist im Channel
                    print(f"Channel {channel.name} ist leer. Bot verlässt den Channel in 5 Sekunden.")
                    await asyncio.sleep(5)  # 5 Sekunden warten, bevor er verlässt
                    # führe async def leave(self, ctx: SlashContext): aus
                    if channel and len(channel.voice_members) <= 1:  # Nur der Bot ist im Channel
                        await channel.disconnect()
                        self.auto_leave_if_empty.restart()

    @slash_command(name="leave", description="Verlässt den Voice-Channel", default_member_permissions=Permissions.ADMINISTRATOR)
    async def leave(self, ctx: SlashContext):
        if ctx.author.voice:
            channelname = ctx.author.voice.channel.name
            await ctx.defer(ephemeral=True)
            await ctx.send(f'Verlasse " **{channelname}**  "')
            await ctx.author.voice.channel.disconnect()
            # Restart the auto leave task
            self.auto_leave_if_empty.restart()
        else:
            await ctx.defer(ephemeral=True)
            await ctx.send("Du bist in keinem Voice-Channel.")


    @listen()
    async def on_startup(self):
        # Ensure the task is started
        self.auto_leave_if_empty.start()
