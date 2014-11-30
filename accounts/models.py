import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django_openid_auth.models import UserOpenID


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars', blank=True)
    steamid = models.CharField("Steam id", max_length=32, blank=True)
    website = models.URLField(blank=True)

    @property
    def avatar_url(self):
        if self.avatar:
            url = self.avatar.url
        else:
            url = settings.STATIC_URL + "images/default-avatar.png"
        return url

    def set_steamid(self):
        try:
            user_openid = UserOpenID.objects.get(user=self)
        except UserOpenID.DoesNotExist:
            return False
        self.steamid = user_openid.claimed_id.split('/')[-1]


class AuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    ip_address = models.IPAddressField()
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.token = str(uuid.uuid4())
        return super(AuthToken, self).save(*args, **kwargs)
