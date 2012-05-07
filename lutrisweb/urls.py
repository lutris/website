from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^about$', TemplateView.as_view(template_name='about.html')),
    url(r'^download/', TemplateView.as_view(template_name='download.html'),
       name="download"),
    url(r'^games/', include('games.urls')),
    url(r'^accounts/', include('registration.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
