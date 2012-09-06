from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^about$', TemplateView.as_view(template_name='about.html')),
    url(r'^download/', TemplateView.as_view(template_name='download.html'),
       name="download"),
    url(r'^games/', include('games.urls')),
    url(r'^accounts/', include('registration.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', "games.views.home", name="homepage"),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT,
            'show_indexes': True}),
    )
