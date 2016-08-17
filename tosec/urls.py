# pylint: disable=C0103
from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^categories$', views.CategoryListView.as_view(),
        name='tosec_categories'),
    url(r'^games$', views.GameListView.as_view(),
        name='tosec_games'),
]
