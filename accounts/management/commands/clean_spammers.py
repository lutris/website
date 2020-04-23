"""Delete spam accounts"""
from django.core.management.base import BaseCommand
from accounts.spam_control import clear_users, get_no_games_with_website, get_spam_avatar_users


class Command(BaseCommand):
    """Delete all spammers command"""
    def handle(self, *args, **_options):
        """Delete unconfirmed users with a website and no games"""
        clear_users(get_no_games_with_website())
        clear_users(get_spam_avatar_users())
