"""Delete spam accounts"""
from django.db.models import Count
from django.core.management.base import BaseCommand
from accounts.models import User


def get_no_games_with_website():
    """Return users that have not confirmed their account but have games"""
    return (
        User.objects
        .annotate(game_count=Count('gamelibrary__games'))
        .filter(
            email_confirmed=False,
            game_count=0
        )
        .exclude(website__exact='')
    )


def get_spam_avatar_users():
    """Return users that have a avatar matching what spam users use"""
    return (
        User.objects
        .annotate(game_count=Count('gamelibrary__games'))
        .filter(
            avatar__regex="/\d{2,3}_.{7}.gif",
            game_count=0,
        )
    )


def clear_users(users):
    """Delete a list of users"""
    cleared_users = len(users)
    for user in users:
        print("Deleting %s (website: %s)" % (user, user.website))
        user.delete()
    print("Cleared %d users" % cleared_users)


class Command(BaseCommand):
    """Delete all spammers command"""
    def handle(self, *args, **_options):
        """Delete unconfirmed users with a website and no games"""
        clear_users(get_no_games_with_website())
        clear_users(get_spam_avatar_users())
