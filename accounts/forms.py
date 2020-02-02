"""Account management handling forms"""
# pylint: disable=W0232, R0903
import logging

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from rest_framework.authtoken.models import Token

from accounts.models import User
from common.forms import get_bootstrap_helper

LOGGER = logging.getLogger(__name__)


class RegistrationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """

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
            "invalid": (
                "This value may contain only letters, numbers and "
                "@/./+/-/_ characters."
            )
        },
    )
    email = forms.EmailField(label="Email address")
    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput, max_length=64
    )
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

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.helper = get_bootstrap_helper(
            ["username", "email", "password1", "password2"], "register", "Register"
        )

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
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        Token.objects.create(user=user)
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = get_bootstrap_helper(
            ["username", "password"], "signin", "Sign in"
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("website", "avatar", "email")

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.helper = get_bootstrap_helper(list(self.Meta.fields), "save", "Save")

    def save(self, commit=True):
        if "email" in self.changed_data:
            self.instance.email_confirmed = False
        return super(ProfileForm, self).save(commit=commit)


class ProfileDeleteForm(forms.Form):
    confirm_delete = forms.BooleanField(
        label="Yes, I confirm I want to delete my account"
    )

    def clean_confirm_delete(self):
        confirm_delete = self.cleaned_data["confirm_delete"]
        if not confirm_delete:
            raise forms.ValidationError("You must confirm to delete your account")
        return confirm_delete
