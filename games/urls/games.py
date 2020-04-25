# pylint: disable=C0103
from __future__ import absolute_import
from django.urls import path
from games.views import games as views


urlpatterns = [
    path('', views.GameListView.as_view(), name='api_game_list'),
    path('stats/', views.GameStatsView.as_view(), name='api_game_stats'),
    path('library/<username>/', views.GameLibraryView.as_view(), name='api_game_library'),
    path('<slug:slug>/', views.GameDetailView.as_view(), name='api_game_detail'),
    path('<slug:slug>/installers/', views.GameInstallersView.as_view(), name='api_game_installers')
]
