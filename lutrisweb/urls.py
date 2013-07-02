from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings

from games import api

from tastypie.api import Api

v1_api = Api(api_name='v1')
v1_api.register(api.GameLibraryResource())
v1_api.register(api.GameResource())

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('registration.urls')),
    url(r'^user/', include('accounts.urls')),
    url(r'^api/', include(v1_api.urls)),
    url(r'^games/', include('games.urls')),
    url(r'^', include('common.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns(
        'django.views.static',
        (r'^media/(?P<path>.*)$', 'serve',
         {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
