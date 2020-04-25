# pylint: disable=C0103
from django.urls import path
from . import views


urlpatterns = [
    path('', views.RuntimeView.as_view(), name='runtime'),
]
