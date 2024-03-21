from django.urls import re_path

from . import views

urlpatterns = [
    re_path("^/umu$", views.umu_games, name="umu-games"),
]
