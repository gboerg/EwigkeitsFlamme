import logging

from interactions import Extension, listen, Embed, Member, Guild, File
from interactions.api.events import MemberAdd
from easy_pil import Editor, load_image_async, Font
import os


class Welcome(Extension):
    def __init__(self, bot):
        self.bot = bot
        logging.info("Extension loaded: Welcome")

    @listen()
    async def onMemberJoin(self, event: MemberAdd):
        member = event.member

        try:
            # Profilbild-URL
            profile_image_url = member.avatar.url if member.avatar else "assets/default_avatar.jpg"
            profile_image = await load_image_async(profile_image_url)

            # Hintergrund und Profilbild
            background = Editor("assets/images/welcome.jpg")
            profile = Editor(profile_image).resize((600, 600)).circle_image()

            # Schriftarten
            poppins = Font.poppins(size=200, variant="bold")
            poppins_small = Font.poppins(size=100, variant="light")

            # Profilbild zentrieren
            background.paste(profile, (2085 - 300, 1000 - 100))
            background.ellipse((2085 - 300, 1000 - 100), 600, 600, outline="white", stroke_width=15)


            # Profilbild zentrieren
            #background.paste(profile, (2085 - 300, 1000 - 300))
            #background.ellipse((2085 - 300, 1000 - 300), 600, 600, outline="white", stroke_width=15)

            # Benutzernamen und Willkommensnachricht
            user_display_name = (
                f"{member.user.username}" if member.user.discriminator == "0" else f"{member.user.username}#{member.user.discriminator}"
            )
            background.text((2085, 500), f"Willkommen auf {member.guild.name}!", color="white", font=poppins, align="center")
            background.text((2085, 1550), user_display_name, color="white", font=poppins_small, align="center")
            #background.text((2085, 1400), user_display_name, color="white", font=poppins_small, align="center")

            # Bild speichern
            temp_path = "new_welcome.jpg"
            background.image = background.image.convert("RGB")
            background.save(temp_path)

            # Datei laden
            file = File(temp_path)

            # Embeds
            dmembed = (
                Embed(
                    title=f"Willkommen {member.user.username}!",
                    description=(f"Du bist jetzt Teil von {member.guild.name}. Erkunde den Server und werde ein Teil unserer Gemeinschaft!"),
                    color=0x8A2BE2
                )
                .set_thumbnail(url=profile_image_url)
                .set_footer(
                    text=f"Du bist jetzt Mitglied in {member.guild.name}.",
                    icon_url=member.guild.icon.url if member.guild.icon else self.bot.user.avatar.url
                )
                .add_field(
                    name="🚀 Dein Abenteuer beginnt!",
                    value="Erkunde den Server und lerne die Community kennen!",
                    inline=False
                )
                .set_image(url="attachment://new_welcome.jpg")
                .set_author(
                    name="Willkommen bei uns!",
                    icon_url=member.guild.icon.url if member.guild.icon else self.bot.user.avatar.url
                )
            )

            clembed = (
                Embed(
                    title=f"Willkommen {member.user.username}!",
                    description=(f"Du bist jetzt Teil von {member.guild.name}. Erkunde den Server und werde ein Teil unserer Gemeinschaft!"),
                    color=0x8A2BE2
                )
                .set_thumbnail(url=profile_image_url)
                .set_footer(
                    text=f"Du bist jetzt Mitglied in {member.guild.name}.",
                    icon_url=member.guild.icon.url if member.guild.icon else self.bot.user.avatar.url
                )
                .add_field(
                    name="🚀 Dein Abenteuer beginnt!",
                    value="Erkunde den Server und lerne die Community kennen!",
                    inline=False
                )
                .set_image(url="attachment://new_welcome.jpg")
                .set_author(
                    name="Willkommen bei uns!",
                    icon_url=member.guild.icon.url if member.guild.icon else self.bot.user.avatar.url
                )
            )

            # Nachrichten senden
            await member.send(embed=dmembed, files=[file])
            await event.guild.get_channel(1315239357740879892).send(embed=clembed, files=[file])


            logging.debug(f"Nachricht erfolgreich an {member.user.username} gesendet.")
        except Exception as e:
            logging.error("Fehler beim Senden der Nachricht", e)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
