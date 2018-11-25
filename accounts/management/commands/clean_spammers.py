from django.db.models import Count
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    def handle(self, *args, **_options):
        """Delete unconfirmed users with a website and no games"""
        users = (
            User.objects
            .annotate(game_count=Count('gamelibrary__games'))
            .filter(
                email_confirmed=False,
                game_count=0
            )
            .exclude(website__exact='')
        )

        cleared_users = len(users)
        for user in users:
            print("Deleting %s (website: %s)" % (user, user.website))
            user.delete()
        print("Cleared %d users" % cleared_users)
