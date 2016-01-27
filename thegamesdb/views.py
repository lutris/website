from django.shortcuts import render
from thegamesdb.api import get_games_list, get_game


def search(request):
    query = request.GET.get('q')
    if query:
        results = get_games_list(query)
    else:
        results = None
    return render(request, 'thegamesdb/search.html', {
        'results': results,
        'query': query
    })


def detail(request, game_id):
    game = get_game(game_id)
    print game
    return render(request, 'thegamesdb/detail.html', {'game': game})
