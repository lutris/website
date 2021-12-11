"""Installer related API views"""
# pylint: disable=too-many-ancestors,too-few-public-methods,raise-missing-from
from __future__ import absolute_import

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.http import Http404
from django.db.models import Count
from rest_framework import generics, mixins, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from reversion.models import Revision

from common.permissions import IsAdminOrReadOnly
from games import models, serializers
from games.webhooks import notify_issue_reply

LOGGER = logging.getLogger(__name__)


class InstallerListView(generics.ListAPIView):
    """Return a list of all installers"""
    serializer_class = serializers.InstallerSerializer

    def get_queryset(self):
        installer_status = self.request.GET.get('status')
        if installer_status == 'published':
            return models.Installer.objects.published()
        if installer_status == 'unpublished':
            return models.Installer.objects.unpublished()
        if installer_status == 'new':
            return models.Installer.objects.new()
        if installer_status == 'abandoned':
            return models.Installer.objects.abandoned()
        return models.Installer.objects.all()


class InstallerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Returns the details for a given installer accessed by its id"""
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerSerializer
    queryset = models.Installer.objects.all()

    def patch(self, request, *args, **kwargs):
        if request.data.get('published'):
            LOGGER.info("Installer is published by %s", self.request.user)
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


class GameRevisionListView(generics.RetrieveAPIView):
    """Returns the list of revisions """
    permission_classes = [IsAdminUser]
    serializer_class = serializers.GameRevisionSerializer
    queryset = models.Game.objects.filter(change_for__isnull=True)
    lookup_field = 'slug'


class InstallerRevisionListView(generics.ListAPIView, mixins.DestroyModelMixin):
    """Return a list of revisions for a given installer"""
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerRevisionSerializer

    def get_queryset(self):
        installer = models.Installer.objects.get(pk=self.request.parser_context['kwargs']['pk'])
        return installer.revisions

    def delete(self, _request, *_args, **_kwargs):  # pylint: disable=no-self-use
        """Prevent deletion
        XXX Why is this needed?
        """
        return Response(status=status.HTTP_204_NO_CONTENT)


class InstallerRevisionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve a detailed view of an installer revision"""
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
        action = request.data.pop('action', None)
        try:
            instance = self.get_object()
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if action == 'accept':
            instance.accept(self.request.user, request.data)
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def get_object(self):
        try:
            revision = Revision.objects.get(pk=self.request.parser_context['kwargs']['pk'])
        except Revision.DoesNotExist:
            LOGGER.warning("No Revision with ID %s", self.request.parser_context['kwargs']['pk'])
            raise Http404
        try:
            version = revision.version_set.all()[0]
        except IndexError:
            LOGGER.warning("Revision ID %s has no versions",
                           self.request.parser_context['kwargs']['pk'])
            raise Http404
        return models.InstallerRevision(version)


class InstallerIssueList(generics.ListAPIView, generics.CreateAPIView):
    """Returns all issues and their replies for a game"""
    serializer_class = serializers.InstallerIssueListSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        slug = self.request.parser_context['kwargs']['slug']
        try:
            game = models.Game.objects.get(slug=slug)
        except models.Game.DoesNotExist:
            return models.Game.objects.none()
        return game.installers.annotate(
            issue_cnt=Count("issues")
        ).filter(issue_cnt__gt=0, published=True)


class InstallerIssueCreateView(generics.CreateAPIView):
    """Create a new issue"""
    serializer_class = serializers.InstallerIssueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the Installer instance based off URL parameters"""
        game_slug = self.request.parser_context['kwargs']['game_slug']
        installer_slug = self.request.parser_context['kwargs']['installer_slug']
        return models.Installer.objects.filter(game__slug=game_slug).get(slug=installer_slug)

    def create(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """Create a new issue"""
        issue_payload = dict(request.data)

        # Complete the information with the current user
        issue_payload['submitted_by'] = request.user.id
        issue_payload['submitted_on'] = timezone.now()
        issue_payload['installer'] = self.get_queryset().id

        serializer = self.get_serializer(data=issue_payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class InstallerIssueView(generics.CreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    """Edit or post a reply to an issue"""
    serializer_class = serializers.InstallerIssueSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return the installer issue from its ID"""
        issue_id = self.request.parser_context['kwargs']['pk']
        return models.InstallerIssue.objects.get(pk=issue_id)

    def create(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """Create the reply"""
        issue_id = self.request.parser_context["kwargs"]["pk"]
        try:
            issue = models.InstallerIssue.objects.get(pk=issue_id)
        except models.InstallerIssue.DoesNotExist:
            raise Http404

        reply_payload = dict(request.data)
        # Complete the information with the current user
        reply_payload["submitted_by"] = request.user.id
        reply_payload["submitted_on"] = timezone.now()
        reply_payload["issue"] = issue_id

        serializer = serializers.InstallerIssueReplySerializer(data=reply_payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        notify_issue_reply(issue, request.user, request.data['description'])

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class InstallerIssueReplyView(generics.RetrieveUpdateDestroyAPIView):
    """View for interacting with individual replies"""
    serializer_class = serializers.InstallerIssueReplySerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return the installer issue reply from its ID"""
        issue_id = self.request.parser_context['kwargs']['pk']
        return models.InstallerIssueReply.objects.get(pk=issue_id)


class SmallResultsSetPagination(PageNumberPagination):
    """Pagination used for heavier serializers that don't need a lot of data returned at once."""
    page_size = 25
    page_query_param = 'page'
    max_page_size = 100


class RevisionListView(generics.ListAPIView):
    """View to list all installer revisions"""
    serializer_class = serializers.RevisionSerializer
    permission_classes = [IsAdminUser]
    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        revision_type = self.request.GET.get('type')
        order_by = "date_created" if self.request.GET.get('order') == "oldest" else "-date_created"
        query = Revision.objects.all()
        if revision_type in ('submission', 'draft'):
            query = query.filter(comment__startswith=f"[{revision_type}]")
        return query.order_by(order_by)
