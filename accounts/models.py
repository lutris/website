import uuid
from django.db import models
from django.contrib.auth.models import User

from accounts import signals


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
