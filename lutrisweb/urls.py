# pylint: disable=C0103
import logging
from importlib import import_module

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django_openid_auth.views import login_begin
from rest_framework.authtoken.views import obtain_auth_token

logger = logging.getLogger(__name__)
admin.autodiscover()


urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/games/', include('games.urls.admin')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^select2/', include('django_select2.urls')),
    url(r'^openid/', include('django_openid_auth.urls')),
    url(r'^user/', include('accounts.urls')),
    url(r'^api/accounts/token', obtain_auth_token, name='accounts_get_token'),
    url(r'^api/accounts/auth',
        include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/tosec', include('tosec.urls')),
    url(r'^api/runners', include('runners.runner_urls')),
    url(r'^api/runtime', include('runners.runtime_urls')),
    url(r'^api/games', include('games.urls.games')),
    url(r'^api/installers', include('games.urls.installers')),
    url(r'^games/', include('games.urls.pages')),
    url(r'^bundles', include('bundles.urls')),
    url(r'^email/', include('emails.urls')),
    url(r'^steam-login/', login_begin, kwargs={
        'login_complete_view': 'associate_steam'}, name='steam_login'),
    url(r'thegamesdb/', include('thegamesdb.urls')),
    url(r'^', include('common.urls')),
]

if settings.DEBUG:
    from django.views.static import serve
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ]


signal_modules = {}

for app in settings.INSTALLED_APPS:
    signals_module = '%s.signals' % app
    try:
        signal_modules[app] = import_module(signals_module)
    except ImportError as e:
        pass
