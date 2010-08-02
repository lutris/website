from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('games',
    (r'^$', 'lutrisweb.games.views.index'),
    (r'^(P<id>\d+)/', 'lutrisweb.games.views.show')
)
