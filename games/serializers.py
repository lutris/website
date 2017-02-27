from reversion.models import Version
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
            'banner_url', 'icon_url', 'is_public', 'updated', 'steamid',
            'gogid', 'humblestoreid',
        )


class GameLibrarySerializer(serializers.ModelSerializer):
    games = GameSerializer(many=True)

    class Meta(object):
        model = models.GameLibrary
        fields = ('user', 'games')


class InstallerSerializer(serializers.ModelSerializer):
    script = serializers.ReadOnlyField(source='raw_script')
    game = serializers.HyperlinkedRelatedField(
        view_name='api_game_detail',
        read_only=True,
        lookup_field='slug'
    )
    user = serializers.StringRelatedField()

    runner = serializers.StringRelatedField()

    class Meta(object):
        model = models.Installer
        fields = ('game', 'user', 'runner', 'slug', 'version', 'description',
                  'notes', 'created_at', 'updated_at', 'published', 'rating', 'script')


class GameInstallersSerializer(GameSerializer):
    installers = InstallerSerializer(many=True)

    class Meta(object):
        model = models.Game
        fields = (
            'name', 'slug', 'year', 'platforms', 'genres',
            'banner_url', 'icon_url', 'is_public', 'updated', 'steamid',
            'gogid', 'humblestoreid', 'installers'
        )


class InstallerRevisionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    data = serializers.JSONField()
    comment = serializers.CharField()
    created_at = serializers.DateTimeField()
    installer = serializers.IntegerField()


class InstallerWithRevisionsSerializer(InstallerSerializer):
    revisions = InstallerRevisionSerializer(many=True)

    class Meta(object):
        model = models.Installer
        fields = ('game', 'user', 'runner', 'slug', 'version', 'description',
                  'notes', 'created_at', 'updated_at', 'published', 'rating',
                  'script', 'content', 'revisions')


class GameRevisionSerializer(GameSerializer):
    installers = InstallerWithRevisionsSerializer(many=True)

    class Meta(object):
        model = models.Game
        fields = (
            'name', 'slug', 'year', 'platforms', 'genres',
            'banner_url', 'icon_url', 'is_public', 'updated', 'steamid',
            'gogid', 'humblestoreid', 'installers'
        )
