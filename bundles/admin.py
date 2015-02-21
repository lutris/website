from django.contrib import admin
from .models import Bundle


class BundleAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    raw_id_fields = ('games', )
    autocomplete_lookup_fields = {
        'm2m': ['games']
    }


admin.site.register(Bundle, BundleAdmin)
