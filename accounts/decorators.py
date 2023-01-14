"""Account related function decorator, mostly used for permission handling"""
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy


def user_confirmed_required(function):
    """Require that a user is logged in and has confirmed their email address"""
    decorator = user_passes_test(
        lambda u: u.is_authenticated and u.email_confirmed,
        login_url=reverse_lazy("user_require_confirmation"),
        redirect_field_name=REDIRECT_FIELD_NAME
    )
    return decorator(function)
