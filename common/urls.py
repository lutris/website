from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns(
    'common.views',
    url(r'^$', "home",
        name="homepage"),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'),
        name='about'),
    url(r'^download/', TemplateView.as_view(template_name='download.html'),
        name="download"),
    url(r'^news/(?P<slug>[\w-]+)', 'news_details', name='news_details'),
    url(r'news/all/?$', 'news_archives',
        name='news_archives'),
)
