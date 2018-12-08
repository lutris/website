"""Updates the popularity of all games"""
from django.core.management.base import BaseCommand
from django.db.models import Count

from games.models import Game


class Command(BaseCommand):
    """Command to update the popularity"""
    help = "My shiny new management command."

    def handle(self, *args, **options):
        for game in Game.objects.all():
            game.popularity = game.libraries.all().count()
            game.save()
