"""URLconf for email app"""
from django.urls import path
from emails import views


# pylint: disable=C0103
urlpatterns = [
    path('example/', views.example_email, name='example_email'),
    path('send-test/', views.email_sender_test, name='email_sender_test'),
]
