"""Runtime API urls"""
# pylint: disable=invalid-name
from django.urls import path
from . import views


urlpatterns = [
    path('', views.RuntimeListView.as_view(), name='runtime_list'),
    path('/<slug:name>', views.RuntimeDetailView.as_view(), name='runtime_detail'),
]
