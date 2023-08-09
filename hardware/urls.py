"""Hardware URLconf"""
# pylint: disable=invalid-name
from django.urls import path
from . import views


urlpatterns = [
    path('/features', views.HardwareInfoView.as_view(), name='hardware_features'),
]
