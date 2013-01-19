"""Views for lutris main app"""
# pylint: disable=E1101

from django.conf import settings
from django.http import HttpResponse

from django.views.generic import list_detail, ListView

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from games.models import Game, Runner, Genre, Platform, \
                         Company, Installer, News
from games.forms import InstallerForm


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


def home(request):
    """Homepage view"""
    featured = Game.objects.exclude(cover__exact="")[:5]
    latest_games = Game.objects.all()[:5]
    news = News.objects.all()[:5]
    download_type = "Ubuntu"
    return render(request, 'home.html',
                  {'featured': featured, 'news': news,
                   'download_type': download_type})

def news_archives(request):
    news = News.objects.all()
    return render(request, 'news.html', {'news': news})

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
    return render(request, 'games/new-installer.html',
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


def game_list_by_year(request, year):
    """View for games filtered by year"""
    return list_detail.object_list(
        request,
        queryset=Game.objects.filter(year__gt=2000),
        template_name="games/game_list.html",
        template_object_name="games",
        extra_context={"year": year}
    )


def game_list_by_genre(request, genre_slug):
    """View for games filtered by genre"""
    genre = get_object_or_404(Genre, slug=genre_slug)
    return list_detail.object_list(
        request,
        queryset=Game.objects.filter(genre__slug=genre_slug),
        template_name="games/game_list.html",
        template_object_name="games",
        extra_context={'genre': genre}
    )


def games_by_publisher(request, publisher_slug):
    """View for games filtered by publisher"""
    company = get_object_or_404(Company, slug=publisher_slug)
    return list_detail.object_list(
        request,
        queryset=Game.objects.filter(publisher=company),
        template_name="games/game_list.html",
        template_object_name='games',
        extra_context={'publisher': company}
    )


def games_by_developer(request, developer_slug):
    """View for games filtered by developer"""
    company = get_object_or_404(Company, slug=developer_slug)
    return list_detail.object_list(
        request,
        queryset=Game.objects.filter(developer=company),
        template_name="games/game_list.html",
        template_object_name='games',
        extra_context={'developer': company}
    )


def games_by_platform(request, platform_slug):
    """View for games filtered by platform"""
    platform = get_object_or_404(Platform, slug=platform_slug)
    return list_detail.object_list(
        request,
        queryset=Game.objects.filter(platform=platform),
        template_name="games/game_list.html",
        template_object_name='games',
        extra_context={'platform': platform}
    )


def screenshot_add(request, slug):
    game = get_object_or_404(Game, slug=slug)
    return render(request, 'games/screenshot/add.html')
