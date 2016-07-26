from django.conf.urls import url
from emails import views


urlpatterns = [
    url(r'^example$', views.example_email, name='example_email'),
    url(r'^send-test$', views.email_sender_test, name='email_sender_test'),
]
