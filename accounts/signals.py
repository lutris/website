import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from tastypie.models import create_api_key
from accounts import models as account_models
LOGGER = logging.getLogger(__name__)


@receiver(post_save, sender=account_models.User)
def create_library(sender, instance, created, **kwargs):
    LOGGER.info("Creating library for %s", instance)
    from games.models import GameLibrary
    if created:
        game_library = GameLibrary(user=instance)
        game_library.save()


@receiver(post_save, sender=account_models.User)
def send_registration_email(sender, instance, created, **kwargs):
    LOGGER.info("Sending registration email for %s", instance)
    if created:
        print instance.email

models.signals.post_save.connect(create_api_key, sender=account_models.User)
