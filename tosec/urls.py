from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns(
    '',
    url('^categories/', views.CategoryListView.as_view(),
        name='tosec_category_search'),
)
