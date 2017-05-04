# pylint: disable=C0103
from __future__ import absolute_import
from django.conf.urls import url
from games.views import achievements as views


urlpatterns = [
    url(r'^$', views.AchievementsView.as_view(),
        name='api_game_list')
]
