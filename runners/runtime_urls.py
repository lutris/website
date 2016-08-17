# pylint: disable=C0103
from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.RuntimeView.as_view(), name='runtime'),
]
