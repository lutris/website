"""Account management handling forms"""
import logging

from django import forms
from django.db import IntegrityError

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
            except IntegrityError as ex:
                LOGGER.error("Integrity error while saving %s: %s", user, ex)
                return user
        Token.objects.create(user=user)
        return user

class ProfileForm(forms.ModelForm):
    """Form to edit profile information"""

    class Meta:
        """ModelForm configuration"""
        model = User
        fields = ("website", "avatar", "email")

    def save(self, commit=True):
        if "email" in self.changed_data:
            self.instance.email_confirmed = False
        return super().save(commit=commit)


class ProfileDeleteForm(forms.Form):
    """Form to ask confirmation for account deletion"""
    confirm_delete = forms.BooleanField(
        label="Yes, I confirm I want to delete my account"
    )

    def clean_confirm_delete(self):
        """Only delete if the user has checked the corresponding checkbox"""
        confirm_delete = self.cleaned_data["confirm_delete"]
        if not confirm_delete:
            raise forms.ValidationError("You must confirm to delete your account")
        return confirm_delete
