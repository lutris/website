"""Serializers for account models"""
# pylint: disable=too-few-public-methods
from rest_framework import serializers
from accounts.models import User
from games.models import LibraryGame

class UserSerializer(serializers.ModelSerializer):
    """Serializer for Users"""

    class Meta:
        """Model and field definitions"""

        model = User
        fields = (
            "id",
            "username",
            "email",
            "avatar_url",
            "steamid",
            "is_staff",
        )


class LibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryGame
        fields = (
            "name",
            "slug",
            "banner",
            "coverart",
            "icon",
            "playtime",
        )