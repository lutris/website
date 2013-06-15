"""Views for lutris main app"""
# pylint: disable=E1101
import yaml

from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.generic import ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from sorl.thumbnail import get_thumbnail

from .models import Game, Runner, Installer, Platform, GameLibrary
from .forms import InstallerForm, ScreenshotForm, GameForm


class GameList(ListView):
    model = Game
    context_object_name = "games"

    def get_queryset(self):
        return Game.objects.published()


class GameListByYear(GameList):
    def get_queryset(self):
        return Game.objects.filter(year=self.args[0])

    def get_context_data(self, **kwargs):
        context = super(GameListByYear, self).get_context_data(**kwargs)
        context['year'] = self.args[0]
        return context


class GameListByGenre(ListView):
    """View for games filtered by genre"""
    def get_queryset(self):
        return Game.objects.filter(genre=self.args[0])

    def get_context_data(self, **kwargs):
        context = super(GameListByGenre, self).get_context_data(**kwargs)
        context['genre'] = self.args[0]
        return context


class GameListByPublisher(ListView):
    """View for games filtered by publisher"""
    def get_queryset(self):
        return Game.objects.filter(publisher=self.args[0])

    def get_context_data(self, **kwargs):
        context = super(GameListByGenre, self).get_context_data(**kwargs)
        context['publisher'] = self.args[0]
        return context


class GameListByDeveloper(ListView):
    """View for games filtered by developer"""
    def get_queryset(self):
        return Game.objects.filter(developer=self.args[0])

    def get_context_data(self, **kwargs):
        context = super(GameListByGenre, self).get_context_data(**kwargs)
        context['developer'] = self.args[0]
        return context


class GameListByPlatform(GameList):
    """View for games filtered by platform"""
    def get_queryset(self):
        return Game.objects.filter(platforms__slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super(GameListByPlatform, self).get_context_data(**kwargs)
        context['platform'] = Platform.objects.get(slug=self.kwargs['slug'])
        return context


def download_latest(request):
    archive_url = settings.LATEST_LUSTRIS_DEB
    return redirect(archive_url)


def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)
    banner_options = {'crop': 'top', 'blur': '4x6'}
    banner_size = "940x352"
    return render(request, 'games/detail.html',
                  {'game': game,
                   'banner_options': banner_options,
                   'banner_size': banner_size})


@login_required
def new_installer(request, slug):
    game = get_object_or_404(Game, slug=slug)
    form = InstallerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        installer = form.save(commit=False)
        installer.game_id = game.id
        installer.user_id = request.user.id
        installer.save()

        return redirect("installer_complete", slug=game.slug)
    return render(request, 'games/installer-form.html',
                  {'form': form, 'game': game})


def validate(game, request, form):
    if request.method == 'POST' and form.is_valid():
        installer = form.save(commit=False)
        installer.game_id = game.id
        installer.user_id = request.user.id
        installer.save()


@login_required
def edit_installer(request, slug):
    installer = get_object_or_404(Installer, slug=slug)
    form = InstallerForm(request.POST or None, instance=installer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect("installer_complete", slug=installer.game.slug)
    return render(request, 'games/installer-form.html',
                  {'form': form, 'game': installer.game, 'new': False})


def installer_complete(request, slug):
    game = get_object_or_404(Game, slug=slug)
    return render(request, 'games/installer-complete.html', {'game': game})


def serve_installer(request, slug):
    """Serve the content of an installer in yaml format"""
    try:
        installer = Installer.objects.fuzzy_get(slug)
    except Installer.DoesNotExist:
        raise Http404
    yaml_content = yaml.safe_load(installer.content)
    yaml_content['version'] = installer.version
    yaml_content['name'] = installer.game.name
    yaml_content['runner'] = installer.runner.slug
    content = yaml.safe_dump(yaml_content)
    return HttpResponse(content, content_type="application/yaml")


def serve_installer_banner(request, slug):
    try:
        installer = Installer.objects.fuzzy_get(slug)
    except Installer.DoesNotExist:
        raise Http404
    if not installer.game.title_logo:
        raise Http404
    banner_thumbnail = get_thumbnail(installer.game.title_logo,
                                     settings.BANNER_SIZE,
                                     crop="top")
    return redirect(banner_thumbnail.url)


def serve_installer_icon(request, slug):
    try:
        installer = Installer.objects.fuzzy_get(slug)
    except Installer.DoesNotExist:
        raise Http404
    if not installer.game.icon:
        raise Http404
    banner_thumbnail = get_thumbnail(installer.game.icon,
                                     settings.ICON_SIZE,
                                     crop="top")
    return redirect(banner_thumbnail.url)


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
    form = GameForm(request.POST or None)
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


def library_show(request, username):
    user = User.objects.get(username=username)
    profile = user.get_profile()
    library = GameLibrary.objects.get(user=user)
    return render(request, 'games/library_show.html',
                  {'profile': profile, 'library': library})


def library_add(request, slug):
    user = request.user
    library = GameLibrary.objects.get(user=user)
    game = get_object_or_404(Game, slug=slug)
    library.games.add(game)
    return redirect(request.META['HTTP_REFERER'])


def library_remove(request, slug):
    user = request.user
    library = GameLibrary.objects.get(user=user)
    game = get_object_or_404(Game, slug=slug)
    library.games.remove(game)
    return redirect(request.META['HTTP_REFERER'])
