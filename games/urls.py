from django.conf.urls.defaults import *
#from django.conf import settings
from django.views.generic import list_detail

from lutrisweb.games.models import Game
from lutrisweb.games.views import games_by_year, games_by_runner, games_by_genre

urlpatterns = patterns(
    '',
    url(r'^$', list_detail.object_list,
        {'queryset': Game.objects.all(),
            'template_object_name': 'games'}),
    url(r'(?P<slug>[\w\-]+)$',
        list_detail.object_detail,
        {'queryset': Game.objects.all(),
         'template_object_name': 'game'}),
    url(r'^genre/(?P<genre_slug>[\w\-]+$)', games_by_genre),
    url(r'^year/(?P<year>[\d]+$)', games_by_year),
    url(r'^runner/(?P<runner_slug>[\w\-])$', games_by_runner),
    url(r'^publisher/(?P<publisher_slug>[\w\-])$', games_by_publisher),
    url(r'^platform/(?P<platform_slug>[\w\-])$', games_by_platform)
)
