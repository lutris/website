# pylint: disable=C0103
from django.conf.urls import patterns, url
from bundles.views import BundleList, BundleDetail


urlpatterns = patterns(
    'bundles.views',
    url(r'^/(?P<slug>[\w\-]+)$', BundleDetail.as_view(), name='bundle_detail'),
    url(r'^/?$', BundleList.as_view(), name='bundle_list'),
)
