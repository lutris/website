# pylint: disable=no-member
import logging
import json

from django.conf import settings
from hardware import models

LOGGER = logging.getLogger(__name__)


# Warning: The load order is important, for example, "HD Graphics 630" matches
# both "HD Graphics 630" and "UHD Graphics 630" so "UHD Graphics 630" has
# to come *after* to override this match.
GPU_GENERATION_FEATURE_MAP = {
    "AMD": {
        r"HD 6\d\d0": "Northern Islands",
        r"Mullins": "Sea Islands",
        r"Vega": "Vega",
        r"RX [4-5][7-9]0": "Polaris",
        r"RX 5\d00": "Navi",
        r"RX 6\d00": "Navi 2X",
        r"RX 7\d00": "Navi 3X",
    },
    "Nvidia": {
        r"GeForce FX": "Geforce FX",
        r"GeForce 6\d00": "Geforce 6",
        r"GeForce 7\d00": "GeForce 7",
        r"GeForce 8\d00": "GeForce 8",
        r"GeForce 9\d00": "GeForce 9",
        r"GeForce GTS 1\d0": "Geforce 100",
        r"GeForce GTS 2\d0": "Geforce 200",
        r"GeForce GTX 2\d0": "Geforce 200",
        r"GeForce GT 3\d0": "Geforce 300",
        r"GeForce GTS 3\d0": "Geforce 300",
        r"GeForce GTS 4\d0": "Fermi",
        r"GeForce GTX 4\d0": "Fermi",
        r"GeForce GTX 5\d0": "Fermi 2.0",
        r"GeForce GTX 6\d0": "Kepler",
        r"GeForce GT 7\d0": "Kepler",
        r"GeForce GTX 7\d0": "Maxwell 1",
        r"GeForce GTX 9\d0": "Maxwell 2",
        r"GTX 10\d0": "Pascal",
        r"RTX 20\d0": "Turing",
        r"RTX 30\d0": "Ampere",
        r"RTX 40\d0": "Ada Lovelace"
    },
    "Intel": {
        r"N3xxx Integrated Graphics Controller": "HD Graphics 400",
        r"HD Graphics .?630": "HD Graphics 630",
        r"UHD Graphics .?620": "HD Graphics 630",
        r"UHD Graphics .?6[2-3]0": "UHD Graphics 630",
        r"Iris Plus Graphics": "Iris Plus Graphics",
        r"Iris Xe Graphics": "Iris Xe Graphics",
        r"Arc ": "Arc"
    }
}


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


def load_features():
    """Load GPU features by geneation from JSON"""
    gpu_json_path = settings.BASE_DIR + "/public/data/gpu-features-by-series.json"
    vendor_ids = {
        "ATI": "1002",
        "AMD": "1002",
        "Nvidia": "10de",
        "Intel": "8086"
    }
    vendors = {
        vendor_name: models.Vendor.objects.get(vendor_id=vendor_id)
        for vendor_name, vendor_id in vendor_ids.items()
    }
    LOGGER.info("Reading features from %s", gpu_json_path)
    with open(gpu_json_path, encoding="utf-8") as gpu_json_file:
        gpu_features_generations =json.load(gpu_json_file)
    for gpu_features in gpu_features_generations:
        vendor = vendors[gpu_features["Vendor"]]
        try:
            generation = models.Generation.objects.get(
                vendor=vendor,
                name=gpu_features["Chip series"]
            )
            generation.year = gpu_features["Year"]
            if gpu_features["Introduced with"]:
                generation.introduced_with = gpu_features["Introduced with"]
            generation.save()
        except models.Generation.DoesNotExist:
            generation = models.Generation.objects.create(
                vendor=vendor,
                name=gpu_features["Chip series"],
                year=gpu_features["Year"],
                introduced_with=gpu_features["Introduced with"]
            )
        for api in ("OpenGL", "Vulkan", "Direct3D"):
            if not gpu_features[api]:
                continue
            versions = str(gpu_features[api])
            feature_level = ""
            for version in versions.strip(")").split(")"):
                if " (FL" in version:
                    version, feature_level = version.split(" (FL")
                if not version:
                    continue
                try:
                    feature = models.Feature.objects.get(
                        name=api,
                        version=version.strip(),
                        feature_level=feature_level or "",
                    )
                except models.Feature.DoesNotExist:
                    feature = models.Feature.objects.create(
                        name=api,
                        version=version.strip(),
                        feature_level=feature_level or "",
                    )
                generation.features.add(feature)


def load_generations_to_devices():
    """Apply generations to devices"""
    vendor_ids = {
        "AMD": "1002",
        "Nvidia": "10de",
        "Intel": "8086"
    }
    vendors = {
        vendor_name: models.Vendor.objects.get(vendor_id=vendor_id)
        for vendor_name, vendor_id in vendor_ids.items()
    }
    generations = {
        gen.name: gen
        for gen in models.Generation.objects.all()
    }

    for vendor, patterns in GPU_GENERATION_FEATURE_MAP.items():
        for pattern, generation_name in patterns.items():
            devices = models.Device.objects.filter(
                vendor=vendors[vendor],
                name__regex=pattern
            )
            for device in devices:
                if device.generation != generations[generation_name]:
                    device.generation = generations[generation_name]
                    device.save()
