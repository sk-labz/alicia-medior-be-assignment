from django.contrib import admin
from .models import URLMapping


@admin.register(URLMapping)
class URLMappingAdmin(admin.ModelAdmin):
    list_display = ['short_code', 'original_url', 'created_at']
    list_filter = ['created_at']
    search_fields = ['short_code', 'original_url']
    readonly_fields = ['created_at']
