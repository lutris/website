"""Serializers for TOSEC"""
from rest_framework import serializers
from .models import TosecCategory, TosecGame, TosecRom


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TosecCategory
        fields = ('name', 'description', 'category',
                  'version', 'author', 'section')


class RomSerializer(serializers.ModelSerializer):
    class Meta:
        model = TosecRom
        fields = '__all__'


class GameSerializer(serializers.ModelSerializer):
    roms = RomSerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = TosecGame
        fields = ('name', 'description', 'category', 'roms')
