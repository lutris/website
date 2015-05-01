from rest_framework import serializers
import models


class GameSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Game
        fields = ('name', 'slug', 'year', 'platforms', 'genres')
