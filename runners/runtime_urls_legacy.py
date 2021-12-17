"""Runtime API urls"""
# pylint: disable=invalid-name
from django.urls import path
from . import views


urlpatterns = [
    path('', views.RuntimeLegacyListView.as_view(), name='runtime'),
]
