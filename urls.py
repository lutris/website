from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView, RedirectView

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', TemplateView.as_view(template_name='index.html')),
    (r'^about$', TemplateView.as_view(template_name='static/about.html')),
    (r'^download/', TemplateView.as_view(template_name='static/download.html')),
    #(r'^games/', include('games.urls')),
    #(r'^accounts/', include('registration.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt')),
    (r'^favicon\.ico$', RedirectView(url='/media/images/favicon.ico')),
)

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
