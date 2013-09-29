import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars', blank=True)
    steamid = models.CharField("Steam id", max_length=32, blank=True)
    website = models.URLField(blank=True)

    def get_avatar_url(self):
        return "/media/avatar.png"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    def __unicode__(self):
        return "%s's profile" % self.user.username


class AuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    ip_address = models.IPAddressField()
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.token = str(uuid.uuid4())
        return super(AuthToken, self).save(*args, **kwargs)
