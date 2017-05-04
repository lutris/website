# pylint: disable=C0103
from __future__ import absolute_import
from django.conf.urls import url
from games.views import achievements as views


urlpatterns = [
    url(r'^/unlock/(?P<achievement_id>\d+)$', views.UnlockAchievementView.as_view(),
        name='api_game_list'),
    url(r'^/get/(?P<username>.*)/(?P<achievement_id>\d+)$', views.GetAchievementsView.as_view(),
        name='api_game_list')
]
