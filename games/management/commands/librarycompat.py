from __future__ import unicode_literals
import json
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    args = "<username>"

    def handle(self, *args, **kwargs):
        try:
            username = args[0]
        except IndexError:
            self.stderr.write("No username provided")

        user = User.objects.get(username=username)
        library = user.gamelibrary
        library_stats = {
            "total": 0,
            "linux_steam": 0,
            "linux": 0,
            "windows_only": 0,
            "wine": 0,
            "non_steam": 0,
            "unknown": 0,
        }
        library_stats["total"] = library.games.count()
        for game in library.games.all():
            if not game.steamid:
                library_stats["non_steam"] += 1
                continue
            runners = set([i.runner.slug for i in game.installers.all()])
            if "steam" in runners:
                library_stats["linux_steam"] += 1
                continue
            if "linux" in runners:
                library_stats["linux"] += 1
                continue
            if "winesteam" in runners:
                game_works = True
                for installer in game.installers.all():
                    if (
                        installer.runner.slug == "winesteam"
                        and installer.rating == "garbage"
                    ):
                        game_works = False
                if game_works:
                    library_stats["wine"] += 1
                else:
                    library_stats["windows_only"] += 1
                continue
            library_stats["unknown"] += 1
            self.stdout.write(str(game))

        self.stdout.write(json.dumps(library_stats, indent=2))
