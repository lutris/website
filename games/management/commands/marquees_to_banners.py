"""Generate banners from ProgettoSnap marquees"""
import os
from PIL import Image

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings
from common.util import crop_banner
from games.models import Game


if settings.DEBUG:
    MARQUEE_PATH = "/media/strider/Backup/Games/Arcade/marquees/"
else:
    MARQUEE_PATH = os.path.join(settings.MEDIA_ROOT, "mame/marquees")
BANNER_PATH = os.path.join(settings.MEDIA_ROOT, "mame/banners")


class Command(BaseCommand):
    """Resize banners and icons"""

    @staticmethod
    def make_banner_from_marquee(game):
        """Generate a banner for a game from available marquees"""
        mame_ids = [pgame.slug for pgame in game.provider_games.all()]
        for mame_id in mame_ids:
            marquee_path = os.path.join(MARQUEE_PATH, "%s.png" % mame_id)
            if not os.path.exists(marquee_path):
                continue
            marquee = Image.open(marquee_path)
            ratio = marquee.size[0] / marquee.size[1]
            max_ratio = 5
            min_ratio = 2
            if ratio < min_ratio or ratio > max_ratio:
                continue
            banner_filename = "%s.jpg" % mame_id
            banner_path = os.path.join(BANNER_PATH, banner_filename)
            crop_banner(marquee_path, banner_path)
            with open(banner_path, "rb") as banner_file:
                banner_content = banner_file.read()
            game.title_logo = ContentFile(banner_content, banner_filename)
            game.save()
            print("Banner created for %s" % game)
            return

    def handle(self, *args, **_kwargs):
        """Run command"""
        if not os.path.exists(BANNER_PATH):
            os.makedirs(BANNER_PATH)

        for game in Game.objects.filter(provider_games__provider__name="MAME"):
            if game.title_logo:
                continue
            self.make_banner_from_marquee(game)
