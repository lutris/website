# pylint: disable=C0103
from django.conf.urls import patterns, url
from . import api_views as views


urlpatterns = patterns(
    '',
    url(r'^$', views.GameListView.as_view(),
        name='api_game_list'),
    url(r'/library/(?P<username>.*)$', views.GameLibraryView.as_view(),
        name='api_game_library'),
    url(r'^/(?P<slug>[\w\-]+)$', views.GameDetailView.as_view(),
        name='api_game_detail')
)
