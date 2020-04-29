"""Resize all game banners to a fixed size"""
import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from sorl.thumbnail import get_thumbnail
from games.models import Game


class Command(BaseCommand):
    """Resize banners and icons"""

    ICON_PATH = os.path.join(settings.MEDIA_ROOT, "game-icons/128")
    BANNER_PATH = os.path.join(settings.MEDIA_ROOT, "game-banners/184")

    def resize_icon(self, game):
        """Resize icon to fixed size"""
        dest_file = os.path.join(self.ICON_PATH, "%s.png" % game.slug)
        if os.path.exists(dest_file):
            return
        thumbnail = get_thumbnail(
            game.icon,
            settings.ICON_SIZE,
            crop="center",
            format="PNG"
        )
        shutil.copy(os.path.join(settings.MEDIA_ROOT, thumbnail.name), dest_file)

    def resize_banner(self, game):
        """Resize banner to fixed size"""
        dest_file = os.path.join(self.BANNER_PATH, "%s.jpg" % game.slug)
        if os.path.exists(dest_file):
            return
        thumbnail = get_thumbnail(
            game.title_logo,
            settings.BANNER_SIZE,
            crop="center"
        )
        shutil.copy(os.path.join(settings.MEDIA_ROOT, thumbnail.name), dest_file)

    def handle(self, *args, **_kwargs):
        """Run command"""
        if not os.path.exists(self.ICON_PATH):
            os.makedirs(self.ICON_PATH)
        if not os.path.exists(self.BANNER_PATH):
            os.makedirs(self.BANNER_PATH)

        games = Game.objects.all()
        for game in games:
            icon_path = os.path.join(settings.MEDIA_ROOT, game.icon.name)
            if game.icon.name:
                if not os.path.exists(icon_path):
                    print("%s is missing icon" % game)
                else:
                    self.resize_icon(game)

            banner_path = os.path.join(settings.MEDIA_ROOT, game.title_logo.name)
            if game.title_logo.name:
                if not os.path.exists(banner_path):
                    print("%s is missing banner" % game)
                else:
                    self.resize_banner(game)
