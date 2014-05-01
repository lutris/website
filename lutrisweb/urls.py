# pylint: disable=C0103
import logging
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django_openid_auth.views import login_begin
from importlib import import_module
from games import api

from tastypie.api import Api

logger = logging.getLogger(__name__)

v1_api = Api(api_name='v1')
v1_api.register(api.GameLibraryResource())
v1_api.register(api.GameResource())

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^openid/', include('django_openid_auth.urls')),
    url(r'^user/', include('accounts.urls')),
    url(r'^api/', include(v1_api.urls)),
    url(r'^games/', include('games.urls')),
    url(r'^steam-login/', login_begin, kwargs={
        'login_complete_view': 'associate_steam'}, name='steam_login'),
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
        logger.debug('loading "%s" ..', signals_module)
        signal_modules[app] = import_module(signals_module)
    except ImportError as e:
        logger.warning(
            'failed to import "%s", reason: %s', (signals_module, str(e)))
