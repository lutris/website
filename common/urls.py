# pylint: disable=E1120, C0103
from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^$',
        views.home,
        name="homepage"),
    url(r'^about/$',
        TemplateView.as_view(template_name='common/about.html'),
        name='about'),
    url(r'^downloads/$',
        views.Downloads.as_view(),
        name='downloads'),
    url(r'^contact/$',
        TemplateView.as_view(template_name='common/contact.html'),
        name='contact'),
    url(r'news/$',
        views.news_archives,
        name='news_archives'),
    url(r'news/feed/$',
        views.NewsFeed(),
        name='news_feed'),
    url(r'^news/(?P<slug>[\w-]+)',
        views.NewsDetails.as_view(),
        name='news_details'),
    url(r'upload/',
        views.upload_file,
        name='upload_file'),
    url(r'^error-testing/', views.error_testing),
]
