# pylint: disable=no-member
"""Hardware reference from PCI Ids"""
from django.db import models


class Vendor(models.Model):
    """Store info about hardware vendor"""
    vendor_id = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=128)

    def __str__(self) -> str:
        return f"{self.name} ({self.vendor_id})"

    class Meta:
        ordering = ("name", )

class Feature(models.Model):
    """Store info about hardware features"""
    name = models.CharField(max_length=64)
    version = models.CharField(max_length=8, blank=True)
    feature_level = models.CharField(max_length=8, blank=True)

    def __str__(self) -> str:
        feature_level = f" ({self.feature_level})" if self.feature_level else ""
        return f"{self.name} {self.version}{feature_level}"


class Generation(models.Model):
    """Store info about a hardware generation"""
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=64)
    year = models.SmallIntegerField()
    introduced_with = models.CharField(max_length=128)
    features = models.ManyToManyField(Feature)

    def __str__(self) -> str:
        return f"{self.name}"


class Device(models.Model):
    """Store info about devices"""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=4)
    name = models.CharField(max_length=256, blank=True)
    comment = models.CharField(max_length=256, blank=True)
    generation = models.ForeignKey(Generation, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        name = self.name if self.name else "[UNKOWN]"
        return f"{name} ({self.device_id})"


class Subsystem(models.Model):
    """Store info about a subsystem"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    subvendor_id = models.CharField(max_length=4)
    subdevice_id = models.CharField(max_length=32)
    name = models.CharField(max_length=256, blank=True)

    def __str__(self) -> str:
        name = self.name if self.name else "[UNKOWN]"
        return f"{name} ({self.subvendor_id}:{self.subdevice_id})"



def get_hardware_features(pci_id):
    """Return hardware capabilities from a PCI ID"""
    try:
        device_pci_id, subdevice_pci_id = pci_id.split()
    except ValueError as ex:
        raise ValueError("Incomplete PCI ID. Use following format: xxxx:xxxx xxxx:xxxx") from ex
    vendor_id, device_id = device_pci_id.split(":")
    try:
        vendor = Vendor.objects.get(vendor_id=vendor_id)
    except Vendor.DoesNotExist as ex:
        raise ValueError(f"Invalid vendor {vendor_id}") from ex
    try:
        device = Device.objects.get(vendor=vendor, device_id=device_id)
    except Device.DoesNotExist as ex:
        raise ValueError(f"Unkown device {vendor_id}:{device_id}") from ex
    subvendor_id, _subsystem_id = subdevice_pci_id.split(":")
    try:
        subvendor = Vendor.objects.get(vendor_id=subvendor_id)
        subvendor_name = subvendor.name
    except Vendor.DoesNotExist:
        subvendor_name = "Unknown"
    features = []
    generation_name = ""
    if device.generation:
        features = [
            str(feature)
            for feature in device.generation.features.all()
        ]
        generation_name = device.generation.name
    return {
        "vendor": vendor.name,
        "device": device.name,
        "subvendor": subvendor_name,
        "generation": generation_name,
        "features": features,
    }
