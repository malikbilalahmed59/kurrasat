from django.contrib import admin
from .models import RfpDocument

@admin.register(RfpDocument)
class RfpDocumentAdmin(admin.ModelAdmin):
    list_display = ('competition_name', 'created_at')
    search_fields = ('competition_name', 'competition_description')
    list_filter = ('created_at',)
