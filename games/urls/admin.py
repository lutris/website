"""Routing for custom admin views"""

# pylint: disable=E1120, C0103
from django.urls import path
from games.views import admin as views


urlpatterns = [
    path('change-submissions/', views.list_change_submissions_view, name='admin-change-submissions'),
    path('change-submissions/<int:game_id>',
         views.list_change_submissions_view,
         name='admin-change-submissions'),
    path('change-submission/<int:submission_id>/',
         views.review_change_submission_view,
         name='admin-change-submission'),
    path('change-submission/<int:submission_id>/accept',
         views.change_submission_accept,
         name='admin-change-submission-accept'),
    path('change-submission/<int:submission_id>/reject',
         views.change_submission_reject,
         name='admin-change-submission-reject'),
]
