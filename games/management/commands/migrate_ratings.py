"""Migrate installer ratings"""
import logging
from collections import defaultdict
from django.core.management.base import BaseCommand
from accounts.models import User
from games.models import Installer, Rating

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate installer ratings to Rating table"

    def handle(self, *args, **options):
        """Change install scripts to specify wine prefix architecture"""
        # Get installers with ratings
        stats = defaultdict(int)
        user = User.objects.get(username='strider')
        installers = Installer.objects.filter(rating__isnull=False)
        for installer in installers:
            if not installer.rating:
                continue
            try:
                playable_value = int(installer.rating) > 2
            except ValueError:
                print("Invalid value for rating '%s'" % installer.rating)
                installer.rating = ""
                installer.save()
                continue

            print("Migrating rating for %s" % installer)
            Rating.objects.create(
                installer=installer,
                playable=playable_value,
                author=user,
            )
            installer.rating = ""
            installer.save()
            stats["migrated"] += 1
        print(stats)
