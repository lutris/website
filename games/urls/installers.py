# pylint: disable=C0103
from __future__ import absolute_import
from django.conf.urls import url
from games.views import installers as views


urlpatterns = [
    url(r'game/(?P<slug>[\w\-]+)/revisions$',
        views.GameRevisionListView.as_view(),
        name='api_game_revisions_list'),

    url(r'game/(?P<slug>[\w\-]+)/revisions/(?P<pk>[\d]+)',
        views.InstallerRevisionDetailView.as_view(),
        name="api_game_installer_detail"),

    url(r'(?P<pk>[\d]+)/revisions$',
        views.InstallerRevisionListView.as_view(),
        name="api_installer_revision_list"),
    url(r'revisions/(?P<pk>[\d]+)$',
        views.InstallerRevisionDetailView.as_view(),
        name="api_installer_revision_detail"),

    url(r'id/(?P<pk>[\d]+)$',
        views.InstallerDetailView.as_view(),
        name='api_installer_detail'),
    url(r'(?P<slug>[\w\-]+)$',
        views.GameInstallerListView.as_view(),
        name='api_game_installer_list'),
    url(r'^$',
        views.InstallerListView.as_view(),
        name='api_installer_list'),

]
