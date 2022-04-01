# pylint: disable=missing-docstring
from django.http import JsonResponse
from django.conf import settings
from django.views.generic import TemplateView


class Downloads(TemplateView):
    template_name = "common/downloads.html"

    def get_context_data(self, **kwargs):
        context = super(Downloads, self).get_context_data(**kwargs)
        context['version'] = settings.CLIENT_VERSION
        context['download_url'] = 'https://lutris.net/releases/'
        return context


def server_status(_request):
    """Simple availability check"""
    return JsonResponse({"status": "ok"})
