# pylint: disable=C0103
from django.conf.urls import url

from bundles import views

urlpatterns = [
    url(r'^/(?P<slug>[\w\-]+)$', views.BundleDetail.as_view(), name='bundle_detail'),
    url(r'^/?$', views.BundleList.as_view(), name='bundle_list'),
]
