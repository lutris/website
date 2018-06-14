"""Module for user account views"""
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django_openid_auth.auth import OpenIDBackend
from django_openid_auth.exceptions import IdentityAlreadyClaimed
from django_openid_auth.views import login_complete, parse_openid_response

import games.models
import games.util.steam
from common.util import get_client_ip

from . import forms, sso, tasks
from .models import AuthToken, EmailConfirmationToken, User

LOGGER = logging.getLogger(__name__)


def register(request):
    """Register a new user account"""
    form = forms.RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return HttpResponseRedirect('/')
    return render(request, 'accounts/registration_form.html', {'form': form})


@csrf_exempt
def client_verify(request):
    """Verify that a token is valid for the current IP"""
    token = request.POST.get('token')
    try:
        auth_token = AuthToken.objects.get(token=token,
                                           ip_address=get_client_ip(request))
        response_data = {'username': auth_token.user.username}
    except AuthToken.DoesNotExist:
        response_data = {'error': 'invalid token'}
    return HttpResponse(json.dumps(response_data),
                        content_type="application/json")


@login_required
def profile(request):
    """Redirect to user account
    Takes the username from the request, allows to have a unique URL for all profiles.
    """
    return HttpResponseRedirect(
        reverse('user_account', args=(request.user.username, ))
    )


def user_account(request, username):
    """Profile view"""
    user = get_object_or_404(User, username=username)
    if request.user.username == username:
        pending_submissions = games.models.GameSubmission.objects.filter(
            user=user, accepted_at__isnull=True
        )
        accepted_submissions = games.models.GameSubmission.objects.filter(
            user=user, accepted_at__isnull=False
        )
        return render(request, 'accounts/profile.html', {
            'user': user,
            'pending_submissions': pending_submissions,
            'accepted_submissions': accepted_submissions
        })
    else:
        # Once public profiles are implemented, we'll return a view here,
        # currently, only throw a 404.
        raise Http404


@login_required
def user_send_confirmation(request):
    """Send an email with a confirmation link"""
    user = request.user
    if not user.email_confirmed:
        token = EmailConfirmationToken(email=user.email)
        token.create_token()
        token.save()
        token.send(request)
    return render(request, 'accounts/confirmation_send.html', {'user': user})


def user_require_confirmation(request):
    """Display an error message that the resource is reserved for confirmed
    accounts only.
    """
    if request.user.is_authenticated:
        messages.error(
            request,
            u"The page you have requested requires that "
            u"you have confirmed your email address."
        )
        return redirect(reverse("user_account", args=(request.user.username,)))
    else:
        login_url = settings.LOGIN_URL
        if 'next' in request.GET:
            login_url += "?next=" + request.GET['next']
        return redirect(login_url)


def user_email_confirm(request):
    """Confirm an user's account

    This is the view pointed by the link in the confirmation email
    """
    token = request.GET.get('token')
    confirmation_token = get_object_or_404(EmailConfirmationToken, token=token)
    if confirmation_token.is_valid():
        confirmation_token.confirm_user()
        confirmation_token.delete()
    return render(request, 'accounts/confirmation_received.html',
                  {'confirmation_token': confirmation_token})


@login_required
def profile_edit(request, username):
    """Change profile imformation"""
    user = get_object_or_404(User, username=username)
    if user != request.user:
        raise Http404
    form = forms.ProfileForm(request.POST or None, request.FILES or None,
                             instance=user)
    if form.is_valid():
        form.save()
        messages.success(
            request,
            'your account info has been updated.'
        )
        return redirect(reverse('user_account', args=(username, )))
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def profile_delete(request, username):
    """Deactivate a user account"""
    user = get_object_or_404(User, username=username)
    if user != request.user:
        raise Http404
    form = forms.ProfileDeleteForm(request.POST or None)
    if form.is_valid():
        logout(request)
        user.deactivate()
        messages.success(request, 'Your account is now deleted')
        return redirect(reverse('homepage'))
    return render(request, 'accounts/profile_delete.html', {'form': form})


@csrf_exempt
def associate_steam(request):
    """Associate a Steam account with a Lutris account"""
    LOGGER.info("Associating Steam user with Lutris account")
    if not request.user.is_authenticated:
        LOGGER.info("User is authenticated, completing login")
        return login_complete(request)
    else:
        openid_response = parse_openid_response(request)
        account_url = reverse('user_account', args=(request.user.username, ))
        if openid_response.status == 'failure':
            messages.warning(request, "Failed to associate Steam account")
            LOGGER.error("Failed to associate Steam account for %s", request.user.username)
            return redirect(account_url)
        openid_backend = OpenIDBackend()
        try:
            openid_backend.associate_openid(request.user, openid_response)
        except IdentityAlreadyClaimed:
            messages.warning(
                request,
                "This Steam account is already claimed by another Lutris "
                "account.\nPlease contact an administrator if you want "
                "to reattribute your Steam account to this current account."
            )
            return redirect(account_url)

        request.user.set_steamid()
        request.user.save()
        return redirect(reverse("library_steam_sync"))


def library_show(request, username):
    """Display the user's library"""
    user = get_object_or_404(User, username=username)
    if request.user != user:
        # Libraries are currently private. This will change once public
        # profiles are implemented
        raise Http404
    library = games.models.GameLibrary.objects.get(user=user)
    library_games = library.games.all()
    return render(request, 'accounts/library_show.html',
                  {'user': user, 'games': library_games,
                   'is_library': True})


@login_required
def library_add(request, slug):
    """Add a game to the user's library"""
    user = request.user
    library = games.models.GameLibrary.objects.get(user=user)
    game = get_object_or_404(games.models.Game, slug=slug)
    try:
        library.games.add(game)
    except IntegrityError:
        LOGGER.debug('Game already in library')
    return redirect(game.get_absolute_url())


@login_required
def library_remove(request, slug):
    """Remove a game from a user's library"""
    user = request.user
    library = games.models.GameLibrary.objects.get(user=user)
    game = get_object_or_404(games.models.Game, slug=slug)
    library.games.remove(game)
    redirect_url = request.META.get('HTTP_REFERER')
    if not redirect_url:
        username = user.username
        redirect_url = reverse('library_show', kwargs={'username': username})
    return redirect(redirect_url)


@login_required
def library_steam_sync(request):
    """Launch a Steam library sync in the background"""
    user = request.user
    LOGGER.info("Syncing contents of Steam library for user %s", user.username)
    tasks.sync_steam_library.delay(user.id)
    messages.success(
        request,
        'Your Steam library is being synced with your Lutris account'
    )
    return redirect(reverse("library_show",
                            kwargs={'username': user.username}))


@login_required
def discourse_sso(request):
    """View used to sign in a user to the Discord forums"""
    user = request.user
    if not user.email_confirmed:
        return HttpResponseBadRequest('You must confirm your email to use the forums')
    payload = request.GET.get('sso')
    signature = request.GET.get('sig')
    try:
        nonce = sso.validate(payload, signature, settings.DISCOURSE_SSO_SECRET)
    except RuntimeError as ex:
        return HttpResponseBadRequest(ex.args[0])

    url = sso.redirect_url(nonce, settings.DISCOURSE_SSO_SECRET, request.user.email,
                           request.user.id, request.user.username)
    return redirect(settings.DISCOURSE_URL + url)
