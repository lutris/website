from django.conf.urls import patterns, url
from django.contrib.auth import views as auth_views

from . import forms

urlpatterns = patterns(
    'accounts.views',
    url(r'^login/$', auth_views.login,
        {'authentication_form': forms.LoginForm}, name="login"),
    url(r'^register/$', 'register', name="register"),
    url(r'^auth/$', 'client_auth', name="client_auth"),
    url(r'^verify/$', 'client_verify'),
    url(r'^associate-steam/', 'associate_steam', name="associate_steam"),
    url(r'^(?P<username>[\w-]+)/library/$', 'library_show',
        name="library_show"),
    url(r'^library/add/(?P<slug>[\w-]+)/$', 'library_add',
        name="add_to_library"),
    url(r'^library/remove/(?P<slug>[\w-]+)/$', 'library_remove',
        name="remove_from_library"),
    url(r'^library/steam-sync/', 'library_steam_sync',
        name="library_steam_sync"),
    url(r'(.*)/$', 'user_account', name="user_account"),
)
