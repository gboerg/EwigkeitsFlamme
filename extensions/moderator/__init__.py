from interactions import Extension, OptionType, Permissions, SlashContext, User, slash_command, slash_option
import interactions

class Moderator(Extension):
    def __init__(self, bot):
        print("Extension loaded: Moderator")

    def setup(bot):
        Moderator(bot)

    @slash_command(
        name="ban",
        description="For thoose who wont behave",
        default_member_permissions=Permissions.BAN_MEMBERS,
    )
    @slash_option(
        name="user",
        description="Who's the bad boy?",
        opt_type=OptionType.USER,
        required=True
    )
    async def ban_user(self, ctx: SlashContext):

        try:
            await ctx.defer(ephemeral=True)

            guild = ctx.guild
            if not guild:
                await ctx.send("Navigate to any guild channel and execute command again")
                return
            
            
            
            user = ctx.kwargs["user"]
            if not user:
                await ctx.send(f"You must select a valid user")
                return

            await guild.ban(user)
            await ctx.send(f"{user} was banned from {guild} successfully")

        except Exception as e:
            await ctx.send(f"Error during banning progress: {e}")

    @slash_command(
        name="unban",
        description="Forgiveness is the key to a better world",
        default_member_permissions=Permissions.BAN_MEMBERS
    )
    @slash_option(
        name="user",
        description="Who deserve to be forgiven",
        opt_type=OptionType.USER,
        required=True
    )
    async def unBanUser(self, ctx:SlashContext):
        try:
            guild = ctx.guild
            if not guild:
                await ctx.send("Guild Only")
                return
            
            user = ctx.kwargs["user"]
            if not user:
                await ctx.send(f"You must select a valid user")
                return

            await guild.unban(user)
            await ctx.send(f"{user} successfully unbanned - His sins will be rememberd but forgiven")

        except Exception as e:
            await ctx.send(f"Error during banning progress: {e}")

    @slash_command(
        name="clear",
        description="Take the trash out - Or unessary messages"
    )
    @slash_option(
        name="count",
        description="How many messages you want to delete?",
        opt_type=OptionType.INTEGER,
        required=False
    )
    async def clear(self, ctx:SlashContext):
        try:
            guild = ctx.guild
            if not guild:
                await ctx.send("Guild Only")
                return
            
            




        except Exception as e:
            await ctx.send(f"Unable to comply | No messages were deleted: {e}")