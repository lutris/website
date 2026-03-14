"""API views for regressions"""

from rest_framework import generics, permissions
from rest_framework.response import Response

from games import models, serializers


class RegressionListView(generics.ListCreateAPIView):
    """List regressions or submit a new one"""

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.RegressionWriteSerializer
        return serializers.RegressionSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = models.Regression.objects.all()
        regression_status = self.request.query_params.get("status")
        if regression_status:
            queryset = queryset.filter(status=regression_status)
        game_slug = self.request.query_params.get("game_slug")
        if game_slug:
            queryset = queryset.filter(games__slug=game_slug)
        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save()


class RegressionDetailView(generics.RetrieveUpdateAPIView):
    """Get or update a regression"""

    queryset = models.Regression.objects.all()

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return serializers.RegressionSerializer
        return serializers.RegressionSerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT"):
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def partial_update(self, request, *args, **kwargs):
        regression = self.get_object()
        allowed_fields = {
            "title",
            "description",
            "bug_url",
            "bug_status",
            "last_known_working_version",
            "status",
        }
        for field, value in request.data.items():
            if field in allowed_fields:
                setattr(regression, field, value)
        if "status" in request.data:
            if request.data["status"] == "resolved" and not regression.resolved_at:
                from django.utils import timezone

                regression.resolved_at = timezone.now()
            regression.reviewed_by = request.user
        regression.save()
        serializer = self.get_serializer(regression)
        return Response(serializer.data)
