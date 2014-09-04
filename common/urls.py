# pylint: disable=E1120, C0103
from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from . import views

urlpatterns = patterns(
    'common.views',
    url(r'^$', "home",
        name="homepage"),
    url(r'^about/$',
        TemplateView.as_view(template_name='common/about.html'),
        name='about'),
    url(r'^downloads/$', views.Downloads.as_view(), name='downloads'),
    url(r'^contact/$',
        TemplateView.as_view(template_name='common/contact.html'),
        name='contact'),
    url(r'news/$', 'news_archives',
        name='news_archives'),
    url(r'news/feed/$', views.NewsFeed()),
    url(r'^news/(?P<slug>[\w-]+)', views.NewsDetails.as_view(),
        name='news_details'),
    url(r'^error-testing/', views.error_testing),
)
