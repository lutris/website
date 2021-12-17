"""Load a list of games from Steam"""
import requests
from django.core.management.base import BaseCommand
from providers import models

API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/?"


class Command(BaseCommand):
    """Load all Steam games from the Steam API"""
    provider_id = "steam"

    def handle(self, *args, **options):
        provider, _created = models.Provider.objects.get_or_create(name=self.provider_id)
        response = requests.get(API_URL)
        game_list = response.json()["applist"]["apps"]
        for game in game_list:
            provider_game, _created = models.ProviderGame.objects.get_or_create(
                slug=game["appid"],
                provider=provider
            )
            provider_game.name = game["name"]
            provider_game.save()
            print("%s (%s)" % (game["name"], game["appid"]))
