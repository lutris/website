"""Views for lutris main app"""
# pylint: disable=too-many-ancestors
from __future__ import absolute_import

import json
import logging

import reversion
from reversion.models import Version
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from sorl.thumbnail import get_thumbnail

from accounts.decorators import check_installer_restrictions, user_confirmed_required
from games import models
from games.forms import (
    ForkInstallerForm,
    GameEditForm,
    GameForm,
    InstallerEditForm,
    InstallerForm,
    ScreenshotForm,
)
from games.models import Game, GameSubmission, Installer, InstallerIssue
from games.util.pagination import get_page_range
from games.webhooks import notify_issue_creation, notify_installer
from emails.messages import send_email
from platforms.models import Platform

LOGGER = logging.getLogger(__name__)


class GameList(ListView):
    """Game list view"""

    model = models.Game
    context_object_name = "games"
    paginate_by = 25

    def get_queryset(self):
        queryset = models.Game.objects
        unpublished_filter = self.request.GET.get("unpublished-filter")
        if unpublished_filter:
            queryset = queryset.filter(change_for__isnull=True)
        else:
            queryset = queryset.with_installer()
        queryset = queryset.prefetch_related(
            "genres", "publisher", "developer", "platforms", "installers"
        )
        search_params = [key for key in self.request.GET.keys() if key != "page"]

        if self.request.GET.get("sort-by-popularity") or not search_params:
            queryset = queryset.order_by("-popularity")
        return self.get_filtered_queryset(queryset)

    def get_filtered_queryset(self, queryset):
        # Filter open source
        filters = []
        if self.request.GET.get("fully-libre-filter"):
            filters.append("fully_libre")
        if self.request.GET.get("open-engine-filter"):
            filters.append("open_engine")
        open_source_filters = " | ".join(
            ["Q(flags=Game.flags.%s)" % flag for flag in filters]
        )

        # Filter free
        filters = []
        if self.request.GET.get("free-filter"):
            filters.append("free")
        if self.request.GET.get("freetoplay-filter"):
            filters.append("freetoplay")
        if self.request.GET.get("pwyw-filter"):
            filters.append("pwyw")

        free_filters = " | ".join(["Q(flags=Game.flags.%s)" % flag for flag in filters])
        query_filters = ", ".join(
            [filters for filters in (open_source_filters, free_filters) if filters]
        )

        if query_filters:
            queryset = eval("queryset.filter(%s)" % query_filters)

        search_terms = self.request.GET.get("q")
        if "\x00" in str(search_terms):
            search_terms = None
        if search_terms:
            search_terms = search_terms.strip()
            if self.request.GET.get("search-installers"):
                # Search in installer instead of the game name
                queryset = queryset.filter(installers__content__icontains=search_terms)
            else:
                queryset = queryset.filter(name__icontains=search_terms)
        return queryset

    def get_pages(self, context):
        page = context["page_obj"]
        paginator = page.paginator
        page_indexes = get_page_range(paginator.num_pages, page.number)
        page.page_count = page_indexes[-1]
        page.diff_to_last_page = page.page_count - page.number
        pages = []
        for i in page_indexes:
            if i:
                pages.append(paginator.page(i))
            else:
                pages.append(None)
        return pages

    def get_context_data(self, **kwargs):
        context = super(GameList, self).get_context_data(**kwargs)
        context["page_range"] = self.get_pages(context)
        get_args = self.request.GET
        context["search_terms"] = get_args.get("q")
        context["all_open_source"] = get_args.get("all-open-source")
        context["fully_libre_filter"] = get_args.get("fully-libre-filter")
        context["open_engine_filter"] = get_args.get("open-engine-filter")
        context["all_free"] = get_args.get("all-free")
        context["free_filter"] = get_args.get("free-filter")
        context["freetoplay_filter"] = get_args.get("freetoplay-filter")
        context["pwyw_filter"] = get_args.get("pwyw-filter")
        context["unpublished_filter"] = get_args.get("unpublished-filter")
        context["sort_by_popularity"] = get_args.get("sort-by-popularity")
        context["search_installers"] = get_args.get("search-installers")
        for key in context:
            if key.endswith("_filter") and context[key]:
                context["show_advanced"] = True
                break
        context["platforms"] = Platform.objects.with_games()
        context["genres"] = models.Genre.objects.with_games()
        context["unpublished_match_count"] = self.get_filtered_queryset(
            models.Game.objects.filter(is_public=False)
        ).count()
        return context


class GameListByYear(GameList):
    def get_filtered_queryset(self, queryset):
        queryset = super(GameListByYear, self).get_filtered_queryset(queryset)
        return queryset.filter(year=self.args[0])

    def get_context_data(self, **kwargs):
        context = super(GameListByYear, self).get_context_data(**kwargs)
        context["year"] = self.args[0]
        return context


class GameListByGenre(GameList):
    """View for games filtered by genre"""

    def get_filtered_queryset(self, queryset):
        queryset = super(GameListByGenre, self).get_filtered_queryset(queryset)
        return queryset.filter(genres__slug=self.args[0])

    def get_context_data(self, **kwargs):
        context = super(GameListByGenre, self).get_context_data(**kwargs)
        try:
            context["genre"] = models.Genre.objects.get(slug=self.args[0])
        except models.Genre.DoesNotExist:
            raise Http404
        return context


class GameListByCompany(GameList):
    """View for games filtered by publisher"""

    def get_filtered_queryset(self, queryset):
        queryset = super(GameListByCompany, self).get_filtered_queryset(queryset)
        return queryset.filter(
            Q(publisher__slug=self.args[0]) | Q(developer__slug=self.args[0])
        )

    def get_context_data(self, **kwargs):
        context = super(GameListByCompany, self).get_context_data(**kwargs)
        try:
            context["company"] = models.Company.objects.get(slug=self.args[0])
        except models.Company.DoesNotExist:
            raise Http404
        return context


class GameListByPlatform(GameList):
    """View for games filtered by platform"""

    def get_filtered_queryset(self, queryset):
        queryset = super(GameListByPlatform, self).get_filtered_queryset(queryset)
        return queryset.filter(platforms__slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super(GameListByPlatform, self).get_context_data(**kwargs)
        try:
            context["platform"] = Platform.objects.get(slug=self.kwargs["slug"])
        except Platform.DoesNotExist:
            raise Http404
        return context


def game_for_installer(_request, slug):
    """Redirects to the game details page from a valid installer slug"""
    try:
        installers = models.Installer.objects.fuzzy_get(slug)
    except Installer.DoesNotExist:
        raise Http404
    installer = installers[0]
    game_slug = installer.game.slug
    return redirect(reverse("game_detail", kwargs={"slug": game_slug}))


def game_detail(request, slug):
    """View rendering the details for a game"""
    try:
        game = models.Game.objects.get(slug=slug)
    except models.Game.DoesNotExist:
        try:
            game = models.Game.objects.get(aliases__slug=slug)
            return redirect(reverse("game_detail", kwargs={"slug": game.slug}))
        except models.Game.DoesNotExist:
            raise Http404
    installers = game.installers.published()
    unpublished_installers = game.installers.unpublished()
    pending_change_subm_count = 0

    user = request.user
    if user.is_authenticated:
        in_library = game in user.gamelibrary.games.all()
        screenshots = game.screenshot_set.published(user=user, is_staff=user.is_staff)

        if user.is_staff and user.has_perm("games.change_game"):
            pending_change_subm_count = len(Game.objects.filter(change_for=game))
    else:
        in_library = False
        screenshots = game.screenshot_set.published()

    return render(
        request,
        "games/detail.html",
        {
            "game": game,
            "banner_options": {"crop": "top", "blur": "14x6"},
            "banner_size": "940x352",
            "in_library": in_library,
            "library_count": models.GameLibrary.objects.filter(
                games__in=[game.id]
            ).count(),
            "pending_change_subm_count": pending_change_subm_count,
            "can_publish": user.is_staff and user.has_perm("games.can_publish_game"),
            "can_edit": user.is_staff and user.has_perm("games.change_game"),
            "installers": installers,
            "auto_installers": game.get_default_installers(),
            "unpublished_installers": unpublished_installers,
            "screenshots": screenshots,
        },
    )


@user_confirmed_required
@check_installer_restrictions
def new_installer(request, slug):
    game = get_object_or_404(models.Game, slug=slug)
    installer = Installer(game=game)
    installer.set_default_installer()
    form = InstallerForm(request.POST or None, instance=installer)
    if request.method == "POST" and form.is_valid():
        installer = form.save(commit=False)
        installer.game_id = game.id
        installer.user = request.user
        installer.save()
        notify_installer(installer)
        return redirect("installer_complete", slug=game.slug)
    return render(
        request, "installers/form.html", {"form": form, "game": game, "new": True}
    )


@user_confirmed_required
@check_installer_restrictions
@never_cache
def edit_installer(request, slug):
    """Display an edit form for install scripts

    Args:
        request: Django request object
        slug (str): installer slug

    Returns:
        Django response
    """

    installer = get_object_or_404(Installer, slug=slug)

    # Handle installer deletion in a separate view
    if "delete" in request.POST:
        return redirect(reverse("delete_installer", kwargs={"slug": installer.slug}))
    # Extract optional revision ID from parameters
    revision_id = request.GET.get("revision")
    try:
        revision_id = int(revision_id)
    except (ValueError, TypeError):
        revision_id = None

    draft_data = None
    versions = Version.objects.get_for_object(installer)

    # Reset reason when the installer is edited.
    installer.reason = ""

    for version in versions:
        if revision_id:
            # Display the revision given in the GET parameters
            if version.revision.id == revision_id:
                draft_data = version.field_dict
                break
        else:
            # Display the latest revision created by the current logged in user
            if (
                    version.revision.user == request.user or request.user.is_staff
            ) and version.revision.date_created > installer.updated_at:
                draft_data = version.field_dict
                revision_id = version.revision.id
                break
    if draft_data:
        draft_data["reason"] = ""
        if "runner_id" in draft_data:
            draft_data["runner"] = draft_data["runner_id"]

    form = InstallerEditForm(
        request.POST or None, instance=installer, initial=draft_data
    )
    if request.method == "POST" and form.is_valid():
        # Force the creation of a revision instead of creating a new installer
        with reversion.create_revision():
            installer = form.save(commit=False)
            reversion.set_user(request.user)
            reversion.set_comment(
                "[{}] {} by {} on {}".format(
                    "draft" if installer.draft else "submission",
                    slug,
                    request.user.username,
                    timezone.now(),
                )
            )
            reversion.add_to_revision(installer)

        if "save" in request.POST:
            messages.info(request, "Draft saved")
            return redirect("edit_installer", slug=installer.slug)
        messages.info(request, "Submission sent to moderation")
        return redirect("installer_complete", slug=installer.game.slug)

    if draft_data:
        messages.info(
            request,
            "You are viewing a draft of the installer which does not "
            "reflect the currently available installer. Changes will be "
            "published once it goes through moderation.",
        )
    return render(
        request,
        "installers/form.html",
        {
            "form": form,
            "game": installer.game,
            "new": False,
            "installer": installer,
            "versions": versions,
            "revision_id": revision_id,
        }
    )


@user_confirmed_required
def delete_installer(request, slug):
    installer = get_object_or_404(Installer, slug=slug)
    if installer.user != request.user or not installer.draft:
        raise Http404
    if request.method == "POST" and "delete" in request.POST:
        game = installer.game
        installer_name = installer.slug
        installer.delete()
        messages.warning(
            request, u"The installer {} has been deleted.".format(installer_name)
        )
        return redirect(game.get_absolute_url())
    return render(request, "installers/delete.html", {"installer": installer})


@staff_member_required
def publish_installer(request, slug):
    installer = get_object_or_404(Installer, slug=slug)
    installer.published = True
    installer.save()
    return redirect("game_detail", slug=installer.game.slug)


def validate(game, request, form):
    if request.method == "POST" and form.is_valid():
        installer = form.save(commit=False)
        installer.game_id = game.id
        installer.user_id = request.user.id
        installer.save()


def installer_complete(request, slug):
    game = get_object_or_404(models.Game, slug=slug)
    return render(request, "installers/complete.html", {"game": game})


def get_installers(request, slug):
    """Deprecated function, use REST API"""
    try:
        installers_json = Installer.objects.get_json(slug)
    except Installer.DoesNotExist:
        raise Http404
    return HttpResponse(installers_json, content_type="application/json")


@never_cache
def view_installer(request, id):
    try:
        installer = Installer.objects.get(pk=id)
    except Installer.DoesNotExist:
        raise Http404
    return render(request, "installers/view.html", {"installer": installer})


@user_confirmed_required
def fork_installer(request, slug):
    try:
        installer = Installer.objects.get(slug=slug)
    except Installer.DoesNotExist:
        raise Http404
    form = ForkInstallerForm(request.POST or None, instance=installer)
    if request.POST and form.is_valid():
        installer.pk = None
        installer.game = form.cleaned_data["game"]
        installer.version = "Change Me"
        installer.published = False
        installer.rating = ""
        installer.user = request.user
        installer.save()
        return redirect(reverse("edit_installer", kwargs={"slug": installer.slug}))
    context = {"form": form, "installer": installer}
    return render(request, "installers/fork.html", context)


class InstallerFeed(Feed):
    title = "Lutris installers"
    link = "/games/"
    description = u"Latest lutris installers"
    feed_size = 20

    def items(self):
        return Installer.objects.order_by("-created_at")[: self.feed_size]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return item.get_absolute_url()


def get_banner(request, slug):
    """Serve game title in an appropriate format for the client."""
    try:
        game = Game.objects.get(slug=slug)
    except Game.DoesNotExist:
        game = None
    if not game or not game.title_logo:
        raise Http404
    try:
        thumbnail = get_thumbnail(game.title_logo, settings.BANNER_SIZE, crop="center")
    except AttributeError:
        game.title_logo.delete()
        raise Http404
    return redirect(thumbnail.url)


def get_icon(request, slug):
    try:
        game = Game.objects.get(slug=slug)
    except Game.DoesNotExist:
        game = None
    if not game or not game.icon:
        raise Http404
    try:
        thumbnail = get_thumbnail(
            game.icon, settings.ICON_SIZE, crop="center", format="PNG"
        )
    except AttributeError:
        game.icon.delete()
        raise Http404
    return redirect(thumbnail.url)


def game_list(request):
    """View for all games"""
    games = models.Game.objects.filter(change_for__isnull=True)
    return render(request, "games/game_list.html", {"games": games})


@user_confirmed_required
def submit_game(request):
    form = GameForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        game = form.save()
        submission = GameSubmission(user=request.user, game=game)
        submission.save()

        # Notify managers a game has been submitted
        admin_url = "https://lutris.net" + reverse(
            "admin:games_game_change", args=(game.id,)
        )
        context = {
            "game_name": game.name,
            "username": request.user.username,
            "admin_link": admin_url,
        }
        subject = "New game submitted: {}".format(game.name)
        send_email("new_game", context, subject, settings.MANAGERS[0][1])

        redirect_url = request.build_absolute_uri(reverse("game-submitted"))

        # Enforce https
        if not settings.DEBUG:
            redirect_url = redirect_url.replace("http:", "https:")

        LOGGER.info("Game submitted, redirecting to %s", redirect_url)
        return redirect(redirect_url)
    return render(request, "games/submit.html", {"form": form})


@user_confirmed_required
def edit_game(request, slug):
    """Lets the user suggest changes to a game for a moderator to verify"""

    # Load game object and get changeable fields and their defaults
    game = get_object_or_404(Game, slug=slug)
    change_model = game.get_change_model()

    # Workaround: Assigning change_model to initial in the form
    # directly will display the error immediately that changes must be made
    initial = change_model if request.method == "POST" else None

    # Sanity check: Disallow change-suggestions for changes
    if game.change_for:
        return HttpResponseBadRequest("You can only apply changes to a game")

    # Initialise form with rejected values or with the working copy
    form = GameEditForm(request.POST or change_model, request.FILES, initial=initial)

    # If form was submitted and is valid, persist suggestion for moderation
    if request.method == "POST" and form.is_valid():
        # Save the game
        change_suggestion = form.save(commit=False)
        change_suggestion.change_for = game
        change_suggestion.save()
        form.save_m2m()

        # Save metadata (author + reason)
        change_suggestion_meta = GameSubmission(
            user=request.user, game=change_suggestion, reason=request.POST["reason"]
        )
        change_suggestion_meta.save()
        return redirect(reverse("game-submitted-changes", kwargs={"slug": slug}))

    # Render template
    return render(request, "games/submit.html", {"form": form, "game": game})


def changes_submitted(request, slug):
    game = get_object_or_404(Game, slug=slug)
    return render(request, "games/submitted-changes.html", {"game": game})


def publish_game(request, game_id):
    """This view should be an API call"""
    if not request.user.has_perm("games.can_publish_game"):
        raise Http404
    game = get_object_or_404(Game, id=game_id)
    game.is_public = True
    game.save()
    return redirect(reverse("game_detail", kwargs={"slug": game.slug}))


@user_confirmed_required
def screenshot_add(request, slug):
    game = get_object_or_404(Game, slug=slug)
    form = ScreenshotForm(request.POST or None, request.FILES or None, game_id=game.id)
    if form.is_valid():
        form.instance.uploaded_by = request.user
        form.save()
        return redirect(reverse("game_detail", kwargs={"slug": slug}))
    return render(request, "games/screenshot/add.html", {"form": form})


@login_required
def publish_screenshot(request, screenshot_id):
    """This view should be an API call"""
    screenshot = get_object_or_404(models.Screenshot, id=screenshot_id)
    if not request.user.is_staff:
        raise Http404
    screenshot.published = True
    screenshot.save()
    return redirect("game_detail", slug=screenshot.game.slug)


@require_POST
@login_required
def submit_issue(request):
    response = {"status": "ok"}
    try:
        installer = Installer.objects.get(slug=request.POST.get("installer"))
    except Installer.DoesNotExist:
        response["status"] = "error"
        response["message"] = "Could not find the installer"
        return HttpResponse(json.dumps(response))

    content = request.POST.get("content")
    if not content:
        response["status"] = "error"
        response["message"] = "The issue content is empty"
        return HttpResponse(json.dumps(response))

    installer_issue = InstallerIssue(
        installer=installer, submitted_by=request.user, description=content
    )
    installer_issue.save()
    notify_issue_creation(installer_issue, request.user, content)

    return HttpResponse(json.dumps(response))


@staff_member_required
def installer_submissions(request):
    submissions = Version.objects.filter(revision__comment__startswith="[submission]")
    drafts = Version.objects.filter(revision__comment__startswith="[draft]")
    installers = Installer.objects.filter(published=False)
    unpublished_games = (
        Game.objects.filter(change_for__isnull=True)
        .filter(installers__isnull=False, is_public=False)
        .distinct()
    )
    return render(
        request,
        "installers/submissions.html",
        {
            "submissions": submissions,
            "drafts": drafts[:20],
            "installers": installers[:20],
            "unpublished_games": unpublished_games,
        },
    )
