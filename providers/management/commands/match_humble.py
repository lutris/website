"""Match GOGDB games with Lutris games"""
import json
from django.core.management.base import BaseCommand
from django.db.models import Q
from games.models import Game, Company, Platform
from providers import models
from common.util import get_auto_increment_slug, slugify
from providers.processors import clean_name


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

    def get_existing_matches(self, game):
        """Return Lutris games matching GOG games"""
        cleaned_name = clean_name(game.name)
        return Game.objects.filter(
            Q(name=cleaned_name)
            | Q(name=game.name)
            | Q(humblestoreid=game.slug)
            | Q(slug=slugify(cleaned_name))
            | Q(aliases__name=cleaned_name)
            | Q(aliases__name=game.name)
        ).exclude(change_for__isnull=False).order_by('id').distinct('id')

    def find_matches(self, game):
        """Find matching Lutris game for a Humble game"""
        existing_games = self.get_existing_matches(game)
        if len(existing_games) > 1:
            print("Duplicates found for %s: %s" % (game, existing_games))
        matches = []
        for existing_game in existing_games:
            matches.append(self.match_game(game, existing_game))
        return matches

    def handle(self, *args, **options):
        platform_slugs = ['linux', 'windows']
        platforms = {
            slug: Platform.objects.get(slug=slug)
            for slug in platform_slugs
        }
        for game in models.ProviderGame.objects.filter(provider__name="HUMBLE"):
            matches = self.find_matches(game)
            if not matches and options.get("create_missing"):
                lutris_game = Game.objects.create(
                    name=game.name,
                    slug=get_auto_increment_slug(Game, None, game.name),
                    is_public=True,
                    humblestoreid=game.slug
                )
                supported_systems = game.metadata.get("platforms", [])
                for system in supported_systems:
                    try:
                        lutris_game.platforms.add(platforms[system])
                    except KeyError:
                        pass
                lutris_game.provider_games.add(game)
                print("Created %s" % lutris_game)
            elif not matches:
                print("No match found for %s" % game.name)
            else:
                print("Matched: %s" % matches)
