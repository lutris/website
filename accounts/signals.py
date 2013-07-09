from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import User
from tastypie.models import create_api_key


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    from games.models import GameLibrary
    from accounts.models import Profile
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()
        game_library = GameLibrary(user=instance)
        game_library.save()


models.signals.post_save.connect(create_api_key, sender=User)
