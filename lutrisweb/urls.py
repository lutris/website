# pylint: disable=C0103
import logging
from importlib import import_module

from django.conf import settings
from django.urls import include, re_path, path
from django.contrib import admin
from django.views.static import serve
from django_openid_auth.views import login_begin
from rest_framework.authtoken.views import obtain_auth_token
from accounts.views import UserDetailView
from bundles.views import BundleView

logger = logging.getLogger(__name__)
admin.autodiscover()


urlpatterns = [
    path('admin/', admin.site.urls),
    path('grappelli/', include('grappelli.urls')),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/games/', include('games.urls.admin')),
    path('select2/', include('django_select2.urls')),
    path('openid/', include('django_openid_auth.urls')),
    path('user/', include('accounts.urls')),
    path('api/accounts/token', obtain_auth_token, name='accounts_get_token'),
    path(
        'api/accounts/auth',
        include('rest_framework.urls', namespace='rest_framework')
    ),
    path('api/tosec', include('tosec.urls')),
    path('api/runners', include('runners.runner_urls')),
    path('api/runtime', include('runners.runtime_urls')),
    path('api/games', include('games.urls.games')),
    path('api/installers', include('games.urls.installers')),
    re_path('api/users/me/?', UserDetailView.as_view(), name='api_user_detail'),
    path('api/bundles/<slug:slug>', BundleView.as_view(), name='api_bundle_view'),
    path('games', include('games.urls.pages')),
    path('bundles', include('bundles.urls')),
    path('runners', include('runners.urls')),
    path('email/', include('emails.urls')),
    path(
        'steam-login/',
        login_begin,
        kwargs={'login_complete_view': 'associate_steam'},
        name='steam_login'
    ),
    path('thegamesdb/', include('thegamesdb.urls')),
    path('', include('common.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve,
                {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ]

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

signal_modules = {}

for app in settings.INSTALLED_APPS:
    signals_module = '%s.signals' % app
    try:
        signal_modules[app] = import_module(signals_module)
    except ImportError as e:
        pass
