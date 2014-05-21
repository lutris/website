# pylint: disable=C0103
from django.conf.urls import patterns, include, url
from .api import GameLibraryResource

from tastypie.api import Api

v1_api = Api(api_name='v1')
v1_api.register(GameLibraryResource())

urlpatterns = patterns(
    url(r'^', include(v1_api.urls)),
)
