"""TOSEC URLconf"""
# pylint: disable=invalid-name
from django.urls import path, re_path
from . import views


urlpatterns = [
    path('categories', views.CategoryListView.as_view(), name='tosec_categories'),
    path('games', views.GameListView.as_view(), name='tosec_games'),
]
