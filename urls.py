from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.views.generic.simple import direct_to_template

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'index.html'}),
    (r'^about$', direct_to_template, {'template': 'static/about.html'}),
    (r'^download/', direct_to_template, {'template': 'static/download.html'}),
    (r'^games/', include('lutrisweb.games.urls')),
    (r'^login/', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^logout/', 'django.contrib.auth.views.logout', {'template_name': 'index.html'}),
    (r'^register/$', 'accounts.views.register'),
    (r'^admin/', include(admin.site.urls)),
)

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
