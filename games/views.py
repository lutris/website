from django.http import Http404
from django.views.generic import list_detail
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from lutrisweb.games.models import Game, Runner, Genre, Platform, Company

def games_all(request):
    return list_detail.object_list(
            request,
            queryset = Game.objects.all(),
            template_name = "games/game_list.html",
            template_object_name = "games"
            )

def games_by_runner(request, runner_slug):
    try:
        runner = Runner.objects.get(slug=runner_slug)
    except Runner.DoesNotExist:
        raise Http404
    return list_detail.object_list(
            request,
            queryset = Game.objects.filter(runner__slug=runner.slug),
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
        genre = Genre.objects.get(slug=genre_slug)
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
        company = Company.objects.get(slug=publisher_slug)
    except:
        raise Http404

    return list_detail.object_list(
            request,
            queryset = Game.objects.filter(publisher=company),
            template_name = "games/game_list.html",
            template_object_name = 'games',
            extra_context = {'publisher': company}
    )

def games_by_developer(request, developer_slug):
    try:
        company = Company.objects.get(slug=developer_slug)
    except:
        raise Http404

    return list_detail.object_list(
            request,
            queryset = Game.objects.filter(developer=company),
            template_name = "games/game_list.html",
            template_object_name = 'games',
            extra_context = {'developer': company}
    )
def games_by_company(request, company_slug):
    try:
        company = Company.objects.get(slug=developer_slug)
    except:
        raise Http404

    return list_detail.object_list(
            request,
            queryset = Game.objects.filter(developer=company),
            template_name = "games/game_list.html",
            template_object_name = 'games',
            extra_context = {'developer': company}
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


