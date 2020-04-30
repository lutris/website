# pylint: disable=E1120, C0103
from django.conf.urls import url
from thegamesdb import views


urlpatterns = [
    url(r'^$', views.search, name='tgb.search'),
    url(r'^search.json', views.search_json, name='tgd.search_json'),
    url(r'^(\d+).json$', views.detail_to_lutris, name='tgd.detail'),
]
