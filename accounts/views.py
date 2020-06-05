"""Module for user account views"""
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
# from django.db.models import Q
from django.http import (Http404, HttpResponseBadRequest,
                         HttpResponseRedirect)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
# from django.views.generic import ListView
# from django.contrib.postgres.search import (
#     SearchQuery,
#     SearchRank,
#     SearchVector
# )
from openid.fetchers import HTTPFetchingError
from django_openid_auth.auth import OpenIDBackend
from django_openid_auth.exceptions import IdentityAlreadyClaimed
from django_openid_auth.views import login_complete, parse_openid_response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from games import models
# from games.forms import LibraryFilterForm
from games.views.pages import GameList

from . import forms, sso, tasks, serializers
from .models import EmailConfirmationToken, User

LOGGER = logging.getLogger(__name__)


def register(request):
    """Register a new user account"""
    form = forms.RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except IntegrityError:
            # We do username validation, so we shouldn't get IntegrityErrors
            # and yet, they still happen from time to time. As a last resort,
            # try to cause panic and havoc.
            messages.error(
                request,
                "OH NO!!!! WHAT HAPPENED!??!?! YOU BROKE EVERYTHING !!"
                "THIS IS BAD BAD BAD.SERIOUSLY, WHAT HAVE YOU DONE ???"
            )
        return HttpResponseRedirect('/')
    return render(request, 'accounts/registration_form.html', {'form': form})


def clear_auth_token(request):
    """Delete the REST API token for the currently logged in user"""
    if not request.user.is_authenticated:
        # Anonymous users fuck off
        return redirect("/")
    try:
        token = Token.objects.get(user=request.user)
    except Token.DoesNotExist:
        raise Http404
    token.delete()
    messages.info(
        request,
        "You authentication token has been cleared. "
        "Please sign-in in Lutris again to generate a new one."
    )
    return redirect(
        reverse('user_account', kwargs={"username": request.user.username})
    )


@login_required
def profile(request):
    """Redirect to user account
    Takes the username from the request, allows to have a unique URL for all
    profiles.
    """
    return HttpResponseRedirect(
        reverse('user_account', args=(request.user.username, ))
    )


def user_account(request, username):
    """Profile view"""
    user = get_object_or_404(User, username=username)
    if request.user.username != username:
        # Once public profiles are implemented, we'll return a view here,
        # currently, only throw a 404.
        raise Http404
    pending_submissions = models.GameSubmission.objects.filter(
        user=user, accepted_at__isnull=True
    )
    accepted_submissions = models.GameSubmission.objects.filter(
        user=user, accepted_at__isnull=False
    )
    return render(request, 'accounts/profile.html', {
        'user': user,
        'pending_submissions': pending_submissions,
        'accepted_submissions': accepted_submissions
    })


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
            'Your account info has been updated.'
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
        return login_complete(request)

    account_url = reverse('user_account', args=(request.user.username, ))
    try:
        openid_response = parse_openid_response(request)
    except HTTPFetchingError:
        messages.warning(
            request,
            "Steam server is unreachable, please try again in a few moments"
        )
        return redirect(account_url)

    if openid_response.status == 'failure':
        messages.warning(request, "Failed to associate Steam account")
        LOGGER.warning("Failed to associate Steam account for %s",
                       request.user.username)
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


@login_required
def steam_disconnect(request):
    """Clears the Steam ID and OpenID key"""
    request.user.useropenid_set.all().delete()
    request.user.steamid = ""
    request.user.save()
    return redirect(reverse("profile"))


class LibraryList(GameList):  # pylint: disable=too-many-ancestors
    """Access the user's game library"""
    template_name = 'accounts/library_show.html'
    context_object_name = 'games'
    paginate_by = 25
    paginate_orphans = 10
    ordering = 'name'

    def get_user(self):
        """Return a user object from the username url segment"""
        try:
            user = User.objects.get(username=self.kwargs['username'])
        except User.DoesNotExist:
            try:
                user = User.objects.get(
                    username__iexact=self.kwargs['username']
                )
            except User.DoesNotExist:
                raise Http404
            except User.MultipleObjectsReturned:
                raise Http404
        return user

    def get_queryset(self):
        user = self.get_user()
        queryset = models.GameLibrary.objects.get(user=user).games.filter(
            is_public=True
        )
        if self.q_params['q']:
            queryset = queryset.order_by('-rank', self.get_ordering())
        else:
            queryset = queryset.order_by(self.get_ordering())
        return self.get_filtered_queryset(queryset)

    # pylint: disable=unused-argument
    def get_context_data(self, *, object_list=None, **kwargs):
        """Display the user's library"""
        context = super(LibraryList, self).get_context_data(
            object_list=object_list, **kwargs
        )
        user = self.get_user()
        if self.request.user != user:
            # Libraries are currently private. This will change once public
            # profiles are implemented
            raise Http404
        context['user'] = user
        context['is_library'] = True
        return context


@login_required
def library_add(request, slug):
    """Add a game to the user's library"""
    user = request.user
    library = models.GameLibrary.objects.get(user=user)
    game = get_object_or_404(models.Game, slug=slug)
    try:
        library.games.add(game)
    except IntegrityError:
        LOGGER.debug('Game already in library')
    return redirect(game.get_absolute_url())


@login_required
def library_remove(request, slug):
    """Remove a game from a user's library"""
    user = request.user
    library = models.GameLibrary.objects.get(user=user)
    game = get_object_or_404(models.Game, slug=slug)
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
    """View used to sign in a user to the Discourse forums"""
    user = request.user
    if not user.email_confirmed:
        return HttpResponseBadRequest(
            'You must confirm your email to use the forums'
        )
    payload = request.GET.get('sso')
    signature = request.GET.get('sig')
    try:
        nonce = sso.validate(payload, signature, settings.DISCOURSE_SSO_SECRET)
    except RuntimeError as ex:
        return HttpResponseBadRequest(ex.args[0])

    url = sso.redirect_url(
        nonce, settings.DISCOURSE_SSO_SECRET, request.user.email,
        request.user.id, request.user.username)
    return redirect(settings.DISCOURSE_URL + url)


class UserDetailView(generics.RetrieveAPIView):
    """Return the information for the currently logged in user"""
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user
