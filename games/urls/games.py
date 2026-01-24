"""Game resources for the API"""
# pylint: disable=invalid-name
from __future__ import absolute_import
from django.urls import path
from games.views import games as views


urlpatterns = [
     path('', views.GameListView.as_view(), name='api_game_list'),
     path('/service/<slug:service>',
          views.ServiceGameListView.as_view(),
          name='api_service_game_list'),
     path('/screenshots', views.ScreenshotView.as_view(), name='api_screenshots_list'),
     path('/screenshots/<int:screenshot_id>', views.ScreenshotReviewView.as_view(), name="api_screenshot_review"),
     path('/stats', views.GameStatsView.as_view(), name='api_game_stats'),
     path('/submissions', views.GameSubmissionsView.as_view(), name='api_game_submissions'),
     path('/submissions/<int:submission_id>', views.GameSubmissionAcceptView.as_view(), name='api_game_submission_accept'),
     path('/changes', views.GameChangesView.as_view(), name='api_game_changes'),
     path('/library/<str:username>', views.GameLibraryView.as_view(), name='api_game_library'),
     path('/merge-suggestions',
          views.GameMergeSuggestionsView.as_view(),
          name='api_merge_suggestions'),
     path('/merge-suggestions/<int:suggestion_id>',
          views.GameMergeSuggestionAcceptView.as_view(),
          name='api_merge_suggestion_accept'),
     path('/<slug:slug>', views.GameDetailView.as_view(), name='api_game_detail'),
     path('/<slug:slug>/installers', views.GameInstallersView.as_view(), name='api_game_installers'),
     path('/<slug:slug>/merge/<slug:other_slug>',
          views.GameMergeView.as_view(),
          name='api_game_merge'),
]
