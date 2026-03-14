"""Custom allauth adapters for Lutris"""

import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)


class LutrisAccountAdapter(DefaultAccountAdapter):
    """Prevent allauth from handling signup — Lutris has its own registration."""

    def is_open_for_signup(self, request):
        return False


class LutrisSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Handle social login integration for Steam, Discord, Google."""

    def is_open_for_signup(self, request, sociallogin):
        return True

    def pre_social_login(self, request, sociallogin):
        """Connect social account to existing user if possible."""
        if sociallogin.is_existing:
            return

        user = None

        # For Steam, match by steamid field
        if sociallogin.account.provider == "steam":
            from accounts.models import User

            try:
                user = User.objects.get(steamid=sociallogin.account.uid)
            except User.DoesNotExist:
                pass

        # For providers with email, match by email
        if sociallogin.account.provider in ("discord", "google"):
            email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else None
            if email:
                from accounts.models import User

                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    pass

        if user:
            sociallogin.connect(request, user)

    def on_authentication_error(
        self, request, provider_id, error=None, exception=None, extra_context=None
    ):
        from allauth.socialaccount.providers.base import AuthError

        if error == AuthError.CANCELLED:
            logger.info("Social login cancelled for %s", provider_id)
        else:
            logger.warning(
                "Social login error for %s: error=%s exception=%s",
                provider_id,
                error,
                exception,
                exc_info=exception,
            )
        return super().on_authentication_error(
            request, provider_id, error=error, exception=exception, extra_context=extra_context
        )

    def save_user(self, request, sociallogin, form=None):
        """After saving social user, set the steamid field if Steam."""
        user = super().save_user(request, sociallogin, form)
        if sociallogin.account.provider == "steam":
            user.steamid = sociallogin.account.uid
            user.save(update_fields=["steamid"])
        return user
