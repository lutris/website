"""Views for lutris main app"""

from django.http import Http404, HttpResponse
from django.views.generic import list_detail
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.decorators import login_required
from games.models import Game, Runner, Genre, Platform, Company, Installer
from games.forms import InstallerForm
#pylint: disable=E1101


def home(request):
    """Homepage view"""
    featured = Game.objects.exclude(cover__exact="")[:5]
    
    return render_to_response('home.html', {
        'featured': featured
        }, context_instance=RequestContext(request)
    )


def game_detail(request, slug):
    """docstring for game_detail"""
    game = Game.objects.get(slug=slug)
    return render_to_response('games/detail.html', {
        "game": game,
        }, context_instance=RequestContext(request)
    )


@login_required
def new_installer(request, slug):
    try:
        game = Game.objects.get(slug=slug)
    except Game.DoesNotExist:
        raise Http404
    form = InstallerForm()
    if request.method == 'POST':
        form = InstallerForm(request.POST)
        if form.is_valid():
            installer = form.save(commit=False)
            installer.game_id = game.id
            installer.user_id = request.user.id
            installer.save()

            return redirect("installer_complete", slug=game.slug)
    return render_to_response('games/new-installer.html', {
        'form': form, 'game': game
        }, context_instance=RequestContext(request)
    )


@login_required
def edit_installer(request, slug):
    try:
        installer = Installer.objects.get(slug=slug)
    except Installer.DoesNotExist:
        raise Http404
    form = InstallerForm(instance=installer)
    if request.method == 'POST':
        form = InstallerForm(data=request.POST, instance=installer)
        if form.is_valid():
            form.save()
            return redirect("installer_complete", slug=installer.game.slug)
    return render_to_response('games/installer-form.html', {
        'form': form, 'game': installer.game, 'new': False
        }, context_instance=RequestContext(request)
    )


def installer_complete(request, slug):
    try:
        game = Game.objects.get(slug=slug)
    except Game.DoesNotExist:
        raise Http404
    return render_to_response('games/installer-complete.html', {
        'game': game
        }, context_instance=RequestContext(request)
    )


def serve_installer(request, slug):
    try:
        installer = Installer.objects.get(slug=slug)
    except Installer.DoesNotExist:
        raise Http404

    content = installer.content
    return HttpResponse(content, content_type="application/yaml")


def games_all(request):
    """View for all games"""
    games = Game.objects.all()
    return render_to_response('games/game_list.html',
                              {'games': games},
                              context_instance=RequestContext(request))


def games_by_runner(request, runner_slug):
    """View for games filtered by runner"""
    try:
        runner = Runner.objects.get(slug=runner_slug)
    except Runner.DoesNotExist:
        raise Http404
    games = Game.objects.filter(runner__slug=runner.slug)
    return render_to_response('games/game_list.html', {
        'games': games
        }, context_instance=RequestContext(request)
    )


def games_by_year(request, year):
    """View for games filtered by year"""
    return list_detail.object_list(request,
                                   queryset=Game.objects.filter(year=year),
                                   template_name="games/game_list.html",
                                   template_object_name="games",
                                   extra_context={"year": year})


def games_by_genre(request, genre_slug):
    """View for games filtered by genre"""
    try:
        genre = Genre.objects.get(slug=genre_slug)
    except Genre.DoesNotExist:
        raise Http404
    return list_detail.object_list(
        request,
        queryset=Game.objects.filter(genre=genre),
        template_name="games/game_list.html",
        template_object_name="games",
        extra_context={'genre': genre}
    )


def games_by_publisher(request, publisher_slug):
    """View for games filtered by publisher"""
    try:
        company = Company.objects.get(slug=publisher_slug)
    except:
        raise Http404

    return list_detail.object_list(
            request,
            queryset=Game.objects.filter(publisher=company),
            template_name="games/game_list.html",
            template_object_name='games',
            extra_context={'publisher': company}
    )


def games_by_developer(request, developer_slug):
    """View for games filtered by developer"""
    try:
        company = Company.objects.get(slug=developer_slug)
    except:
        raise Http404

    return list_detail.object_list(
            request,
            queryset=Game.objects.filter(developer=company),
            template_name="games/game_list.html",
            template_object_name='games',
            extra_context={'developer': company}
    )


def games_by_platform(request, platform_slug):
    """View for games filtered by platform"""
    try:
        platform = Platform.objects.get(slug=platform_slug)
    except:
        raise Http404

    return list_detail.object_list(
            request,
            queryset=Game.objects.filter(platform=platform),
            template_name="games/game_list.html",
            template_object_name='games',
            extra_context={'platform': platform}
    )
