"""Serializers for account models"""
# pylint: disable=too-few-public-methods
from rest_framework import serializers
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Users"""

    class Meta:
        """Model and field definitions"""
        model = User
        fields = (
            'id',
            'username',
            'email',
            'website',
            'avatar',
            'steamid',
            'is_staff',
        )
