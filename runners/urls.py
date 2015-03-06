from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns(
    '',
    url(r'^$', views.RunnerListView.as_view(), name='runner_list'),
    url(r'^/(?P<slug>[\w\-]+)$', views.RunnerDetailView.as_view(),
        name='runner_detail'),
)
