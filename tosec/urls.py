# pylint: disable=C0103
from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns(
    '',
    url(r'^categories$', views.CategoryListView.as_view(),
        name='tosec_categories'),
    url(r'^games$', views.GameListView.as_view(),
        name='tosec_games'),
)
