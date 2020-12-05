"""Match GOGDB games with Lutris games"""
import json
from django.core.management.base import BaseCommand
from django.db.models import Q
from games.models import Game, Company, Platform
from providers import models
from common.util import get_auto_increment_slug, slugify
from providers.processors import clean_name


class Command(BaseCommand):
    def handle(self, *args, **options):
        for game in models.ProviderGame.objects.filter(provider__name="steam"):
            existing_games = Game.objects.filter(steamid=game.slug)
            for lutris_game in existing_games:
                print(lutris_game)
                lutris_game.provider_games.add(game)
                if not lutris_game.is_public:
                    lutris_game.is_public = True
                    lutris_game.save()
