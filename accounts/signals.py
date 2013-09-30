from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from tastypie.models import create_api_key
from accounts import models as accounts_models


@receiver(post_save, sender=accounts_models.User)
def create_profile(sender, instance, created, **kwargs):
    from games.models import GameLibrary
    if created:
        game_library = GameLibrary(user=instance)
        game_library.save()


models.signals.post_save.connect(create_api_key, sender=accounts_models.User)
