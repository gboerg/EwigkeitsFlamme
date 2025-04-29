import interactions
import logging as l


from interactions import Extension, Permissions, Reaction, SlashContext, slash_command, slash_option


class RoleReact(Extension):
    def __init__(self, bot):
        self.bot = bot
        l.info("[MISC | ROLEREACT] Extension was loaded")
    def setup(bot):
        RoleReact(bot)

    @slash_command(
        name="reaction",
        description="Verwalte die Reactions.",
        default_member_permissions=Permissions.ADMINISTRATOR
    )
    async def reaction(self, ctx: SlashContext):
        pass
    @reaction.subcommand(
        sub_cmd_name="add",
        sub_cmd_description="Füge eine Beschreibung.",
    )
    @slash_option(
        name="message",
        description="Nachricht für welche die Reaction vorgesehen ist."
    )
    @slash_option(
        name="emoji",
        description="Emoji mit dem Reagiert werden sollte."
    )

    async def add_reaction(
        self,
        ctx: SlashContext,
        message: int,
        emoji: str,
    ):
        try:
            await ctx.defer(ephemeral=True)
            guild = ctx.guild

            if not message:
                return
            
        except Exception as e:
            await ctx.send(f"Failed to add Reaction {e}")
            
        


    async def on_user_react(self, reaction: Reaction):
        reaction