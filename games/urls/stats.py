# pylint: disable=C0103
from __future__ import absolute_import
from django.conf.urls import url
from games.views import stats as views


urlpatterns = [
    url(r'^/set/(?P<stat_id>\d+)/(?P<value>.*)$', views.SetStatView.as_view(),
        name='api_game_list'),
    url(r'^/get/(?P<username>.*)/(?P<stat_id>\d+)$', views.GetStatView.as_view(),
        name='api_game_list')
]
