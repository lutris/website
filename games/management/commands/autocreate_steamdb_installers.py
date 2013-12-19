import json
from django.core.management.base import BaseCommand
from games import models
from accounts.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open("steamdb.json") as steamdb_file:
            steamdb = json.loads(steamdb_file.read())
        steam_runner = models.Runner.objects.get(slug='steam')
        user = User.objects.get(username='strider')
        for steamapp in steamdb:
            if steamapp['linux_status'] == 'Game Works':
                appid = steamapp['appid']
                name = steamapp['name']
                try:
                    game = models.Game.objects.get(steamid=int(appid))
                except models.Game.DoesNotExist:
                    continue
                current_installer = game.installer_set.all()
                if current_installer:
                    continue
                self.stdout.write("Creating installer for %s" % name)
                installer = models.Installer()
                installer.runner = steam_runner
                installer.user = user
                installer.game = game
                installer.set_default_installer()
                installer.published = True
                installer.save()
