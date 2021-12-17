"""URL conf for the installer API"""
# pylint: disable=invalid-name
from __future__ import absolute_import
from django.urls import path, re_path
from games.views import installers as views


urlpatterns = [
    # Revision access by game slug
    path('/game/<slug:slug>/revisions',
         views.GameRevisionListView.as_view(),
         name='api_game_revisions_list'),
    path('/game/<slug:slug>/revisions/<int:pk>',
         views.InstallerRevisionDetailView.as_view(),
         name="api_game_installer_revision_detail"),

    # There's a typo in the URL provided in the client
    path('/games/<slug:slug>/revisions/<int:pk>',
         views.InstallerRevisionDetailView.as_view(),
         name="api_game_installer_revision_detail_client_typo_support"),

    # Revision access via installer pk
    path('/<int:pk>/revisions',
         views.InstallerRevisionListView.as_view(),
         name="api_installer_revision_list"),

    # Revision objects
    path('/revisions/<int:pk>',
         views.InstallerRevisionDetailView.as_view(),
         name="api_installer_revision_detail"),
    path('/revisions',
         views.RevisionListView.as_view(),
         name="api_revision_list"),

    # Issues
    re_path(r'/(?P<slug>[\w\-]+)/issues',
            views.InstallerIssueList.as_view(),
            name='api_installer_issue'),
    path('/<slug:game_slug>/issues/<slug:installer_slug>',
         views.InstallerIssueCreateView.as_view(),
         name='api_installer_issue_create'),
    path('/issues/<int:pk>',
         views.InstallerIssueView.as_view(),
         name='api_installer_issue_by_id'),
    path('/issue-replies/<int:pk>',
         views.InstallerIssueReplyView.as_view(),
         name='api_installer_issue_reply'),

    # WTF is this shit? Remove after migrating to Vue!
    path('/id/<int:pk>',
         views.InstallerDetailView.as_view(),
         name='api_installer_detail'),

    # Generic views
    re_path(r'/(?P<slug>[\w\-]+)/?',
            views.GameInstallerListView.as_view(),
            name='api_game_installer_list'),

    path('',
         views.InstallerListView.as_view(),
         name='api_installer_list'),

]
