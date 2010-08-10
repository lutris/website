from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'lutrisweb.static.views.index'),
    (r'^contribute/', 'lutrisweb.static.views.contribute'),
    (r'^download/', 'lutrisweb.static.views.download'),
    (r'^games/', include('lutrisweb.games.urls')),
    (r'^admin/', include(admin.site.urls)),
)

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
