from django.http import JsonResponse

from providers.umu import export_umu_games


def umu_games(request):
    return JsonResponse(export_umu_games(), safe=False)
