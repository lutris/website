from rest_framework import serializers
from .models import Runner, RunnerVersion, Runtime


class RunnerVersionSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = RunnerVersion
        fields = ('version', 'architecture', 'url', 'default')


class RunnerSerializer(serializers.ModelSerializer):
    versions = RunnerVersionSerializer(many=True)

    class Meta(object):
        model = Runner
        fields = ('name', 'slug', 'icon', 'website', 'versions')


class RuntimeSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Runtime
        fields = ('architecture', 'created_at', 'url')
