"""Installer related API views"""
# pylint: disable=too-many-ancestors,too-few-public-methods
from __future__ import absolute_import

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from common.permissions import IsAdminOrReadOnly
from games import models, serializers

LOGGER = logging.getLogger(__name__)


class InstallerListView(generics.ListAPIView):
    """Return a list of all installers
    Supported query parameters:
        status: installer status (published, unpublished)
        revision: installer revision (draft, final)
        created_from: installer creation period start
        created_to: installer creation period end
        updated_from: installer modification period start
        updated_to: installer modification period end
        order: order results by creation date (oldest, newest), default=newest
    """
    serializer_class = serializers.InstallerSerializer

    def get_queryset(self):        
        params = self.request.GET.dict()
        filter = {}
        if 'status' in params:
            if params['status'] == 'published':
                filter['published'] = True
            elif params['status'] == 'unpublished':
                filter['published'] = False
        if 'revision' in params:
            if params['revision'] == 'draft':
                filter['draft'] = True
            elif params['revision'] == 'final':
                filter['draft'] = False
        for param in {'created_from', 'created_to', 'updated_from', 'updated_to'}:
            if param in params:
                filter[param] = params[param]        
        order = self.request.GET.get('order')
        order_by = "created_at" if order == "oldest" else "-created_at"
        return models.Installer.objects.get_filtered(filter).order_by(order_by)

class InstallerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Returns the details for a given installer accessed by its id"""
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerSerializer
    queryset = models.Installer.objects.all()

    def patch(self, request, *args, **kwargs):
        LOGGER.error("Deprecated view called")
        if request.data.get('published'):
            LOGGER.debug("Installer is published by %s", self.request.user)
            request.data['published_by'] = self.request.user.id
        return super().patch(request, *args, **kwargs)


class GameInstallerListView(generics.ListAPIView):
    """Return the list of installers available for a game if a game slug is provided,
    or a particular installer if an installer slug is passed.
    """
    serializer_class = serializers.InstallerSerializer

    def get_queryset(self):
        slug = self.request.parser_context['kwargs']['slug']
        return models.Installer.objects.fuzzy_filter(slug)


class SmallResultsSetPagination(PageNumberPagination):
    """Pagination used for heavier serializers that don't need a lot of data returned at once."""
    page_size = 25
    page_query_param = 'page'
    max_page_size = 100

class InstallerDraftListView(generics.ListAPIView):
    """Return a list of revisions for a given installer"""
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerDraftSerializer

    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        revision_type = self.request.GET.get('type')
        order_by = "created_at" if self.request.GET.get('order') == "oldest" else "-created_at"
        query = models.InstallerDraft.objects.all()
        if revision_type == 'submission':
            query = query.filter(draft=False)
        elif revision_type == 'draft':
            query = query.filter(draft=True)
        return query.order_by(order_by)

class InstallerDraftDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve a detailed view of an installer draft"""
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerDraftSerializer


    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        action = request.data.pop('action', None)
        try:
            instance = self.get_object()
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if action == 'accept':
            instance.accept(self.request.user, request.data)
            return Response(status=status.HTTP_202_ACCEPTED)
        if action == 'reject':
            instance.reject(request.data)
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def get_object(self):
        try:
            return models.InstallerDraft.objects.get(pk=self.request.parser_context['kwargs']['pk'])
        except models.InstallerDraft.DoesNotExist:
            raise Http404

class InstallerHistoryListView(generics.ListAPIView):
    """Return history of installers
    Supported query parameters:        
        created_from: installer history period start
        created_to: installer history period end        
        order: order results by creation date (oldest, newest), default=newest
    """
    serializer_class = serializers.InstallerHistorySerializer

    def get_queryset(self):        
        params = self.request.GET.dict()
        filter = {}        
        for param in {'created_from', 'created_to'}:
            if param in params:
                filter[param] = params[param]        
        order = self.request.GET.get('order')
        order_by = "created_at" if order == "oldest" else "-created_at"
        return models.InstallerHistory.objects.get_filtered(filter).order_by(order_by)

class InstallerHistoryView(generics.ListAPIView):
    """Retrieve a history for a given installer accessed by its id"""
    serializer_class = serializers.InstallerHistorySerializer

    def get_queryset(self):
        return models.InstallerHistory.objects.filter(
            installer_id=self.request.parser_context['kwargs']['installer_id']
        ).order_by('created_at')
