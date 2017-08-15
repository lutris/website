from rest_framework import serializers

from games import models
from platforms.models import Platform


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
            'gogslug', 'humblestoreid',
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
    game_slug = serializers.ReadOnlyField(source='game.slug')
    name = serializers.ReadOnlyField(source='game.name')
    year = serializers.ReadOnlyField(source='game.year')
    steamid = serializers.ReadOnlyField(source='game.steamid')
    gogslug = serializers.ReadOnlyField(source='game.gogslug')
    humblestoreid = serializers.ReadOnlyField(source='game.humblestoreid')

    user = serializers.StringRelatedField()

    runner = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta(object):
        model = models.Installer
        fields = ('id', 'game', 'game_slug', 'name', 'year', 'user', 'runner', 'slug',
                  'version', 'description', 'notes', 'created_at', 'updated_at', 'draft',
                  'published', 'rating', 'steamid', 'gogslug', 'humblestoreid',
                  'script', 'content')


class GameInstallersSerializer(GameSerializer):
    installers = InstallerSerializer(many=True)

    class Meta(object):
        model = models.Game
        fields = (
            'id', 'name', 'slug', 'year', 'platforms', 'genres',
            'banner_url', 'icon_url', 'is_public', 'updated',
            'steamid', 'gogslug', 'humblestoreid', 'installers'
        )


class InstallerRevisionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    game = serializers.HyperlinkedRelatedField(
        view_name='api_game_detail',
        read_only=True,
        lookup_field='slug'
    )
    game_slug = serializers.ReadOnlyField(source='game.slug')
    name = serializers.ReadOnlyField(source='game.name')
    year = serializers.ReadOnlyField(source='game.year')
    user = serializers.StringRelatedField()
    runner = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    slug = serializers.CharField()
    version = serializers.CharField()
    description = serializers.CharField()
    notes = serializers.CharField()
    created_at = serializers.DateTimeField()
    draft = serializers.BooleanField()
    published = serializers.BooleanField()
    rating = serializers.CharField()

    steamid = serializers.ReadOnlyField(source='game.steamid')
    gogslug = serializers.ReadOnlyField(source='game.gogslug')
    humblestoreid = serializers.ReadOnlyField(source='game.humblestoreid')

    script = serializers.JSONField()
    content = serializers.CharField()
    comment = serializers.CharField()
    installer_id = serializers.IntegerField()


class InstallerWithRevisionsSerializer(InstallerSerializer):
    revisions = InstallerRevisionSerializer(many=True)

    class Meta(object):
        model = models.Installer
        fields = ('id', 'game', 'user', 'runner', 'slug', 'version', 'description', 'draft',
                  'notes', 'created_at', 'updated_at', 'published', 'rating',
                  'script', 'content', 'revisions')


class GameRevisionSerializer(GameSerializer):
    installers = InstallerWithRevisionsSerializer(many=True)

    class Meta(object):
        model = models.Game
        fields = (
            'name', 'slug', 'year', 'platforms', 'genres',
            'banner_url', 'icon_url', 'is_public', 'updated', 'steamid',
            'gogslug', 'humblestoreid', 'installers'
        )
