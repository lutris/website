# pylint: disable=W0613
import logging
from django.db.models.signals import post_save
from django.db import models
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

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
        body = "Hello %s!\n Your account is now active." % instance.username
        send_mail("Welcome to lutris.net", body, settings.DEFAULT_FROM_EMAIL,
                  [instance.email])

models.signals.post_save.connect(create_api_key, sender=account_models.User)
