from __future__ import absolute_import

from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework import status
from reversion.models import Version

from common.permissions import IsAdminOrReadOnly
from rest_framework.permissions import IsAdminUser
from games import models, serializers


class InstallerListView(generics.ListAPIView):
    """Lists all the installers"""
    serializer_class = serializers.InstallerSerializer
    queryset = models.Installer.objects.all()


class InstallerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Returns the details for a given installer accessed by its id"""
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerSerializer
    queryset = models.Installer.objects.all()


class GameInstallerListView(generics.ListAPIView):
    """Return the list of installers available for a game if a game slug is provided,
    or a particular installer if an installer slug is passed.
    """
    serializer_class = serializers.InstallerSerializer

    def get_queryset(self):
        slug = self.request.parser_context['kwargs']['slug']
        return models.Installer.objects.fuzzy_filter(slug)


class GameRevisionListView(generics.RetrieveAPIView):
    """Returns the list of revisions """
    permission_classes = [IsAdminUser]
    serializer_class = serializers.GameRevisionSerializer
    queryset = models.Game.objects.all()
    lookup_field = 'slug'


class InstallerRevisionListView(generics.ListAPIView, mixins.DestroyModelMixin):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerRevisionSerializer

    def get_queryset(self):
        installer = models.Installer.objects.get(pk=self.request.parser_context['kwargs']['pk'])
        return installer.revisions

    def delete(self, request, *args, **kwargs):
        return Response(status=status.HTTP_204_NO_CONTENT)


class InstallerRevisionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerRevisionSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.data.get('action') == 'accept':
            instance.accept()
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def get_object(self):
        try:
            version = Version.objects.get(pk=self.request.parser_context['kwargs']['pk'])
        except Version.DoesNotExist:
            raise Http404
        return models.InstallerRevision(version)
