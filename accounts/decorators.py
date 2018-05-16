from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils.decorators import available_attrs

from games.models import Game, Installer


def user_confirmed_required(function):
    """Require that a user is logged in and has confirmed their email address"""
    decorator = user_passes_test(
        lambda u: u.is_authenticated and u.email_confirmed,
        login_url=reverse_lazy("user_require_confirmation"),
        redirect_field_name=REDIRECT_FIELD_NAME
    )
    return decorator(function)


def can_edit_installer(slug=None, is_game=False):
    if not slug:
        return False
    game = None
    if not is_game:
        try:
            installer = Installer.objects.get(slug=slug)
        except Installer.DoesNotExist:
            return True
        game = installer.game
    else:
        try:
            game = Game.objects.get(slug=slug)
        except Game.DoesNotExist:
            return True
    if not game:
        return True
    return not bool(game.flags.protected)


def check_installer_restrictions(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        slug = kwargs.get('slug')
        if request.user.is_staff or can_edit_installer(slug, is_game=request.path.endswith('new')):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied("Installers are protected")
    return _wrapped_view
