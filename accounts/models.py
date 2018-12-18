# pylint: disable=no-member
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


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars', blank=True)
    steamid = models.CharField("Steam id", max_length=32, blank=True)
    website = models.URLField(blank=True)
    key = models.CharField(max_length=256, blank=True, default='')
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    @property
    def avatar_url(self):
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
        try:
            user_openid = UserOpenID.objects.get(user=self)
        except UserOpenID.DoesNotExist:
            return False
        except UserOpenID.MultipleObjectsReturned:
            # TODO: Handle properly the case when a user has connected to
            # multiple Steam accounts.
            user_openid = UserOpenID.objects.filter(user=self)[0]
        self.steamid = user_openid.claimed_id.split('/')[-1]

    @staticmethod
    def generate_key():
        # Get a random UUID.
        new_uuid = uuid.uuid4()
        # Hmac that beast.
        return hmac.new(new_uuid.bytes, digestmod=hashlib.sha1).hexdigest()

    def deactivate(self):
        self.gamelibrary.delete()
        self.groups.clear()
        self.authtoken_set.all().delete()
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


class AuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.token = str(uuid.uuid4())
        return super(AuthToken, self).save(force_insert=force_insert, force_update=force_update,
                                           using=using, update_fields=update_fields)


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
        try:
            user = User.objects.get(email=self.email)
        except User.DoesNotExist:
            LOGGER.warning("%s tried to confirm but does not exist", self.email)
            return
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email=self.email).order_by('-id')[0]
        user.email_confirmed = True
        user.save()
