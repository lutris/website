from django.shortcuts import render
from django.http import JsonResponse
from thegamesdb.api import get_games_list, get_game


def _get_games_db_results(query):
    if query:
        return get_games_list(query)


def search(request):
    query = request.GET.get('q')
    results = _get_games_db_results(query)
    return render(request, 'thegamesdb/search.html', {
        'results': results,
        'query': query
    })


def search_json(request):
    query = request.GET.get('term')
    results = _get_games_db_results(query)
    return JsonResponse({
        'results': [
            {
                'text': "{} ({}, {})".format(
                    result['game_title'], result['release_date'], result['platform']
                ),
                'id': result['id']
            } for result in results
        ],
        'more': False
    })


def detail(request, game_id):
    game = get_game(game_id)
    print game
    return render(request, 'thegamesdb/detail.html', {'game': game})
