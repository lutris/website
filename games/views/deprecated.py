"""Installer related API views"""
# pylint: disable=too-many-ancestors,too-few-public-methods
from __future__ import absolute_import

import logging

from django.utils import timezone
from django.http import Http404
from django.db.models import Count
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from games import models, serializers
from games.webhooks import notify_issue_reply

LOGGER = logging.getLogger(__name__)


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
