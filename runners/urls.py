# pylint: disable=C0103
from django.urls import path, register_converter

from runners import converters, views

register_converter(converters.VersionConverter, 'version')

urlpatterns = [
    path("/", views.RunnersList.as_view(), name='runners_list'),
    path("/<slug:runner>/<version:version>/games",
         views.RunnerVersionGameList.as_view(),
         name="games_by_runner_version"),
    path("/<slug:runner>/games", views.RunnerGameList.as_view(), name="games_by_runner")
]
