from django.http import JsonResponse

from providers.ulwgl import export_ulwgl_games


def ulwgl_games(request):
    return JsonResponse(
        {
            "games": export_ulwgl_games(),
        }
    )
