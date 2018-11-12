"""URL conf for the installer API"""
# pylint: disable=invalid-name
from __future__ import absolute_import
from django.conf.urls import url
from games.views import installers as views


urlpatterns = [
    # Revisions
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

    # Issues
    url(r'(?P<slug>[\w\-]+)/issues$',
        views.InstallerIssueView.as_view(),
        name='api_installer_issue'),
    url(r'(?P<game_slug>[\w\-]+)/issues/(?P<installer_slug>[\w\-]+)$',
        views.InstallerIssueCreateView.as_view(),
        name='api_installer_issue_create'),

    # WTF is this shit? Remove after migrating to Vue!
    url(r'id/(?P<pk>[\d]+)$',
        views.InstallerDetailView.as_view(),
        name='api_installer_detail'),

    # Generic views
    url(r'(?P<slug>[\w\-]+)$',
        views.GameInstallerListView.as_view(),
        name='api_game_installer_list'),
    url(r'^$',
        views.InstallerListView.as_view(),
        name='api_installer_list'),
]
