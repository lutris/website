"""Module for user account views"""
# pylint: disable=too-many-ancestors,raise-missing-from
import logging
from collections import defaultdict
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LogoutView,
    LoginView,
    PasswordResetDoneView,
    PasswordResetView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetConfirmView,
)
from django.views.generic import ListView
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from openid.fetchers import HTTPFetchingError
from django_openid_auth.auth import OpenIDBackend
from django_openid_auth.models import UserOpenID
from django_openid_auth.exceptions import IdentityAlreadyClaimed
from django_openid_auth.views import login_complete, parse_openid_response

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from games import models
from . import forms, sso, tasks, serializers
from .models import EmailConfirmationToken, User

LOGGER = logging.getLogger(__name__)


class LutrisRegisterView(CreateView):
    """Account registration view"""

    form_class = forms.RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("homepage")


class LutrisLoginView(LoginView):
    """Sign in view"""

    template_name = "accounts/login.html"
    authentication_form = AuthenticationForm


class LutrisLogoutView(LogoutView):
    """Sign out view"""

    next_page = "/"

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You are now logged out of Lutris.")
        return super().dispatch(request, *args, **kwargs)


class LutrisPasswordResetView(PasswordResetView):
    """View to reset a user's password"""

    template_name = "accounts/password_reset.html"
    form_class = PasswordResetForm


class LutrisPasswordResetDoneView(PasswordResetDoneView):
    """Tell the user an email has been sent with a password reset link"""

    template_name = "accounts/password_reset_done.html"


class LutrisPasswordChangeView(PasswordChangeView):
    """View confirming the password reset is sent"""

    template_name = "accounts/password_change.html"


class LutrisPasswordChangeDoneView(PasswordChangeDoneView):
    """View confirming the password was changed"""

    template_name = "accounts/password_change_done.html"


class LutrisPasswordResetConfirmView(PasswordResetConfirmView):
    """View where the user confirms the password reset"""

    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been updated.")
        return super().form_valid(form)


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
        "Please sign-in in Lutris again to generate a new one.",
    )
    return redirect(reverse("user_account", kwargs={"username": request.user.username}))


@login_required
def profile(request):
    """Redirect to user account
    Takes the username from the request, allows to have a unique URL for all profiles.
    """
    return HttpResponseRedirect(reverse("user_account", args=(request.user.username,)))


def user_account(request, username):
    """Profile view"""
    if request.user.username != username:
        raise Http404
    return render(
        request,
        "accounts/profile.html",
        {"user": request.user, "profile_page": "profile"},
    )


@login_required
def user_submissions(request):
    """Lists a user game submissions"""
    pending_submissions = models.GameSubmission.objects.filter(
        user=request.user, accepted_at__isnull=True
    )
    accepted_submissions = models.GameSubmission.objects.filter(
        user=request.user, accepted_at__isnull=False
    )
    return render(
        request,
        "accounts/game_submissions.html",
        {
            "pending_submissions": pending_submissions,
            "accepted_submissions": accepted_submissions,
        },
    )


@login_required
def user_send_confirmation(request):
    """Send an email with a confirmation link"""
    user = request.user
    if user.email_confirmed:
        messages.info(request, "Your email has already been confirmed.")
        return HttpResponseRedirect(reverse("user_account", args=(user.username,)))
    token = EmailConfirmationToken(email=user.email)
    token.create_token()
    token.save()
    token.send(request)
    messages.info(
        request,
        "An email with a confirmation link has been sent to the specified "
        "address. Click the link to confirm your email address.",
    )
    return HttpResponseRedirect(reverse("user_account", args=(user.username,)))


def user_require_confirmation(request):
    """Display an error message that the resource is reserved for confirmed
    accounts only.
    """
    if request.user.is_authenticated:
        messages.error(
            request,
            "The page you have requested requires that "
            "you have confirmed your email address.",
        )
        return redirect(reverse("user_account", args=(request.user.username,)))
    login_url = settings.LOGIN_URL
    if "next" in request.GET:
        login_url += "?next=" + request.GET["next"]
    return redirect(login_url)


def user_email_confirm(request):
    """Confirm an user's account

    This is the view pointed by the link in the confirmation email
    """
    token = request.GET.get("token")
    confirmation_token = get_object_or_404(EmailConfirmationToken, token=token)
    if confirmation_token.is_valid():
        confirmation_token.confirm_user()
        confirmation_token.delete()
    return render(
        request,
        "accounts/confirmation_received.html",
        {"confirmation_token": confirmation_token},
    )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Edit the user's profile info"""

    template_name = "accounts/profile_edit.html"
    form_class = forms.ProfileForm
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, *args, **kwargs):  # pylint: disable=arguments-differ
        context = super().get_context_data(*args, **kwargs)
        context["profile_page"] = "edit"
        return context


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
        messages.success(request, "Your account is now deleted")
        return redirect(reverse("homepage"))
    return render(request, "accounts/profile_delete.html", {"form": form})


@csrf_exempt
def associate_steam(request):
    """Associate a Steam account with a Lutris account"""
    LOGGER.info("Associating Steam user with Lutris account")
    if not request.user.is_authenticated:
        return login_complete(request)

    account_url = reverse("user_account", args=(request.user.username,))
    try:
        openid_response = parse_openid_response(request)
    except HTTPFetchingError:
        messages.warning(
            request, "Steam server is unreachable, please try again in a few moments"
        )
        return redirect(account_url)

    if openid_response.status == "failure":
        messages.warning(request, "Failed to associate Steam account")
        LOGGER.warning(
            "Failed to associate Steam account for %s", request.user.username
        )
        return redirect(account_url)
    openid_backend = OpenIDBackend()
    try:
        openid_backend.associate_openid(request.user, openid_response)
    except IdentityAlreadyClaimed:
        other_open_id = UserOpenID.objects.get(
            claimed_id__exact=openid_response.identity_url
        )
        other_open_id.delete()
        openid_backend.associate_openid(request.user, openid_response)
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


class LibraryList(ListView):  # pylint: disable=too-many-ancestors
    """Access the user's game library"""

    template_name = "accounts/library_list.html"
    context_object_name = "games"
    ordering = "name"
    profile_page = "library"
    paginate_by = 30

    def get_user(self):
        """Return a user object from the username url segment"""
        try:
            user = User.objects.get(username=self.kwargs["username"])
        except User.DoesNotExist:
            try:
                user = User.objects.get(username__iexact=self.kwargs["username"])
            except User.DoesNotExist:
                raise Http404
            except User.MultipleObjectsReturned:
                raise Http404
        return user

    def get_queryset(self):
        """Return all games in library, optionally filter them"""
        queryset = models.LibraryGame.objects.filter(gamelibrary__user=self.get_user())
        if self.request.GET.get("q"):
            queryset = queryset.filter(name__icontains=self.request.GET["q"])
        return queryset.order_by(self.request.GET.get("sort", self.ordering))

    def get_context_data(self, *, object_list=None, **kwargs):  # pylint: disable=unused-argument
        """Display the user's library"""
        context = super().get_context_data(object_list=object_list, **kwargs)
        user = self.get_user()
        if self.request.user != user:
            # Libraries are currently private. This will change once public
            # profiles are implemented
            raise Http404
        context["user"] = user
        context["profile_page"] = self.profile_page
        context["q"] = self.request.GET.get("q", "")
        context["sort"] = self.request.GET.get("sort", "")
        return context


class SubmissionList(LibraryList):  # pylint: disable=too-many-ancestors
    """List all user submissions"""

    template_name = "accounts/submission_list.html"
    context_object_name = "submissions"
    ordering = "-created_at"
    profile_page = "submissions"

    def get_queryset(self):
        """Return all submitted games"""
        queryset = models.GameSubmission.objects.filter(user=self.get_user())
        if self.request.GET.get("q"):
            queryset = queryset.filter(game__name__icontains=self.request.GET["q"])
        return queryset.order_by(self.request.GET.get("sort", self.ordering))


@login_required
def installer_list(request, username):
    """List all private installers"""
    if username != request.user.username:
        raise Http404

    installers = models.InstallerDraft.objects.filter(user=request.user)
    if request.GET.get("q"):
        installers = installers.filter(game__name__icontains=request.GET["q"])
    installers = installers.order_by(request.GET.get("sort", "-created_at"))
    return render(
        request,
        "accounts/installer_list.html",
        {"user": request.user, "profile_page": "installers", "installers": installers},
    )


@login_required
def library_add(request, slug):
    """Add a game to the user's library"""
    library = models.GameLibrary.objects.get(user=request.user)
    game = get_object_or_404(models.Game, slug=slug)
    models.LibraryGame.objects.create(
        name=game.name,
        slug=game.slug,
        game=game,
        gamelibrary=library,
    )
    return redirect(game.get_absolute_url())


@login_required
def library_remove(request, pk):
    """Remove a game from a user's library"""
    gamelibrary = models.GameLibrary.objects.get(user=request.user)
    library_game = get_object_or_404(models.LibraryGame, pk=pk)
    if library_game.gamelibrary != gamelibrary:
        response = HttpResponse("smartass")
        response.status_code = 418
        return response
    library_game.delete()
    redirect_url = request.META.get("HTTP_REFERER")
    if not redirect_url:
        redirect_url = reverse(
            "library_list", kwargs={"username": request.user.username}
        )
    return redirect(redirect_url)


@login_required
def library_steam_sync(request):
    """Launch a Steam library sync in the background"""
    user = request.user
    LOGGER.info("Syncing contents of Steam library for user %s", user.username)
    tasks.sync_steam_library.delay(user.id)
    messages.success(
        request, "Your Steam library is being synced with your Lutris account"
    )
    return redirect(reverse("library_list", kwargs={"username": user.username}))


@login_required
def discourse_sso(request):
    """View used to sign in a user to the Discourse forums"""
    if not request.user.email_confirmed:
        return HttpResponseBadRequest("You must confirm your email to use the forums")
    payload = request.GET.get("sso")
    signature = request.GET.get("sig")
    try:
        nonce = sso.validate(payload, signature, settings.DISCOURSE_SSO_SECRET)
    except RuntimeError as ex:
        return HttpResponseBadRequest(ex.args[0])

    url = sso.redirect_url(
        nonce,
        settings.DISCOURSE_SSO_SECRET,
        request.user.email,
        request.user.id,
        request.user.username,
    )
    return redirect(settings.DISCOURSE_URL + url)


class UserDetailView(generics.RetrieveAPIView):
    """Return the information for the currently logged in user"""

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user


class GameLibraryAPIView(generics.ListCreateAPIView):
    """List a user's library"""

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LibrarySerializer
    pagination_class = None

    def get_queryset(self):
        return (
            models.LibraryGame.objects.prefetch_related("game")
            .filter(gamelibrary__user=self.request.user)
            .order_by("game__slug")
        )

    def is_empty_key(self, key):
        """Return true if runner, platform, service are empty"""
        return not key[1] and not key[2] and not key[3]

    def post(self, request, *args, **kwargs):
        client_library = defaultdict(list)
        for game in request.data:
            client_library[game["slug"]].append(game)
        stored_library = self.get_queryset()
        updated_games = set()
        stats = {"updated": 0, "created": 0, "errors": 0}
        for game in stored_library:
            if game.get_slug() in client_library:
                client_games = client_library[game.get_slug()]
                stored_key = (game.get_slug(), game.runner, game.platform, game.service)
                for client_game in client_games:
                    client_key = (
                        client_game["slug"],
                        client_game["runner"],
                        client_game["platform"],
                        client_game["service"],
                    )
                    if client_key == stored_key or self.is_empty_key(stored_key):
                        game.slug = client_game["slug"]
                        game.name = client_game["name"]
                        game.runner = client_game["runner"]
                        game.platform = client_game["platform"]
                        client_lastplayed = client_game["lastplayed"] or 0
                        if not game.lastplayed or game.lastplayed > client_lastplayed:
                            game.lastplayed = client_game["lastplayed"] or 0
                        client_playtime = client_game["playtime"] or 0
                        if not game.playtime or game.playtime < client_playtime:
                            game.playtime = client_playtime
                        if client_game["service"]:
                            game.service = client_game["service"]
                            game.service_id = client_game["service_id"]
                        game.save()
                        stored_key = client_key
                        updated_games.add(stored_key)
                        stats["updated"] += 1
        for slug in client_library:
            client_games = client_library[slug]
            for client_game in client_games:
                client_key = (
                    client_game["slug"],
                    client_game["runner"],
                    client_game["platform"],
                    client_game["service"],
                )
                if client_key in updated_games:
                    continue
                try:
                    game = models.Game.objects.get(slug=client_game["slug"])
                except models.Game.DoesNotExist:
                    game = None
                try:
                    models.LibraryGame.objects.create(
                        game=game,
                        name=client_game["name"],
                        slug=client_game["slug"],
                        gamelibrary=models.GameLibrary.objects.get(user=request.user),
                        playtime=client_game["playtime"] or 0,
                        runner=client_game["runner"],
                        platform=client_game["platform"],
                        service=client_game["service"],
                        lastplayed=client_game["lastplayed"] or 0,
                    )
                    stats["created"] += 1
                    LOGGER.info("Create new Library game %s", client_game["slug"])
                except Exception as ex:
                    LOGGER.error(
                        "Failed to create new Library game %s: %s", client_game["slug"], ex
                    )
                    stats["errors"] += 1
        return self.get(request)