"""URL patterns for regression API"""
from django.urls import path
from games.views import regressions as views

urlpatterns = [
    path('', views.RegressionListView.as_view(), name='api_regression_list'),
    path('/<int:pk>', views.RegressionDetailView.as_view(), name='api_regression_detail'),
]
