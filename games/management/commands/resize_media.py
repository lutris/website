"""Resize all game banners to a fixed size"""
import os
from django.core.management.base import BaseCommand
# from django.conf import settings
from games.models import Game


class Command(BaseCommand):
    """Resize banners and icons"""

    def handle(self, *args, **_kwargs):
        """Run command"""
        if not os.path.exists(Game.ICON_PATH):
            os.makedirs(Game.ICON_PATH)
        if not os.path.exists(Game.BANNER_PATH):
            os.makedirs(Game.BANNER_PATH)

        for game in Game.objects.all():
            game.precache_media()
