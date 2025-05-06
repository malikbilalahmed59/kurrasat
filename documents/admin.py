from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _  # Import translation function
from .models import Document, DocumentAnalysis


class DocumentAnalysisInline(admin.TabularInline):
    model = DocumentAnalysis
    extra = 0
    readonly_fields = ('analysis_date',)
    fields = ('analysis_text', 'suggestions', 'analysis_date')
    can_delete = False

    # Translate the verbose names
    verbose_name = _("Document Analysis")
    verbose_name_plural = _("Document Analyses")

    def has_add_permission(self, request, obj=None):
        # Only allow adding analysis through the document detail view
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'created_at', 'updated_at', 'document_actions')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'content', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    inlines = [DocumentAnalysisInline]

    # Translate the model's verbose name
    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'status')
        }),
        (_('Content'), {  # Wrap fieldset titles in gettext_lazy
            'fields': ('description', 'content', 'file'),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def document_actions(self, obj):
        """Custom column for action buttons"""
        # Use gettext_lazy for translating the button text
        view_text = _("View")

        return format_html(
            '<a class="button" href="{}" style="margin-right: 5px; background-color: #79aec8; '
            'color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">{}</a>',
            f'/admin/documents/document/{obj.id}/change/',
            view_text
        )

    # Translate the column header
    document_actions.short_description = _('Actions')


@admin.register(DocumentAnalysis)
class DocumentAnalysisAdmin(admin.ModelAdmin):
    list_display = ('document', 'analysis_date')
    list_filter = ('analysis_date',)
    search_fields = ('document__title', 'analysis_text', 'suggestions')
    readonly_fields = ('analysis_date',)

    # Translate the model's verbose name
    class Meta:
        verbose_name = _("Document Analysis")
        verbose_name_plural = _("Document Analyses")

    fieldsets = (
        (None, {
            'fields': ('document',)
        }),
        (_('Analysis'), {  # Wrap fieldset titles in gettext_lazy
            'fields': ('analysis_text', 'suggestions', 'analysis_date'),
        }),
    )

    def has_add_permission(self, request):
        # Analyses should be created through the API or document views
        return True