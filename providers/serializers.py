"""DRF serializers for providers models"""
# pylint: disable=too-few-public-methods
from rest_framework import serializers
from providers.models import Provider, ProviderGame


class ProviderSerializer(serializers.ModelSerializer):
    """Serializer for Providers"""
    class Meta:
        """Model and field definitions"""
        model = Provider
        fields = ('name',)


class ProviderGameSerializer(serializers.ModelSerializer):
    """Serializer for ProviderGames"""
    service = serializers.SerializerMethodField()

    class Meta:
        """Model and field definitions"""
        model = ProviderGame
        fields = ('name', 'slug', 'service')

    def get_service(self, obj):
        """Return provider name"""
        return obj.provider.name
