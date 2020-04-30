"""Routing for custom admin views"""

# pylint: disable=E1120, C0103
from __future__ import absolute_import
from django.conf.urls import url
from games.views import admin as views


urlpatterns = [
    url(r'^change-submissions/$',
        views.list_change_submissions_view,
        name='admin-change-submissions'),
    url(r'^change-submissions/(?P<game_id>\d+)$',
        views.list_change_submissions_view,
        name='admin-change-submissions'),
    url(r'^change-submission/(?P<submission_id>\d+)/$',
        views.review_change_submission_view,
        name='admin-change-submission'),
    url(r'^change-submission/(?P<submission_id>\d+)/accept$',
        views.change_submission_accept,
        name='admin-change-submission-accept'),
    url(r'^change-submission/(?P<submission_id>\d+)/reject$',
        views.change_submission_reject,
        name='admin-change-submission-reject'),
]
