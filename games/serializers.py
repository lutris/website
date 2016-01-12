from rest_framework import serializers
from platforms.models import Platform
from . import models


class PlatformSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Platform
        fields = ('name',)


class GenreSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Genre
        fields = ('name',)


class GameSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True)
    platforms = PlatformSerializer(many=True)

    class Meta(object):
        model = models.Game
        fields = (
            'name', 'slug', 'year', 'platforms', 'genres',
            'banner_url', 'icon_url', 'is_public', 'updated', 'steamid'
        )


class GameLibrarySerializer(serializers.ModelSerializer):
    games = GameSerializer(many=True)

    class Meta(object):
        model = models.GameLibrary
        fields = ('user', 'games')
