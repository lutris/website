# pylint: disable=no-member
"""Hardware API views"""
from rest_framework import views
from rest_framework.response import Response
from hardware import models


class HardwareInfoView(views.APIView):
    """Return hardware features from a PCI ID"""
    def get(self, request):
        """Query PCI ID against database and return features"""
        pci_ids = request.GET.get("pci_ids", "").lower()
        if not pci_ids:
            return Response({"error": "No pci_ids given"})
        response = {}
        for pci_id in pci_ids.split(","):
            try:
                response[pci_id] = models.get_hardware_features(pci_id)
            except ValueError as ex:
                return Response({"error": str(ex)})
        return Response(response)
