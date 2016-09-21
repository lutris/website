# pylint: disable=C0103
from django.conf.urls import url
from . import api_views as views


urlpatterns = [
    url(r'^$', views.GameListView.as_view(),
        name='api_game_list'),
    url(r'/library/(?P<username>.*)$', views.GameLibraryView.as_view(),
        name='api_game_library'),
    url(r'^/(?P<slug>[\w\-]+)$', views.GameDetailView.as_view(),
        name='api_game_detail'),
    url(r'^/(?P<slug>[\w\-]+)/installers$', views.GameInstallersView.as_view(),
        name='api_game_installers'),
]
