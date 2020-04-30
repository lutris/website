"""bundles views"""
# pylint: disable=too-many-ancestors
from django.views.generic import DetailView, ListView

from rest_framework import generics
from rest_framework.response import Response

from . import models, serializers


class BundleList(ListView):
    """List all bundles in a paginated view"""
    model = models.Bundle
    context_object_name = 'bundles'
    paginate_by = 25


class BundleDetail(DetailView):
    """Show a bundle"""
    model = models.Bundle
    context_object_name = 'bundle'


class BundleView(generics.RetrieveAPIView):
    """Get a bundle from the API"""
    serializer_class = serializers.BundleSerializer

    def get(self, request, slug):  # pylint: disable=arguments-differ
        try:
            bundle = models.Bundle.objects.get(slug=slug)
        except models.Bundle.DoesNotExist:
            return Response(status=404)
        serializer = serializers.BundleSerializer(bundle)
        return Response(serializer.data)
