"""URLconf for runners"""
from django.conf.urls import url
from . import views


urlpatterns = [  # pylint: disable=invalid-name
    url(r'^$', views.RunnerListView.as_view(), name='runner_list'),
    url(r'^/(?P<slug>[\w\-]+)$', views.RunnerDetailView.as_view(),
        name='runner_detail'),
    url(r'^/(?P<slug>[\w\-]+)/versions',
        views.RunnerUploadView.as_view(),
        name='runner_upload')
]
