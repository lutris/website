import uuid
import hmac
import datetime
import logging
import urllib
import hashlib
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django_openid_auth.models import UserOpenID

from emails import messages

LOGGER = logging.getLogger(__name__)


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars', blank=True)
    steamid = models.CharField("Steam id", max_length=32, blank=True)
    website = models.URLField(blank=True)
    key = models.CharField(max_length=256, blank=True, default='')
    email_confirmed = models.BooleanField(default=False)

    def __unicode__(self):
        return self.username

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        default_url = settings.STATIC_URL + "images/default-avatar.png"
        size = 64
        return (
            "https://www.gravatar.com/avatar/" +
            hashlib.md5(self.email.encode('utf-8').lower()).hexdigest() + "?" +
            urllib.urlencode({'d': default_url, 's': str(size)})
        )

    def set_steamid(self):
        try:
            user_openid = UserOpenID.objects.get(user=self)
        except UserOpenID.DoesNotExist:
            return False
        except UserOpenID.MultipleObjectsReturned:
            # TODO: Handle properly the case when a user has connected to
            # multiple Steam accounts.
            user_openid = UserOpenID.objects.filter(user=self)[0]
        self.steamid = user_openid.claimed_id.split('/')[-1]

    def generate_key(self):
        """API key generation from TastyPie"""
        # Get a random UUID.
        new_uuid = uuid.uuid4()
        # Hmac that beast.
        return hmac.new(new_uuid.bytes, digestmod=hashlib.sha1).hexdigest()


class AuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    ip_address = models.GenericIPAddressField()
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.token = str(uuid.uuid4())
        return super(AuthToken, self).save(*args, **kwargs)


class EmailConfirmationToken(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def create_token(self):
        self.token = str(uuid.uuid4())

    def get_token_url(self):
        return reverse('user_email_confirm') + '?token=' + self.token

    def send(self, request):
        user = request.user
        confirmation_link = request.build_absolute_uri(self.get_token_url())
        messages.send_confirmation_link(user, confirmation_link)

    def is_valid(self):
        return self.created_at > timezone.now() - datetime.timedelta(days=3)

    def confirm_user(self):
        try:
            user = User.objects.get(email=self.email)
        except User.DoesNotExist:
            LOGGER.error("%s tried to confirm but does not exist", self.email)
            return
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email=self.email).order_by('-id')[0]
        user.email_confirmed = True
        user.save()
