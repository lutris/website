from tastypie.resources import ModelResource
from tastypie import fields
from . import models


class GameResource(ModelResource):
    class Meta:
        queryset = models.Game.objects.published()
        fields = ['name', 'slug', 'year', 'platforms']
        allowed_methods = ['get']


class GameLibraryResource(ModelResource):
    games = fields.ManyToManyField(GameResource, 'games')

    class Meta:
        queryset = models.GameLibrary.objects.all()
        resource_name = 'library'
