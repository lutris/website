"""Migrates winesteam scripts to Proton"""
import logging
from django.core.management.base import BaseCommand

from common.util import load_yaml, dump_yaml
from games.models import Installer, Runner

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate WineSteam games to Proton"

    def is_simple_installer(self, installer):
        script = load_yaml(installer.content)
        sections = set(script.keys())
        if sections in (
            {"game"},
            {"game", "wine"},
            {"game", "winesteam"},
            {"game", "winesteam", "system"}
        ):
            return True
        # Any Media Foundation workaround is likely very
        # outdated at this point
        if "Media Foundation" in installer.content:
            return True
        # People just submitting garbage
        if "vcrun2017 dxvk" in installer.content:
            return True
        print(list(script.keys()))
        print(installer.content)
        return False

    def has_steam_installer(self, installer):
        return bool(Installer.objects.filter(
            game=installer.game,
            runner__slug="steam"
        ).count())

    def get_winesteam_installers(self):
        return Installer.objects.filter(runner__slug="winesteam")

    def migrate_to_proton(self, installer):
        script = load_yaml(installer.content)
        appid = script["game"]["appid"]
        installer.content = dump_yaml({"game": {"appid": appid}})
        installer.runner = self.steam_runner
        installer.version = "Proton"
        installer.save()

    def handle(self, *args, **options):
        """Change install scripts to specify wine prefix architecture"""
        self.steam_runner = Runner.objects.get(slug="steam")
        installers = self.get_winesteam_installers()
        migrate_count = 0
        delete_count = 0
        for installer in installers:
            if self.has_steam_installer(installer):
                delete_count += 1
                print("Deleting %s" % installer)
                installer.delete()
                continue
            if not self.is_simple_installer(installer):
                continue
            migrate_count += 1
            print("Migrating %s" % installer)
            self.migrate_to_proton(installer)
        print("%s/%s installers migrated" % (migrate_count, len(installers)))
        print("%s/%s installers deleted" % (delete_count, len(installers)))