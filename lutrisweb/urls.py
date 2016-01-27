# pylint: disable=C0103
import logging
from importlib import import_module
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django_openid_auth.views import login_begin

from games import deprecated_api
from tastypie.api import Api

logger = logging.getLogger(__name__)
admin.autodiscover()


# Tastypie API will be deprecated in lutris 0.4.0
v1_api = Api(api_name='v1')
v1_api.register(deprecated_api.GameLibraryResource())
v1_api.register(deprecated_api.GameResource())


urlpatterns = patterns(
    '',
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^openid/', include('django_openid_auth.urls')),
    url(r'^user/', include('accounts.urls')),
    url(r'^api/accounts/token',
        'rest_framework.authtoken.views.obtain_auth_token',
        name='accounts_get_token'),
    url(r'^api/accounts/auth',
        include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/tosec', include('tosec.urls')),
    url(r'^api/runners', include('runners.runner_urls')),
    url(r'^api/runtime', include('runners.runtime_urls')),
    url(r'^api/games', include('games.drf_urls')),
    url(r'^api/', include(v1_api.urls)),
    url(r'^games/', include('games.urls')),
    url(r'^bundles', include('bundles.urls')),
    url(r'^steam-login/', login_begin, kwargs={
        'login_complete_view': 'associate_steam'}, name='steam_login'),
    url(r'thegamesdb/', include('thegamesdb.urls')),
    url(r'^', include('common.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns(
        'django.views.static',
        (r'^media/(?P<path>.*)$', 'serve',
         {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )


signal_modules = {}

for app in settings.INSTALLED_APPS:
    signals_module = '%s.signals' % app
    try:
        signal_modules[app] = import_module(signals_module)
    except ImportError as e:
        pass
