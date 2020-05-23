"""Match MAME games with Lutris games"""
import json
from django.core.management.base import BaseCommand
from games.models import Game, Company, Platform
from providers import models
from common.util import get_auto_increment_slug, slugify

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-missing",
            action="store_true",
            help="Path to the MAME game list"
        )

    @staticmethod
    def match_game(mame_game, lutris_game):
        """Matches a MAME game to a Lutris game"""
        lutris_game.provider_games.add(mame_game)
        return lutris_game

    def find_matches(self, game):
        mame_year = int(game.metadata["year"]) if game.metadata["year"] else None
        existing_games = Game.objects.filter(name=game.name)
        for existing_game in existing_games:
            lutris_year = existing_game.year
            if mame_year != lutris_year:
                if all((lutris_year, mame_year)) and abs(lutris_year - mame_year) < 3:
                    return self.match_game(game, existing_game)
                continue
            return self.match_game(game, existing_game)

    def handle(self, *args, **options):
        arcade_platform = Platform.objects.get(slug="arcade")
        for game in models.ProviderGame.objects.filter(provider__name="MAME"):
            match = self.find_matches(game)
            if not match and options.get("create_missing"):
                mame_year = int(game.metadata["year"]) if game.metadata["year"] else None
                publisher_slug = slugify(game.metadata.get("publisher", ""))
                if publisher_slug:
                    publisher, created = Company.objects.get_or_create(slug=publisher_slug)
                    if created:
                        publisher.name = game.metadata["publisher"]
                        publisher.save()
                else:
                    publisher = None
                lutris_game = Game.objects.create(
                    name=game.name,
                    slug=get_auto_increment_slug(Game, None, game.name),
                    year=mame_year,
                    publisher=publisher,
                    is_public=True
                )
                lutris_game.platforms.add(arcade_platform)
                lutris_game.provider_games.add(game)
                print("Created %s" % lutris_game)
