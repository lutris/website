# pylint: disable=C0103
from django.urls import path, re_path

from bundles import views

urlpatterns = [
    path('/<slug:slug>', views.BundleDetail.as_view(), name='bundle_detail'),
    re_path(r'/?$', views.BundleList.as_view(), name='bundle_list'),
]
