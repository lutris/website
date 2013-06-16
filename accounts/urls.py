from django.conf.urls import patterns, url

urlpatterns = patterns(
    'accounts.views',
    url(r'^auth/$', 'client_auth', name="client_auth"),
    url(r'^verify/$', 'client_verify'),
)
