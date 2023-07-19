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
            device_pci_id, subdevice_pci_id = pci_id.split()
            vendor_id, device_id = device_pci_id.split(":")
            try:
                vendor = models.Vendor.objects.get(vendor_id=vendor_id)
            except models.Vendor.DoesNotExist:
                return Response({"error": f"Invalid vendor {vendor_id}"})
            try:
                device = models.Device.objects.get(vendor=vendor, device_id=device_id)
            except models.Device.DoesNotExist:
                return Response({"error": f"Unkown device {vendor_id}:{device_id}"})
            subvendor_id, subsystem_id = subdevice_pci_id.split(":")
            try:
                subvendor = models.Vendor.objects.get(vendor_id=subvendor_id)
                subvendor_name = subvendor.name
            except models.Vendor.DoesNotExist:
                subvendor_name = "Unkown"
            response[pci_id] = {
                "vendor": vendor.name,
                "device": device.name,
                "subvendor": subvendor_name,
            }
        return Response(response)
