"""Delete spam accounts"""
from django.core.management.base import BaseCommand
from accounts.tasks import clear_spammers


class Command(BaseCommand):
    """Delete all spammers command"""
    def handle(self, *args, **_options):
        """Delete unconfirmed users with a website and no games"""
        clear_spammers()
