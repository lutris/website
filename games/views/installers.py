from __future__ import absolute_import

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from reversion.models import Version

from common.permissions import IsAdminOrReadOnly
from games import models, serializers


class InstallerListView(generics.ListAPIView):
    serializer_class = serializers.InstallerSerializer
    queryset = models.Installer.objects.all()


class InstallerDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerSerializer
    queryset = models.Installer.objects.all()


class InstallerRevisionListView(generics.ListAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerRevisionSerializer

    def get_queryset(self):
        installer_id = self.request.parser_context['kwargs']['pk']
        return [
            models.InstallerRevision(version.id)
            for version
            in Version.objects.filter(
                content_type__model='installer', object_id=installer_id
            )
        ]


class InstallerRevisionDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerRevisionSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_object(self):
        revision_id = self.request.parser_context['kwargs']['pk']
        return models.InstallerRevision(revision_id)
