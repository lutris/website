# pylint: disable=C0103
from django.urls import path

from bundles import views

urlpatterns = [
    path('<slug:slug>/', views.BundleDetail.as_view(), name='bundle_detail'),
    path('', views.BundleList.as_view(), name='bundle_list'),
]
