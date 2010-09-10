# Create your views here.
from django.http import Http404
from django.views.generic import list_detail
from django.template.context import RequestContext
#from django.http import HttpResponse
from django.shortcuts import render_to_response
from lutrisweb.games.models import Game, Runner, Genre, Platform, Publisher

def index(request):
    games = Game.objects.all()
    return render_to_response('games/index.html',
                              {'games' : games},
                              RequestContext(request))

def games_by_runner(request, runner_slug):
    try:
        runner = Runner.objects.get(slug=runner_slug)
    except Runner.DoesNotExist:
        raise Http404
    return list_detail.object_list(
            request,
            queryset = Game.objects.filter(runner=runner),
            template_name = "games/game_list.html",
            template_object_name = "games",
            extra_context = { "runner": runner }
    )

def games_by_year(request, year):
    return list_detail.object_list(
            request,
            queryset = Game.objects.filter(year=year),
            template_name = "games/game_list.html",
            template_object_name = "games",
            extra_context = {"year": year}
    )

def games_by_genre(request, genre_slug):
    try:
        genre = Genre.objects.get(slug_iexact=genre_slug)
    except Genre.DoesNotExist:
        raise Http404
    return list_detail.object_list(
            request,
            queryset = Game.objects.filter(genre=genre),
            template_name = "games/game_list.html",
            template_object_name = "games",
            extra_context = {'genre': genre}
    )

def games_by_publisher(request, publisher_slug):
    try:
        publisher = Publisher.objects.get(slug=publisher_slug)
    except:
        raise Http404

    return list_detail.object_list(
            request,
            queryset = Game.objects.filter(publisher=publisher),
            template_name = "games/game_list.html",
            template_object_name = 'games',
            extra_context = {'publisher': publisher}
    )

    def games_by_platform(request, platform_slug):
        try:
            platform = Platform.objects.get(slug=platform_slug)
        except:
            raise Http404

        return list_detail.object_list(
                request,
                queryset = Game.objects.filter(platform=platform),
                template_name = "games/game_list.html",
                template_object_name = 'games',
                extra_context = {'platform': platform}
        )
