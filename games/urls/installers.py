"""URL conf for the installer API"""
# pylint: disable=invalid-name
from __future__ import absolute_import
from django.urls import path, re_path
from games.views import installers as views
from games.views import deprecated


urlpatterns = [
    # URLs used in the client to install drafts
    path('/game/<slug:slug>/revisions/<int:pk>',
         views.InstallerDraftDetailView.as_view(),
         name="api_game_installer_revision_detail"),
    # There's a typo in the URL provided in the client (Fixed in Jan 2023)
    path('/games/<slug:slug>/revisions/<int:pk>',
         views.InstallerDraftDetailView.as_view(),
         name="api_game_installer_revision_detail_client_typo_support"),

    # Drafts
    path('/drafts/<int:pk>',
         views.InstallerDraftDetailView.as_view(),
         name="api_installer_draft_detail"),
    path('/drafts',
         views.InstallerDraftListView.as_view(),
         name="api_installer_draft_list"),

    # Issues
    re_path(r'/(?P<slug>[\w\-]+)/issues',
            deprecated.InstallerIssueList.as_view(),
            name='api_installer_issue'),
    path('/<slug:game_slug>/issues/<slug:installer_slug>',
         deprecated.InstallerIssueCreateView.as_view(),
         name='api_installer_issue_create'),
    path('/issues/<int:pk>',
         deprecated.InstallerIssueView.as_view(),
         name='api_installer_issue_by_id'),
    path('/issue-replies/<int:pk>',
         deprecated.InstallerIssueReplyView.as_view(),
         name='api_installer_issue_reply'),

    # History
    path('/<int:installer_id>/history',
         views.InstallerHistoryView.as_view(),
         name='api_installer_history'),
    path('/history',
         views.InstallerHistoryListView.as_view(),
         name='api_installer_history_list'),

    # Generic views
    path('/id/<int:pk>',
         views.InstallerDetailView.as_view(),
         name='api_installer_detail'),
    re_path(r'/(?P<slug>[\w\-]+)/?',
            views.GameInstallerListView.as_view(),
            name='api_game_installer_list'),
    path('',
         views.InstallerListView.as_view(),
         name='api_installer_list'),

]
