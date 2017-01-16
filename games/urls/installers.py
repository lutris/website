# pylint: disable=C0103
from __future__ import absolute_import
from django.conf.urls import url
from games.views import installers as views


urlpatterns = [
    url(r'^$',
        views.InstallerListView.as_view(),
        name='api_installer_list'),
    url(r'^(?P<pk>[\d]+)$',
        views.InstallerDetailView.as_view(),
        name='api_installer_detail'),
    url(r'(?P<pk>[\d]+)/revisions$',
        views.InstallerRevisionListView.as_view(),
        name="api_installer_revision_list"),
    url(r'(?P<installer_pk>[\d]+)/revisions/(?P<pk>[\d]+)$',
        views.InstallerRevisionDetailView.as_view(),
        name="api_installer_revision_detail"),
]
