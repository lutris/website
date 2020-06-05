# pylint: disable=E1120, C0103
from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.home, name="homepage"),
    path('about/', TemplateView.as_view(template_name='common/about.html'),
         name='about'),
    path('downloads/', views.Downloads.as_view(), name='downloads'),
    path('news/', views.news_archives, name='news_archives'),
    path('news/feed/', views.NewsFeed(), name='news_feed'),
    path('news/<slug:slug>/', views.NewsDetails.as_view(),
         name='news_details'),
    path('upload/', views.upload_file, name='upload_file'),
    path('faq', TemplateView.as_view(template_name='common/faq.html'),
         name='faq'),
    path('donate', TemplateView.as_view(template_name='common/donate.html'),
         name='donate')
]
