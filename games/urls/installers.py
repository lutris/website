# pylint: disable=C0103
from __future__ import absolute_import
from django.conf.urls import url
from games.views import games as views


urlpatterns = [
    url(r'^$', views.InstallerListView.as_view(),
        name='api_installer_list'),
]
