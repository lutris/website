# pylint: disable=C0103
import logging
from importlib import import_module

from django.conf import settings
from django.urls import include, re_path
from django.contrib import admin
from django.views.static import serve
from django_openid_auth.views import login_begin
from rest_framework.authtoken.views import obtain_auth_token

logger = logging.getLogger(__name__)
admin.autodiscover()


urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^grappelli/', include('grappelli.urls')),
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^admin/games/', include('games.urls.admin')),
    re_path(r'^select2/', include('django_select2.urls')),
    re_path(r'^openid/', include('django_openid_auth.urls')),
    re_path(r'^user/', include('accounts.urls')),
    re_path(r'^api/accounts/token', obtain_auth_token, name='accounts_get_token'),
    re_path(
        r'^api/accounts/auth',
        include('rest_framework.urls', namespace='rest_framework')
    ),
    re_path(r'^api/tosec', include('tosec.urls')),
    re_path(r'^api/runners', include('runners.runner_urls')),
    re_path(r'^api/runtime', include('runners.runtime_urls')),
    re_path(r'^api/games', include('games.urls.games')),
    re_path(r'^api/installers', include('games.urls.installers')),
    re_path(r'^games/', include('games.urls.pages')),
    re_path(r'^bundles', include('bundles.urls')),
    re_path(r'^email/', include('emails.urls')),
    re_path(
        r'^steam-login/',
        login_begin,
        kwargs={'login_complete_view': 'associate_steam'},
        name='steam_login'
    ),
    re_path(r'thegamesdb/', include('thegamesdb.urls')),
    re_path(r'^', include('common.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve,
                {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ]


signal_modules = {}

for app in settings.INSTALLED_APPS:
    signals_module = '%s.signals' % app
    try:
        signal_modules[app] = import_module(signals_module)
    except ImportError as e:
        pass
