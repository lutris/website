from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic import list_detail

from lutrisweb.games.models import Game
from lutrisweb.games.views import games_by_year, games_by_runner, games_by_genre
from lutrisweb.games.views import games_by_publisher, games_by_platform
from lutrisweb.games.views import games_by_developer, games_by_company, games_all

urlpatterns = patterns(
    '',
    url(r'^$', games_all),
    url(r'^genre/(?P<genre_slug>[\w\-]+$)', games_by_genre),
    url(r'^year/(?P<year>[\d]+)$', games_by_year),
    url(r'^runner/(?P<runner_slug>[\w\-]+)$', games_by_runner),
    url(r'^by-publisher/(?P<publisher_slug>[\w\-]+)$', games_by_publisher),
    url(r'^by-developer/(?P<developer_slug>[\w\-]+)$', games_by_developer),
    url(r'^by-company/(?P<company_slug>[\w\-]+)$', games_by_company),
    url(r'^platform/(?P<platform_slug>[\w\-]+)$', games_by_platform),
    url(r'(?P<slug>[\w\-]+)$',
        list_detail.object_detail,
        {'queryset': Game.objects.all(),
         'template_object_name': 'game'})
)
