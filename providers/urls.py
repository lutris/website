from django.urls import re_path

from . import views

urlpatterns = [
    re_path("^/ulwgl$", views.ulwgl_games, name="ulwgl-games"),
]
