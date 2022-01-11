"""Models for user accounts"""
# pylint: disable=no-member
import os
import datetime
import hashlib
import hmac
import logging
import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_openid_auth.models import UserOpenID

from emails import messages

LOGGER = logging.getLogger(__name__)


class User(AbstractUser):  # pylint: disable=too-many-instance-attributes
    """Model for user accounts"""
    avatar = models.ImageField(upload_to='avatars', blank=True)
    steamid = models.CharField("Steam id", max_length=32, blank=True)
    website = models.URLField(blank=True)
    key = models.CharField(max_length=256, blank=True, default='')
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    @property
    def avatar_url(self):
        """Return the local avatar URL or one from Gravatar"""
        if self.avatar:
            return self.avatar.url
        default_url = "https://lutris.net" + settings.STATIC_URL + "images/default-avatar.png"
        size = 64
        return (
            "https://www.gravatar.com/avatar/%s?%s" % (
                hashlib.md5(self.email.encode('utf-8').lower()).hexdigest(),
                urlencode({'d': default_url, 's': str(size)})
            )
        )

    def set_steamid(self):
        """Set the Steam ID from the OpenID auth"""
        try:
            user_openid = UserOpenID.objects.get(user=self)
        except UserOpenID.DoesNotExist:
            return
        except UserOpenID.MultipleObjectsReturned:
            # TODO: Handle properly the case when a user has connected to
            # multiple Steam accounts.
            user_openid = UserOpenID.objects.filter(user=self)[0]
        self.steamid = user_openid.claimed_id.split('/')[-1]

    @staticmethod
    def generate_key():
        """Return a random key"""
        # Get a random UUID.
        new_uuid = uuid.uuid4()
        # Hmac that beast.
        return hmac.new(new_uuid.bytes, digestmod=hashlib.sha1).hexdigest()

    def deactivate(self):
        """Deactivate a user
        Leaves the user intact while suppressing any identifying information"""
        self.gamelibrary.delete()
        self.groups.clear()
        self.useropenid_set.all().delete()
        self.username = hmac.new(uuid.uuid4().bytes, digestmod=hashlib.md5).hexdigest()
        self.set_password(hmac.new(uuid.uuid4().bytes, digestmod=hashlib.sha1).hexdigest())
        self.is_active = False
        self.is_staff = False
        self.email_confirmed = False
        self.email = ''
        self.avatar = ''
        self.steamid = ''
        self.key = ''
        self.save()

    def delete(self, *args, **kwargs):
        """Delete the user along with its avatar"""
        if self.avatar and os.path.exists(self.avatar.path):
            self.avatar.delete()
        return super().delete(*args, **kwargs)


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
        context = {
            'username': user.username,
            'confirmation_link': confirmation_link
        }
        subject = 'Confirm your email address'
        messages.send_email('email_confirmation', context, subject, user.email)

    def is_valid(self):
        return self.created_at > timezone.now() - datetime.timedelta(days=3)

    def confirm_user(self):
        """Confirm a user account"""
        try:
            user = User.objects.get(email=self.email)
        except User.DoesNotExist:
            LOGGER.warning("%s tried to confirm but does not exist", self.email)
            return
        except User.MultipleObjectsReturned:
            user = User.objects.filter(
                email_confirmed=False,
                email=self.email
            ).first()
        user.email_confirmed = True
        user.save()
