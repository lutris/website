# pylint: disable=no-member
import logging

from django.conf import settings
from hardware import models

LOGGER = logging.getLogger(__name__)


def load_from_pci_ids():
    """Load IDs from https://pci-ids.ucw.cz/v2.2/pci.ids"""
    pci_ids_path = settings.MEDIA_ROOT + "/pci.ids"
    LOGGER.info("Reading PCI IDs from %s", pci_ids_path)
    data_started = False
    comment_for_next_dev = ""
    device = None
    with open(pci_ids_path, encoding="utf-8") as pci_ids_file:
        for line in pci_ids_file.readlines():
            if line and line[0].isdigit():
                data_started = True
            if not data_started:
                continue
            if line.startswith("#"):
                comment_for_next_dev = line[2:]
                continue
            if line[0].isdigit():
                vendor_id, vendor_name = line.strip().split(maxsplit=1)
                print(vendor_name, vendor_id)
                vendor, created = models.Vendor.objects.get_or_create(
                    vendor_id=vendor_id,
                    name=vendor_name
                )
                if created:
                    LOGGER.info("Created vendor %s", vendor)
            if line.startswith("\t\t"):
                subvendor_id, subdevice_id, name = line.strip().split(maxsplit=2)
                try:
                    subsystem = models.Subsystem.objects.get(
                        device=device,
                        subvendor_id=subvendor_id,
                        subdevice_id=subdevice_id
                    )
                    if subsystem.name != name:
                        subsystem.name = name
                        subsystem.save()
                except models.Subsystem.DoesNotExist:
                    subsystem = models.Subsystem.objects.create(
                        device=device,
                        subvendor_id=subvendor_id,
                        subdevice_id=subdevice_id,
                        name=name
                    )
                    LOGGER.info("Created subsystem %s", subsystem)
            elif line.startswith("\t"):
                device_id, name = line.strip().split(maxsplit=1)
                try:
                    device = models.Device.objects.get(
                        vendor=vendor,
                        device_id = device_id,
                    )
                    device_changed = False
                    if device.name != name:
                        device.name = name
                        device_changed = True
                    if comment_for_next_dev:
                        device.comment = comment_for_next_dev
                        comment_for_next_dev = ""
                        device_changed = True
                    if device_changed:
                        device.save()
                except models.Device.DoesNotExist:
                    device = models.Device.objects.create(
                        vendor=vendor,
                        device_id=device_id,
                        name=name,
                        comment=comment_for_next_dev,
                    )
                    if comment_for_next_dev:
                        comment_for_next_dev = ""
                    LOGGER.info("Created device %s", device)
            elif line.startswith("ffff"):
                return
