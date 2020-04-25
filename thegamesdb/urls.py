# pylint: disable=E1120, C0103
from django.urls import path, re_path
from thegamesdb import views


urlpatterns = [
    path('', views.search, name='tgb.search'),
    path('search.json', views.search_json, name='tgd.search_json'),
    re_path(r'^(\d+).json$', views.detail_to_lutris, name='tgd.detail'),
]
