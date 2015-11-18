from django.conf.urls import patterns, url
from . import api_views as views


urlpatterns = patterns(
    '',
    url(r'^$', views.GameListView.as_view(),
        name='api_game_list'),
    url(r'^/banners', views.GameBannersView.as_view(), name='api_banners'),
    url(r'^/(?P<slug>[\w\-]+)$', views.GameDetailView.as_view(),
        name='api_game_detail')
)
