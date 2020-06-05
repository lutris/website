"""Generate banners from ProgettoSnap marquees"""
import os
from PIL import Image

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings
# from common.util import crop_banner
from games.models import Game


if settings.DEBUG:
    MAME_ICO_PATH = "/media/strider/Backup/Games/Arcade/icons"
else:
    MAME_ICO_PATH = os.path.join(settings.MEDIA_ROOT, "mame/icons")
ICON_PATH = os.path.join(settings.MEDIA_ROOT, "mame/icons-png")


class Command(BaseCommand):
    """Resize banners and icons"""

    @staticmethod
    def make_icon_from_icon(game):
        """Generate a banner for a game from available marquees"""
        mame_ids = [pgame.slug for pgame in game.provider_games.all()]
        for mame_id in mame_ids:
            mame_ico_path = os.path.join(MAME_ICO_PATH, "%s.ico" % mame_id)
            if not os.path.exists(mame_ico_path):
                continue
            icon_filename = "%s.png" % mame_id
            icon_path = os.path.join(ICON_PATH, icon_filename)
            try:
                ico_file = Image.open(mame_ico_path)
            except ValueError:
                print("Failed to read %s" % mame_ico_path)
                continue
            ico_file.save(icon_path, "PNG")
            with open(icon_path, "rb") as banner_file:
                icon_content = banner_file.read()
            game.icon = ContentFile(icon_content, icon_filename)
            game.save()
            print("Icon created for %s" % game)
            return

    def handle(self, *args, **_kwargs):
        """Run command"""
        if not os.path.exists(ICON_PATH):
            os.makedirs(ICON_PATH)

        for game in Game.objects.filter(provider_games__provider__name="MAME"):
            if game.icon:
                continue
            self.make_icon_from_icon(game)
