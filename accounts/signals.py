# pylint: disable=W0613
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from tastypie.models import create_api_key

from . import models
from emails import messages

LOGGER = logging.getLogger(__name__)


@receiver(post_save, sender=models.User)
def create_library(sender, instance, created, **kwargs):
    from games.models import GameLibrary
    if created:
        game_library = GameLibrary(user=instance)
        game_library.save()


@receiver(post_save, sender=models.User)
def send_registration_email(sender, instance, created, **kwargs):
    if created:
        token = models.EmailConfirmationToken(email=instance.email)
        token.create_token()
        token.save()
        messages.send_account_creation(instance, token.get_token_url())

post_save.connect(create_api_key, sender=models.User)
