"""Custom authentication backends"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class SmarterModelBackend(ModelBackend):
    """Authentication backend that is less moronic that the default Django one"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Avoids being a complete dick to users by fetching usernames case insensitively"""
        UserModel = get_user_model()  # pylint: disable=invalid-name
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            case_insensitive_username_field = '{}__iexact'.format(UserModel.USERNAME_FIELD)
            user = UserModel._default_manager.get(  # pylint: disable=protected-access
                **{case_insensitive_username_field: username}
            )
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
