from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns(
    'games.views',
    url(r'^$', "home",
        name="homepage"),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'),
        name='about'),
    url(r'^download/', TemplateView.as_view(template_name='download.html'),
        name="download"),
)
