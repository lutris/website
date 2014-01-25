"""Views for lutris main app"""
# pylint: disable=E1101, R0901
import yaml

from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.generic import ListView
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
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
        queryset = Game.objects.published()
        installers = Installer.objects.published().values("game_id")
        search_terms = self.request.GET.get('q')
        without_installer = self.request.GET.get('without_installer')
        if search_terms:
            queryset = queryset.filter(name__icontains=search_terms)
        if not without_installer:
            queryset = queryset.filter(id__in=installers)
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
        installer = models.Installer.objects.fuzzy_get(slug)
    except Installer.DoesNotExist:
        raise Http404
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

    return render(request, 'games/detail.html',
                  {'game': game,
                   'banner_options': banner_options,
                   'banner_size': banner_size,
                   'in_library': in_library,
                   'installers': installers})


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
    if installer.user is not request.user and not request.user.is_staff:
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
    """ Serve the content of an installer in yaml format. """
    try:
        installer = Installer.objects.fuzzy_get(slug)
    except Installer.DoesNotExist:
        raise Http404
    yaml_content = yaml.safe_load(installer.content)
    yaml_content['version'] = installer.version
    yaml_content['name'] = installer.game.name
    yaml_content['runner'] = installer.runner.slug
    yaml_content['installer_slug'] = installer.slug
    content = yaml.safe_dump(yaml_content)
    return HttpResponse(content, content_type="application/yaml")


def get_game_by_slug(slug):
    game = None
    try:
        installer = Installer.objects.fuzzy_get(slug)
        game = installer.game
    except Installer.DoesNotExist:
        try:
            game = Game.objects.get(slug=slug)
        except Game.DoesNotExist:
            pass
    return game


def serve_installer_banner(_request, slug):
    """ Serve game title in an appropriate format for the client. """
    game = get_game_by_slug(slug)
    if not game or not game.title_logo:
        raise Http404
    thumbnail = get_thumbnail(game.title_logo, settings.BANNER_SIZE,
                              crop="top")
    return redirect(thumbnail.url)


def serve_installer_icon(_request, slug):
    game = get_game_by_slug(slug)
    if not game or not game.icon:
        raise Http404
    thumbnail = get_thumbnail(game.icon, settings.ICON_SIZE, crop="top")
    return redirect(thumbnail.url)


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


def submit_game(request):
    form = GameForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
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
