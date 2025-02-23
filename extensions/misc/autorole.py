from interactions import Extension, listen, Member
from interactions.api.events import MemberAdd
from interactions.models.discord import guild


class Autorole(Extension):
    def __init__(self, bot):
        self.bot = bot
        print("Extension loaded: Autorole")





    @listen(MemberAdd)
    async def onMemberAdd(self, event: MemberAdd):
        member = event.member
        guild = member.guild

        # Suche nach der Rolle "Flammenjünger"
        role = next((r for r in guild.roles if r.name == "Flammenjünger"), None)

        # Rolle erstellen, falls sie nicht existiert
        if role is None:
            print("[INFO] Rolle 'Flammenjünger' existiert nicht. Erstelle Rolle...")
            role = await guild.create_role(
                name="Flammenjünger",
                mentionable=True,
                hoist=True,
                color=0x00FF00
            )
            print("[INFO] Rolle 'Flammenjünger' wurde erstellt.")

        # Rolle hinzufügen
        try:
            # add_roles erwartet eine Liste oder ein Tupel, also Rolle in eine Liste packen
            await member.add_roles([role])
            print(f"[INFO] Rolle '{role.name}' wurde an {member.user.username} vergeben.")
        except Exception as e:
            print(f"[ERROR] Fehler beim Hinzufügen der Rolle: {e}")
