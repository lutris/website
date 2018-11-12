"""Runner URL conf"""
# pylint: disable=invalid-name
from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.RunnerListView.as_view(), name='runner_list'),
    url(r'^(?P<slug>[\w\-]+)$', views.RunnerDetailView.as_view(),
        name='runner_detail'),
    url(r'^(?P<slug>[\w\-]+)/versions',
        views.RunnerUploadView.as_view(),
        name='runner_upload')
]
