"""Game resources for the API"""
# pylint: disable=invalid-name
from __future__ import absolute_import
from django.urls import re_path, path
from accounts import views

urlpatterns = [
    re_path('/me/?', views.UserDetailView.as_view(), name='api_user_detail_legacy'),
    re_path('/details', views.UserDetailView.as_view(), name='api_user_detail'),
    path('/library', views.GameLibraryAPIView.as_view(), name="api_user_library"),
]
