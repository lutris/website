# pylint: disable=missing-docstring,too-few-public-methods
from rest_framework import serializers
from .models import Runner, RunnerVersion, Runtime


class RunnerVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunnerVersion
        fields = ('version', 'architecture', 'url', 'default')


class RunnerSerializer(serializers.ModelSerializer):
    versions = RunnerVersionSerializer(many=True)

    class Meta:
        model = Runner
        fields = ('name', 'slug', 'icon', 'website', 'versions')


class RuntimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Runtime
        fields = ('name', 'created_at', 'architecture', 'url')
