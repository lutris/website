from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('games',
    (r'^$', 'views.index'),
    (r'^(P<id>\d+)/', 'views.show')
)
