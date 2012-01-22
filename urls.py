from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.views.generic.simple import direct_to_template, redirect_to

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'index.html'}),
    (r'^about$', direct_to_template, {'template': 'static/about.html'}),
    (r'^download/', direct_to_template, {'template': 'static/download.html'}),
    (r'^games/', include('lutrisweb.games.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^robots\.txt$', direct_to_template, {'template': 'robots.txt', 'mimetype': 'text/plain'},),
    (r'^favicon\.ico$', redirect_to, {'url': '/media/images/favicon.ico'}),
)

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
