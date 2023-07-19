"""Admin configuration for hardware"""
from django.contrib import admin
from hardware import models


class VendorAdmin(admin.ModelAdmin):
    """Admin config for Vendor"""
    list_display = ("vendor_id", "name")
    search_fields = ("vendor_id", "name")

class DeviceAdmin(admin.ModelAdmin):
    """Admin config for Device"""
    list_display = ("device_id", "vendor", "name")
    search_fields = ("device_id", "name")
    list_filter = ("vendor", )


class SubsystemAdmin(admin.ModelAdmin):
    """Admin config for Subsystem"""
    list_display = ("subvendor_id", "subdevice_id", "name")
    search_fields = ("subvendor_id", "subdevice_id", "name")


class GenerationAdmin(admin.ModelAdmin):
    """Admin config for Generation"""
    list_display = ("name", "vendor", "year")
    raw_id_fields = ('vendor', )
    autocomplete_lookup_fields = {
        'fk': ['vendor'],
    }


class FeatureAdmin(admin.ModelAdmin):
    """Admin config for Feature"""
    list_display = ("name", "version", "feature_level")


admin.site.register(models.Vendor, VendorAdmin)
admin.site.register(models.Device, DeviceAdmin)
admin.site.register(models.Subsystem, SubsystemAdmin)
admin.site.register(models.Generation, GenerationAdmin)
admin.site.register(models.Feature, FeatureAdmin)
