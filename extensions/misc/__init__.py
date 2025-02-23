from time import sleep

from interactions import Extension, slash_command, Embed, SlashContext, slash_option, OptionType, SlashCommandChoice


class Misc(Extension):
    def __init__(self, bot):
        print("Extension loaded: Misc")
        #bot.load_extension("extensions.misc.voicejoin")
        bot.load_extension("extensions.misc.autorole")
        bot.load_extension("extensions.misc.welcome")

    @slash_command(name="ping", description="Does pong along with a simple embed")
    async def ping_command(self, ctx: SlashContext):
        await ctx.defer(ephemeral=True)
        sleep(1)
        await ctx.send(embed=Embed(
            color=0x00ff00,
            title="Just a simple ping command",
            description="pong"
        ))

