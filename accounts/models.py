import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from tastypie.models import create_api_key


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    from games.models import GameLibrary
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()
        game_library = GameLibrary(user=instance)
        game_library.save()

models.signals.post_save.connect(create_api_key, sender=User)


class Profile(models.Model):
    user = models.OneToOneField(User)
    avatar = models.ImageField(upload_to='avatars', blank=True)
    website = models.URLField(blank=True)

    def __unicode__(self):
        return "%s's profile" % self.user.username


class AuthToken(models.Model):
    user = models.ForeignKey(User)
    ip_address = models.IPAddressField()
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.token = str(uuid.uuid4())
        return super(AuthToken, self).save(*args, **kwargs)
