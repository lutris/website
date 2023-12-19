"""Accounts related signals"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from emails import messages

from . import models

LOGGER = logging.getLogger(__name__)


@receiver(post_save, sender=models.User)
def create_library(sender, instance, created, **_kwargs):  # pylint: disable=unused-argument
    """Create a new game library for new users"""
    from games.models import GameLibrary
    if created:
        game_library = GameLibrary(user=instance)
        game_library.save()


@receiver(post_save, sender=models.User)
def send_registration_email(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """Send a confirmation email after user creation"""
    if created:
        token = models.EmailConfirmationToken(email=instance.email)
        token.create_token()
        token.save()
        result = messages.send_account_creation(instance, token.get_token_url())
        if not result:
            LOGGER.warning("Error sending confirmation email. Deleting token")
            token.delete()
