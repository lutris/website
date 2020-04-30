"""URLconf for runners"""
from django.urls import path
from . import views


urlpatterns = [  # pylint: disable=invalid-name
    path('', views.RunnerListView.as_view(), name='runner_list'),
    path('<slug:slug>/', views.RunnerDetailView.as_view(), name='runner_detail'),
    path('<slug:slug>/versions/', views.RunnerUploadView.as_view(), name='runner_upload')
]
