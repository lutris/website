"""Custom authentication backends"""
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

LOGGER = logging.getLogger(__name__)


class SmarterModelBackend(ModelBackend):
    """
    Authentication backend that is less moronic that the default Django one
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Avoids being a complete dick to users by fetching usernames case
        insensitively
        """
        UserModel = get_user_model()  # pylint: disable=invalid-name
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            case_insensitive_username_field = '{}__iexact'.format(
                UserModel.USERNAME_FIELD)
            # pylint: disable=protected-access
            user = UserModel._default_manager.get(
                **{case_insensitive_username_field: username}
            )
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        except UserModel.MultipleObjectsReturned:
            # Usernames are migrated to be case insensitive but some existing
            # users will have duplicate usernames when all converted to
            # lowercase. If that's the case, try logging in the user with a
            # case sensitive password.
            return self.case_sensitive_authenticate(username, password)
        else:
            if (
                    user.check_password(password) and
                    self.user_can_authenticate(user)
               ):
                return user

    def case_sensitive_authenticate(self, username, password):
        """Tries to authenticate any user with the username exactly as given
        This should resolve most issues regarding duplicate usernames.
        """
        LOGGER.info("Duplicate username %s", username)
        UserModel = get_user_model()  # pylint: disable=invalid-name
        try:
            # pylint: disable=protected-access
            user = UserModel._default_manager.get(
                username=username
            )
        except UserModel.DoesNotExist:
            return
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
