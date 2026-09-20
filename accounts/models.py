"""Models for user accounts"""

# pylint: disable=no-member
import datetime
import hashlib
import hmac
import logging
import os
import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils import timezone

from emails import messages

LOGGER = logging.getLogger(__name__)


class User(AbstractUser):  # pylint: disable=too-many-instance-attributes
    """Model for user accounts"""

    avatar = models.ImageField(upload_to="avatars", blank=True)
    steamid = models.CharField("Steam id", max_length=32, blank=True)
    website = models.URLField(blank=True)
    signup_ip = models.GenericIPAddressField(null=True, blank=True)
    key = models.CharField(max_length=256, blank=True, default="")
    email_confirmed = models.BooleanField(default=False)
    show_adult_content = models.BooleanField(default=False)
    password_setup_notified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

    @property
    def avatar_url(self):
        """Return the local avatar URL or one from Gravatar"""
        if self.avatar:
            return self.avatar.url
        default_url = "https://lutris.net" + settings.STATIC_URL + "images/default-avatar.png"
        size = 64
        return "https://www.gravatar.com/avatar/%s?%s" % (
            hashlib.md5(self.email.encode("utf-8").lower()).hexdigest(),
            urlencode({"d": default_url, "s": str(size)}),
        )

    def set_steamid(self):
        """Set the Steam ID from the allauth social account"""
        from allauth.socialaccount.models import SocialAccount

        try:
            social = SocialAccount.objects.get(user=self, provider="steam")
        except SocialAccount.DoesNotExist:
            return
        except SocialAccount.MultipleObjectsReturned:
            social = SocialAccount.objects.filter(user=self, provider="steam").first()
        self.steamid = social.uid

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
        try:
            self.gamelibrary.delete()
        except ObjectDoesNotExist:
            # Accounts predating the library-on-signup signal have none, and so
            # does an account that has been deactivated once already.
            pass
        self.groups.clear()
        from allauth.socialaccount.models import SocialAccount

        SocialAccount.objects.filter(user=self).delete()
        self.username = hmac.new(uuid.uuid4().bytes, digestmod=hashlib.md5).hexdigest()
        self.set_password(hmac.new(uuid.uuid4().bytes, digestmod=hashlib.sha1).hexdigest())
        self.is_active = False
        self.is_staff = False
        self.email_confirmed = False
        self.email = ""
        self.avatar = ""
        self.steamid = ""
        self.key = ""
        self.save()

    def delete(self, *args, **kwargs):
        """Delete the user along with its avatar"""
        if self.avatar and os.path.exists(self.avatar.path):
            self.avatar.delete()
        return super().delete(*args, **kwargs)


class BannedAccount(models.Model):
    """Record of an account banned for spam.

    ``User.deactivate()`` scrubs the username and email, so this is the only
    lasting record of who was banned and why. It also keeps a banned address
    from simply signing up again.

    The IP is kept for investigation (spotting one actor behind several
    accounts) but is never used to refuse a signup on its own: addresses are
    shared, reassigned and proxied, so blocking one hits bystanders.
    """

    email = models.EmailField(db_index=True)
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="ban_records",
        null=True,
        on_delete=models.SET_NULL,
    )
    banned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="bans_issued",
        null=True,
        on_delete=models.SET_NULL,
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model configuration"""

        ordering = ("-created_at",)
        verbose_name = "Banned account"

    def __str__(self):
        return "%s (%s) banned on %s" % (self.username, self.email, self.created_at)

    @classmethod
    def is_email_banned(cls, email):
        """Whether an email address belongs to a banned account"""
        if not email:
            return False
        return cls.objects.filter(email__iexact=email.strip()).exists()


class EmailConfirmationToken(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def create_token(self):
        self.token = str(uuid.uuid4())

    def get_token_url(self):
        return reverse("user_email_confirm") + "?token=" + self.token

    def send(self, request):
        user = request.user
        confirmation_link = request.build_absolute_uri(self.get_token_url())
        context = {"username": user.username, "confirmation_link": confirmation_link}
        subject = "Confirm your email address"
        messages.send_email("email_confirmation", context, subject, user.email)

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
            user = User.objects.filter(email_confirmed=False, email=self.email).first()
        if not user:
            LOGGER.error("Couldn't find user with email %s", self.email)
            return
        user.email_confirmed = True
        user.save()
