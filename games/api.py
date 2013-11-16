from django.conf.urls import url
from tastypie.resources import ModelResource
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie import fields
from . import models


class GameLibraryAuthorization(Authorization):
    def create_list(self, object_list, bundle):
        raise Unauthorized()

    def read_list(self, object_list, bundle):
        return object_list.filter(user=bundle.request.user)

    def delete_list(self, object_list, bundle):
        raise Unauthorized()


class GameResource(ModelResource):
    # pylint: disable=W0232, R0903
    class Meta:
        queryset = models.Game.objects.published()
        fields = ['name', 'slug', 'year', 'platforms', 'title_logo', 'icon']
        allowed_methods = ['get']
        detail_uri_name = 'slug'

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$"
                % self._meta.resource_name,
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail")
        ]


class GameLibraryResource(ModelResource):
    games = fields.ManyToManyField(GameResource, 'games', full=True)

    # pylint: disable=W0232, R0903
    class Meta:
        queryset = models.GameLibrary.objects.all()
        resource_name = 'library'
        authentication = ApiKeyAuthentication()
        authorization = GameLibraryAuthorization()
        detail_uri_name = 'user'

    def get_object_list(self, request):
        self._meta.queryset = models.GameLibrary.objects.filter(
            user=request.user
        )
        return super(GameLibraryResource, self).get_object_list(request)

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<user__username>[\w\d_.-]+)/$"
                % self._meta.resource_name,
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail")
        ]
