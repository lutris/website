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
)
