"""Load a list of games from a GOGDB export"""
import json
from django.core.management.base import BaseCommand
from providers import models


class Command(BaseCommand):

    provider_id = "GOGDB"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs=1,
            help="Path to the GOG DB game list"
        )

    def handle(self, *args, **options):
        file_path = options["file_path"][0]
        provider, _created = models.Provider.objects.get_or_create(
            name=self.provider_id
        )
        with open(file_path) as list_file:
            game_list = json.load(list_file)
        for game in game_list:
            if "product_id" not in game:
                continue
            provider_game, _created = \
                models.ProviderGame.objects.get_or_create(
                    slug=game["product_id"], provider=provider
                )
            provider_game.name = game["name"]
            provider_game.metadata = game
            provider_game.save()
            print("%s - %s %s (%s)" % (
                game["name"],
                game.get("release_date"),
                game.get("publisher"),
                game["product_id"]
            ))
