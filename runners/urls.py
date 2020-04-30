# pylint: disable=C0103
from django.conf.urls import url

from runners import views

urlpatterns = [
    url(r"^/?$", views.RunnersList.as_view(), name='runners_list'),
    url(r"^/(?P<runner>[\w\-]+)/(?P<version>[\w\-\.\_]+)/games$",
        views.RunnerVersionGameList.as_view(),
        name="games_by_runner_version"),
    url(r"^/(?P<runner>[\w\-]+)/games$",
        views.RunnerGameList.as_view(),
        name="games_by_runner")
]
