"""Views for lutris main app"""
# pylint: disable=E1101

from django.conf import settings
from django.http import HttpResponse

from django.views.generic import ListView

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from games.models import Game, Runner, Installer
from games.forms import InstallerForm, ScreenshotForm, GameForm


class GameList(ListView):
    model = Game
    context_object_name = "games"


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


class GameListByPlatform(ListView):
    """View for games filtered by platform"""
    def get_queryset(self):
        return Game.objects.filter(platform=self.args[0])

    def get_context_data(self, **kwargs):
        context = super(GameListByGenre, self).get_context_data(**kwargs)
        context['platform'] = self.args[0]
        return context


def download_latest(request):
    archive_url = settings.LATEST_LUSTRIS_DEB
    return redirect(archive_url)


def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)
    return render(request, 'games/detail.html', {'game': game})


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
    installer = get_object_or_404(Installer, slug=slug)
    content = installer.content
    return HttpResponse(content, content_type="application/yaml")


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
    form = GameForm()
    return render(request, 'games/submit.html', {'form': form})


def screenshot_add(request, slug):
    game = get_object_or_404(Game, slug=slug)
    form = ScreenshotForm(request.POST or None, game_id=game.id)
    if form.is_valid():
        form.save()
    return render(request, 'games/screenshot/add.html', {'form': form})
