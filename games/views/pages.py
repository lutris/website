"""Views for lutris main app"""
# pylint: disable=too-many-ancestors,raise-missing-from
from __future__ import absolute_import

import json
import logging

import reversion
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import (SearchQuery, SearchRank,
                                            SearchVector)
from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from reversion.models import Version
from sorl.thumbnail import get_thumbnail

from accounts.decorators import (check_installer_restrictions,
                                 user_confirmed_required)
from emails.messages import send_email
from games import models
from games.forms import (ForkInstallerForm, GameEditForm, GameForm,
                         InstallerEditForm, InstallerForm, LibraryFilterForm,
                         ScreenshotForm)
from games.models import Game, GameSubmission, Installer, InstallerIssue
from games.webhooks import notify_installer, notify_issue_creation

LOGGER = logging.getLogger(__name__)


class GameList(ListView):
    """Game list view"""
    template_name = 'games/game_list.html'
    model = models.Game
    context_object_name = "games"
    paginate_by = 25
    paginate_orphans = 10
    ordering = 'name'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.q_params = {}

    def get(self, request, *args, **kwargs):
        self.q_params = {
            'q': request.GET.get('q', ''),
            'platforms': request.GET.getlist('platforms',
                                             [kwargs.get('platform')] if 'platform' in kwargs else []),
            'genres': request.GET.getlist('genres',
                                          [kwargs.get('genre')] if 'genre' in kwargs else []),
            'companies': request.GET.getlist('companies',
                                             [kwargs.get('company')] if 'company' in kwargs else []),
            'years': request.GET.getlist('years', [kwargs.get('year')] if 'year' in kwargs else []),
            'flags': request.GET.getlist('flags', []),
            'unpublished-filter': request.GET.get('unpublished-filter', False),
            'search-installers': request.GET.get('search-installers', False)
        }
        return super().get(request, *args, **kwargs)

    def get_page(self):
        """Return the page number for the paginated queryset"""
        try:
            page = int(self.request.GET.get("page"))
        except ValueError:
            return 1
        if page < 1:
            return 1
        return page

    def get_paginate_by(self, queryset):
        """Return the number of items per page"""
        try:
            return int(self.request.GET.get("paginate_by", self.paginate_by))
        except ValueError:
            return self.paginate_by

    def get_ordering(self):
        """Return the field used to order the query by"""
        field = self.request.GET.get("ordering", self.ordering)
        if field.strip('-') not in Game.valid_fields():
            return None
        return field

    def get_queryset(self):
        queryset = models.Game.objects
        if self.q_params['unpublished-filter']:
            queryset = queryset.filter(change_for__isnull=True)
        else:
            queryset = queryset.with_installer()
        queryset = queryset.prefetch_related(
            "genres", "publisher", "developer", "platforms", "installers"
        )
        ordering = self.get_ordering()
        if ordering:
            if self.q_params['q'] and not self.q_params['search-installers']:
                queryset = queryset.order_by('-rank', ordering)
            else:
                queryset = queryset.order_by(ordering)
        return self.get_filtered_queryset(queryset)

    def get_filtered_queryset(self, queryset):
        """Build search query from the search parameters"""
        self.clean_search_query()
        if self.q_params['q']:
            if self.q_params['search-installers']:
                queryset = queryset.filter(installers__content__icontains=self.q_params['q'])
            else:
                vector = SearchVector('name', weight='A') + SearchVector('aliases__name', weight='A')
                query = SearchQuery(self.q_params['q'])
                queryset = queryset.annotate(rank=SearchRank(vector, query)).filter(rank__gte=0.3)
        if self.q_params['platforms']:
            queryset = queryset.filter(platforms__pk__in=self.q_params['platforms'])
        if self.q_params['genres']:
            queryset = queryset.filter(genres__pk__in=self.q_params['genres'])
        if self.q_params['companies']:
            queryset = queryset.filter(
                Q(publisher__pk__in=self.q_params['companies'])
                | Q(developer__pk__in=self.q_params['companies'])
            )
        if self.q_params['years']:
            queryset = queryset.filter(Q(year__in=self.q_params['years']))
        if self.q_params['flags']:
            flag_q = Q()
            for flag_name in self.q_params['flags']:
                try:
                    flag = getattr(models.Game.flags, flag_name)
                except AttributeError:
                    continue
                flag_q |= Q(flags=flag)
            queryset = queryset.filter(flag_q)
        return queryset

    def clean_search_query(self):
        """Validators used to remove garbage input sent in search data."""
        # those fields should only contain ints.
        int_lists = ("companies", "years", "genres", "platforms")
        for field in int_lists:
            if field in self.q_params:
                try:
                    self.q_params[field] = [
                        int(f) for f in self.q_params[field]
                    ]
                except ValueError:
                    self.q_params[field] = []

    def clean_parameters(self):
        """Validators used to prevent sending garbage data to Django views"""
        # Set the GET QueryDict to mutable so we can corrrect the values
        self.request.GET._mutable = True  # pylint: disable=protected-access
        if "paginate_by" in self.request.GET:
            self.request.GET["paginate_by"] = self.get_paginate_by(None)
        if "page" in self.request.GET:
            self.request.GET["page"] = self.get_page()

    def get_context_data(self, *, object_list=None, **kwargs):  # pylint: disable=unused-argument
        """Display the Lutris library"""
        self.clean_parameters()
        context = super(GameList, self).get_context_data(object_list=object_list, **kwargs)
        context['is_library'] = False
        filter_string = ''
        if self.q_params.get('q'):
            filter_string = '&q=%s' % self.q_params['q']
        if self.q_params.get('platforms'):
            for platform in self.q_params['platforms']:
                filter_string += '&platforms=%s' % platform
        if self.q_params.get('genres'):
            for genre in self.q_params['genres']:
                filter_string += '&genres=%s' % genre
        if self.q_params.get('companies'):
            for company in self.q_params['companies']:
                filter_string += '&companies=%s' % company
        if self.q_params.get('years'):
            for year in self.q_params['years']:
                filter_string += '&years=%s' % year
        if self.q_params.get('flags'):
            for flag in self.q_params['flags']:
                filter_string += '&flags=%s' % flag
        if self.q_params.get('unpublished-filter'):
            filter_string += '&unpublished-filter=%s' % self.q_params['unpublished-filter']
        if self.q_params.get('search-installers'):
            filter_string += '&search-installers=%s' % self.q_params['search-installers']
        context['filter_string'] = filter_string
        context['filter_form'] = LibraryFilterForm(initial=self.q_params)
        context['order_by'] = self.get_ordering()
        context['paginate_by'] = self.get_paginate_by(None)
        context['search_terms'] = self.q_params.get('search', '')
        context["unpublished_filter"] = self.q_params.get('unpublished-filter', False)
        context["search_installers"] = self.q_params.get('search-installers', False)
        context["unpublished_match_count"] = self.get_filtered_queryset(
            models.Game.objects.filter(is_public=False)
        ).count()
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
        except models.Game.MultipleObjectsReturned:
            games = models.Game.objects.filter(aliases__slug=slug)
            LOGGER.error("The slug '%s' was used multiple times", slug)
            return redirect(reverse("game_detail", kwargs={"slug": games[0].slug}))
    user = request.user
    installers = game.installers.published()

    if user.is_staff:
        unpublished_installers = game.installers.unpublished()
    elif user.is_authenticated:
        unpublished_installers = game.installers.unpublished().filter(user=user)
    else:
        unpublished_installers = []

    pending_change_subm_count = 0


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
            request, "The installer {} has been deleted.".format(installer_name)
        )
        return redirect(game.get_absolute_url())
    return render(request, "installers/delete.html", {"installer": installer})


@staff_member_required
def publish_installer(request, slug):  # pylint: disable=unused-argument
    installer = get_object_or_404(Installer, slug=slug)
    installer.published = True
    installer.save()
    return redirect("game_detail", slug=installer.game.slug)


def installer_complete(request, slug):
    game = get_object_or_404(models.Game, slug=slug)
    return render(request, "installers/complete.html", {"game": game})


def get_installers(request, slug):  # pylint: disable=unused-argument
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
    """RSS feed for Lutris installers"""
    title = "Lutris installers"
    link = "/games/"
    description = "Latest lutris installers"
    feed_size = 20

    def items(self):
        return Installer.objects.order_by("-created_at")[: self.feed_size]

    def item_title(self, item):
        return item.slug

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
    """Show a form to upload a new screenshot"""
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
    """Create a new issue
    This should really be done in the REST API
    """
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

    return JsonResponse(response)


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
