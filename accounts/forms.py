"""Account management handling forms"""

# pylint: disable=no-member
import logging
import unicodedata

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.db import IntegrityError, transaction
from rest_framework.authtoken.models import Token

from accounts.models import User

LOGGER = logging.getLogger(__name__)


class RegistrationForm(forms.ModelForm):
    """Form to create a new user from a given username and password."""

    error_messages = {
        "duplicate_username": "A user with that username already exists.",
        "password_mismatch": "The two password fields didn't match.",
    }
    username = forms.RegexField(
        label="Username",
        max_length=30,
        regex=r"^[\w.@+-]+$",
        help_text=("30 characters max."),
        error_messages={
            "invalid": ("This value may contain only letters, numbers and @/./+/-/_ characters.")
        },
    )
    email = forms.EmailField(label="Email address")
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, max_length=64)
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        max_length=64,
        help_text="Enter the same password as above, for verification.",
    )

    class Meta:
        """Model and field definitions"""

        model = User
        fields = ("username", "email")

    def clean_email(self):
        """Users with a 'hotmails.com email are not legit'"""
        email = self.cleaned_data["email"]
        if email.endswith("hotmails.com"):
            raise forms.ValidationError("lol :)")
        return email

    def clean_username(self):
        """Check that no similar username exist in a case insensitive way"""
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return username
        except User.MultipleObjectsReturned:
            LOGGER.warning("Mutiple users with username: %s", username)
        raise forms.ValidationError(self.error_messages["duplicate_username"])

    def clean_password2(self):
        """Check that passwords match"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(self.error_messages["password_mismatch"])
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            try:
                user.save()
            except IntegrityError:
                return user
        Token.objects.create(user=user)
        return user


class ProfileForm(forms.ModelForm):
    """Form to edit profile information"""

    class Meta:
        """ModelForm configuration"""

        model = User
        fields = ("email", "show_adult_content")
        help_texts = {
            "show_adult_content": "Display adult content in Lutris searches. Only enable this if you are legally authorized to view this type of content in your country."
        }

    def save(self, commit=True):
        update_fields = list(self.changed_data)
        if "email" in self.changed_data:
            self.instance.email_confirmed = False
            update_fields.append("email_confirmed")
        self.instance = super().save(commit=False)
        if commit and update_fields:
            self.instance.save(update_fields=update_fields)
        return self.instance


class ProfileDeleteForm(forms.Form):
    """Form to ask confirmation for account deletion"""

    confirm_delete = forms.BooleanField(label="Yes, I confirm I want to delete my account")

    def clean_confirm_delete(self):
        """Only delete if the user has checked the corresponding checkbox"""
        confirm_delete = self.cleaned_data["confirm_delete"]
        if not confirm_delete:
            raise forms.ValidationError("You must confirm to delete your account")
        return confirm_delete


class LutrisPasswordResetForm(PasswordResetForm):
    """Password reset that also serves users without a usable password.

    Django's default form silently drops users with set_unusable_password(),
    i.e. accounts created via social login (Discord, Google, Steam). Those
    users would never receive a reset email and could not set a password,
    blocking them from signing in to the desktop client.
    """

    def get_users(self, email):
        user_model = get_user_model()
        email_field = user_model.get_email_field_name()
        active_users = user_model._default_manager.filter(
            **{f"{email_field}__iexact": email, "is_active": True}
        )
        return (u for u in active_users if _email_ci_equal(email, getattr(u, email_field)))


def _email_ci_equal(s1, s2):
    """Case-insensitive Unicode-normalized email comparison (UTR 36)."""
    return (
        unicodedata.normalize("NFKC", s1).casefold() == unicodedata.normalize("NFKC", s2).casefold()
    )


class SetUsernameAndPasswordForm(SetPasswordForm):
    """Set an initial password and (optionally) rename the account.

    Used only on the set-password flow for social-signup users whose username
    was auto-generated by allauth. After they save here they have a usable
    password, so this view becomes inaccessible and the rename is effectively
    one-shot.
    """

    username = forms.RegexField(
        label="Username",
        max_length=30,
        regex=r"^[\w.@+-]+$",
        help_text="30 characters max. Letters, digits and @/./+/-/_ only.",
        error_messages={
            "invalid": "This value may contain only letters, numbers and @/./+/-/_ characters."
        },
    )

    field_order = ("username", "new_password1", "new_password2")

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["username"].initial = user.username

    def clean_username(self):
        username = self.cleaned_data["username"]
        if username == self.user.username:
            return username
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def save(self, commit=True):
        with transaction.atomic():
            user = super().save(commit=False)
            user.username = self.cleaned_data["username"]
            if commit:
                user.save()
        return user
