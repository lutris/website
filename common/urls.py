# pylint: disable=E1120, C0103
from django.urls import re_path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    re_path('^/?$', views.home, name="homepage"),
    re_path('^about/?$', TemplateView.as_view(template_name='common/about.html'), name='about'),
    re_path('^downloads/?$', views.Downloads.as_view(), name='downloads'),
    re_path('^upload/?$', views.upload_file, name='upload_file'),
    re_path('^faq/?$', TemplateView.as_view(template_name='common/faq.html'), name='faq'),
    re_path('^donate/?$', TemplateView.as_view(template_name='common/donate.html'), name='donate'),
]
