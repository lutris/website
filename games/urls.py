from django.conf.urls.defaults import *
from django.conf import settings

from lutrisweb.games.models import Game

urlpatterns = patterns(
    'django.views.generic.list_detail',
    url(r'$', 'object_list', {'queryset': Game.objects.all()}),
    url(r'(/P<slug>[-\w]+)$', 'object_detail',
        {'queryset': Game.objects.all()})
)
