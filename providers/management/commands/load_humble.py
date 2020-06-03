"""Load a list of games from a Humble Bundle export"""
import json
from django.core.management.base import BaseCommand
from providers import models


class Command(BaseCommand):

    provider_id = "HUMBLE"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs=1,
            help="Path to the Humble DB game list"
        )

    def handle(self, *args, **options):
        file_path = options["file_path"][0]
        provider, _created = models.Provider.objects.get_or_create(name=self.provider_id)
        with open(file_path) as list_file:
            game_list = json.load(list_file)
        for game in game_list.values():
            provider_game, _created = models.ProviderGame.objects.get_or_create(
                slug=game["slug"],
                provider=provider
            )
            provider_game.name = game["name"]
            provider_game.metadata = game
            provider_game.save()
            print("%s (%s)" % (game["name"], game["slug"]))
