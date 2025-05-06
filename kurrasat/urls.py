from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import gettext_lazy as _
from accounts.admin import switch_language  # Import the language switch view

# Create a path for the language switching view
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # For language switching
    path('admin/language-switch/', switch_language, name='language_switch'),  # Custom language switch endpoint
]

# Wrap URL patterns with i18n_patterns for internationalization
urlpatterns += i18n_patterns(
    path(_('admin/'), admin.site.urls),  # Make the admin URL translatable
    path('', include(('core.urls', 'core'), namespace='core')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('documents/', include(('documents.urls', 'documents'), namespace='documents')),
    prefix_default_language=False,  # Don't prefix URLs for default language
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)