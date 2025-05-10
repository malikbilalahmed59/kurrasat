from django.contrib import admin
from .models import RfpDocument, ImprovedRfpDocument


@admin.register(RfpDocument)
class RfpDocumentAdmin(admin.ModelAdmin):
    list_display = ('competition_name', 'created_at')
    search_fields = ('competition_name', 'competition_description')
    list_filter = ('created_at',)


@admin.register(ImprovedRfpDocument)
class ImprovedRfpDocumentAdmin(admin.ModelAdmin):
    list_display = ('competition_name', 'created_at')
    search_fields = ('competition_name', 'competition_description')
    list_filter = ('created_at',)
    readonly_fields = ('original_document', 'improved_document', 'created_at')