"""Match GOGDB games with Lutris games"""
import json
from django.core.management.base import BaseCommand
from django.db.models import Q
from games.models import Game, Company, Platform
from providers import models
from common.util import get_auto_increment_slug, slugify

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-missing",
            action="store_true",
            help="Create missing games in Lutris"
        )

    @staticmethod
    def match_game(gogdb_game, lutris_game):
        """Matches a game to a Lutris game"""
        lutris_game.provider_games.add(gogdb_game)
        return lutris_game

    @staticmethod
    def get_year(game):
        """Return release year from GOGDB release date"""
        if not game.metadata.get('release_date'):
            return
        return int(game.metadata["release_date"].split(',')[1].split('(')[0].strip())

    @staticmethod
    def clean_name(name):
        extras = (
            "demo",
            "gold pack",
            "complete pack",
            "the final cut",
            "enhanced edition",
            "free preview",
            "complete edition",
            "alpha version",
            "pc edition",
            "ultimate edition",
            "commander pack",
            "gold edition",
            "drm free edition",
            "directx 11 version",
            "remake",
            "original game soundtrack",
            "soundtrack",
            "cd version",
            "deluxe edition",
            "galaxy edition"
        )
        for extra in extras:
            if name.strip(")").lower().endswith(extra):
                name = name[:-len(extra)].strip(" -:®™(").replace("™", "")
        return name

    def get_existing_matches(self, game):
        """Return Lutris games matching GOG games"""
        game_name = self.clean_name(game.name)
        return Game.objects.filter(
            Q(name=game_name)
            | Q(gogid=game.slug)
            | Q(slug=slugify(game_name))
            | Q(aliases__name=game_name)
        ).exclude(change_for__isnull=False).order_by('id').distinct('id')

    def find_match(self, game):
        """Find matching Lutris game for a GOG game"""
        gog_year = self.get_year(game)
        existing_games = self.get_existing_matches(game)
        if len(existing_games) > 1:
            print("Duplicates found for %s: %s" % (game, existing_games))
        matches = []
        for existing_game in existing_games:
            matches.append(self.match_game(game, existing_game))
        return matches

    def handle(self, *args, **options):
        arcade_platform = Platform.objects.get(slug="arcade")
        for game in models.ProviderGame.objects.filter(provider__name="GOGDB"):
            product_type = game.metadata.get("product_type")
            if product_type != "Game":
                print("Skipping content type %s for %s" % (product_type, game))
                continue
            match = self.find_match(game)
            if not match and options.get("create_missing"):
                gog_year = int(game.metadata["year"]) if game.metadata["year"] else None
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
                    year=gog_year,
                    publisher=publisher,
                    is_public=True
                )
                lutris_game.platforms.add(arcade_platform)
                lutris_game.provider_games.add(game)
                print("Created %s" % lutris_game)
            elif match:
                print("Matched game %s with %s" % (game, match))
                pass
            else:
                print("No match found for %s" % game)
