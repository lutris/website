"""Views for lutris main app"""
# pylint: disable=E1101, W0613
from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.generic import ListView
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.contrib.syndication.views import Feed
from django.contrib.auth.decorators import login_required

from sorl.thumbnail import get_thumbnail

from .models import Game, Runner, Installer
from . import models
from .forms import InstallerForm, ScreenshotForm, GameForm


class GameList(ListView):
    model = Game
    context_object_name = "games"
    paginate_by = 25

    def get_queryset(self):
        without_installer = self.request.GET.get('without_installer')
        if without_installer:
            queryset = Game.objects.published()
        else:
            queryset = Game.objects.with_installer()
        search_terms = self.request.GET.get('q')
        if search_terms:
            queryset = queryset.filter(name__icontains=search_terms)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(GameList, self).get_context_data(**kwargs)
        search_terms = self.request.GET.get('q')
        context['platforms'] = models.Platform.objects.all()
        context['genres'] = models.Genre.objects.all()
        if search_terms:
            context['search_terms'] = search_terms
        return context


class GameListByYear(GameList):
    def get_queryset(self):
        queryset = super(GameListByYear, self).get_queryset()
        return queryset.filter(year=self.args[0])

    def get_context_data(self, **kwargs):
        context = super(GameListByYear, self).get_context_data(**kwargs)
        context['year'] = self.args[0]
        return context


class GameListByGenre(GameList):
    """View for games filtered by genre"""
    def get_queryset(self):
        queryset = super(GameListByGenre, self).get_queryset()
        return queryset.filter(genres__slug=self.args[0])

    def get_context_data(self, **kwargs):
        context = super(GameListByGenre, self).get_context_data(**kwargs)
        try:
            context['genre'] = models.Genre.objects.get(slug=self.args[0])
        except models.Genre.DoesNotExist:
            raise Http404
        return context


class GameListByCompany(GameList):
    """View for games filtered by publisher"""
    def get_queryset(self):
        queryset = super(GameListByCompany, self).get_queryset()
        return queryset.filter(Q(publisher__slug=self.args[0])
                               | Q(developer__slug=self.args[0]))

    def get_context_data(self, **kwargs):
        context = super(GameListByCompany, self).get_context_data(**kwargs)
        try:
            context['company'] = models.Company.objects.get(slug=self.args[0])
        except models.Company.DoesNotExist:
            raise Http404
        return context


class GameListByPlatform(GameList):
    """View for games filtered by platform"""
    def get_queryset(self):
        queryset = super(GameListByPlatform, self).get_queryset()
        return queryset.filter(platforms__slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super(GameListByPlatform, self).get_context_data(**kwargs)
        try:
            context['platform'] = models.Platform.objects.get(
                slug=self.kwargs['slug']
            )
        except models.Platform.DoesNotExist:
            raise Http404
        return context


def game_for_installer(request, slug):
    """ Redirects to the game details page from a valid installer slug """
    try:
        installers = models.Installer.objects.fuzzy_get(slug)
    except Installer.DoesNotExist:
        raise Http404
    installer = installers[0]
    game_slug = installer.game.slug
    return redirect(reverse('game_detail', kwargs={'slug': game_slug}))


def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)
    banner_options = {'crop': 'top', 'blur': '14x6'}
    banner_size = "940x352"
    user = request.user

    if user.is_authenticated():
        in_library = game in user.gamelibrary.games.all()
        installers = game.installer_set.published(user=user)
    else:
        in_library = False
        installers = game.installer_set.published()

    auto_installers = game.get_default_installers()
    return render(request, 'games/detail.html',
                  {'game': game,
                   'banner_options': banner_options,
                   'banner_size': banner_size,
                   'in_library': in_library,
                   'installers': installers,
                   'auto_installers': auto_installers})


@login_required
def new_installer(request, slug):
    game = get_object_or_404(Game, slug=slug)
    installer = Installer(game=game)
    installer.set_default_installer()
    form = InstallerForm(request.POST or None, instance=installer)
    if request.method == 'POST' and form.is_valid():
        installer = form.save(commit=False)
        installer.game_id = game.id
        installer.user = request.user
        installer.save()
        return redirect("installer_complete", slug=game.slug)
    return render(request, 'games/installer-form.html',
                  {'form': form, 'game': game})


@login_required
def publish_installer(request, slug):
    installer = get_object_or_404(Installer, slug=slug)
    if not request.user.is_staff:
        raise Http404
    installer.published = True
    installer.save()
    return redirect('game_detail', slug=installer.game.slug)


def validate(game, request, form):
    if request.method == 'POST' and form.is_valid():
        installer = form.save(commit=False)
        installer.game_id = game.id
        installer.user_id = request.user.id
        installer.save()


@login_required
def edit_installer(request, slug):
    installer = get_object_or_404(Installer, slug=slug)
    if installer.user is not request.user or not request.user.is_staff:
        raise Http404
    form = InstallerForm(request.POST or None, instance=installer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect("installer_complete", slug=installer.game.slug)
    return render(request, 'games/installer-form.html',
                  {'form': form, 'game': installer.game, 'new': False})


def installer_complete(request, slug):
    game = get_object_or_404(Game, slug=slug)
    return render(request, 'games/installer-complete.html', {'game': game})


def serve_installer(_request, slug):
    """Serve the content of an installer in yaml format."""
    try:
        installers = Installer.objects.fuzzy_get(slug)
    except Installer.DoesNotExist:
        raise Http404
    installer = installers[0]
    return HttpResponse(installer.as_yaml(), content_type='application/yaml')


def get_installers(request, slug):
    try:
        installers_json = Installer.objects.get_json(slug)
    except Installer.DoesNotExist:
        raise Http404
    return HttpResponse(installers_json, content_type='application/json')


class InstallerFeed(Feed):
    title = "Lutris installers"
    link = '/games/'
    description = u"Latest lutris installers"
    feed_size = 20

    def items(self):
        return Installer.objects.order_by("-created_at")[:self.feed_size]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return item.get_absolute_url()


def get_game_by_slug(slug):
    """Return game matching an installer slug or game slug"""
    game = None
    try:
        installers = Installer.objects.fuzzy_get(slug)
        installer = installers[0]
        game = installer.game
    except Installer.DoesNotExist:
        try:
            game = Game.objects.get(slug=slug)
        except Game.DoesNotExist:
            pass
    return game


def get_banner(request, slug):
    """Serve game title in an appropriate format for the client."""
    game = get_game_by_slug(slug)
    if not game or not game.title_logo:
        raise Http404
    thumbnail = get_thumbnail(game.title_logo, settings.BANNER_SIZE,
                              crop="center")
    return redirect(thumbnail.url)


def serve_installer_banner(request, slug):
    return get_banner(request, slug)


def get_icon(request, slug):
    game = get_game_by_slug(slug)
    if not game or not game.icon:
        raise Http404
    thumbnail = get_thumbnail(game.icon, settings.ICON_SIZE, crop="center",
                              format="PNG")
    return redirect(thumbnail.url)


def serve_installer_icon(request, slug):
    """ Legacy url, remove by Lutris 0.4 """
    return get_icon(request, slug)


def game_list(request):
    """View for all games"""
    games = Game.objects.all()
    return render(request, 'games/game_list.html', {'games': games})


def games_by_runner(request, runner_slug):
    """View for games filtered by runner"""
    runner = get_object_or_404(Runner, slug=runner_slug)
    games = Game.objects.filter(runner__slug=runner.slug)
    return render(request, 'games/game_list.html',
                  {'games': games})


@login_required
def submit_game(request):
    form = GameForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        game = form.save()
        # Notify admins a game has been submitted
        body = "The game %s has been added by %s" % (game.name, request.user)
        send_mail("New game submitted", body,
                  settings.DEFAULT_FROM_EMAIL,
                  settings.MANAGERS[0])

        return redirect(reverse("game-submitted"))
    return render(request, 'games/submit.html', {'form': form})


@login_required
def screenshot_add(request, slug):
    game = get_object_or_404(Game, slug=slug)
    form = ScreenshotForm(request.POST or None, request.FILES or None,
                          game_id=game.id)
    if form.is_valid():
        form.instance.uploaded_by = request.user
        form.save()
        return redirect(reverse("game_detail", kwargs={'slug': slug}))
    return render(request, 'games/screenshot/add.html', {'form': form})
