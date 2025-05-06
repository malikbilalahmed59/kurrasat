from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponseRedirect

from .models import Profile, Payment

from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils.translation import activate
import re


def switch_language(request):
    """
    View to handle language switching in the admin interface
    with improved URL handling to fix language toggle issues.
    """
    # Get current language
    user_language = request.session.get(settings.LANGUAGE_SESSION_KEY, settings.LANGUAGE_CODE)

    # Toggle language
    next_language = 'ar' if user_language == 'en' else 'en'

    # Store in session
    request.session[settings.LANGUAGE_SESSION_KEY] = next_language

    # Activate the language for the current request
    activate(next_language)

    # Get referring URL
    referer = request.META.get('HTTP_REFERER', '/admin/')

    # Extract path from the referring URL
    path_match = re.search(r'https?://[^/]+(/.*)', referer)
    if path_match:
        path = path_match.group(1)
    else:
        path = '/admin/'  # Default to admin if no path found

    # Remove any language prefix from the path
    if path.startswith('/en/') or path.startswith('/ar/'):
        path = path[3:]  # Remove language code and slash

    # Ensure path starts with a slash
    if not path.startswith('/'):
        path = '/' + path

    # Build proper URL with or without language prefix
    if next_language == settings.LANGUAGE_CODE:
        # Default language doesn't need prefix
        url = path
    else:
        # Add language prefix for non-default language
        url = '/' + next_language + path

    # Redirect to the new URL
    return HttpResponseRedirect(url)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_date',)
    fields = ('subscription_type', 'amount', 'payment_date', 'status', 'transaction_id')
    ordering = ('-payment_date',)
    max_num = 5
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_type', 'subscription_status', 'created_at', 'profile_actions')
    list_filter = ('subscription_type', 'created_at', 'subscription_end_date')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('user', 'profile_image', 'subscription_type')
        }),
        ('Subscription Details', {
            'fields': ('subscription_end_date',),
            'classes': ('collapse',),
            'description': 'Subscription information and expiration date'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def subscription_status(self, obj):
        """Display subscription status with color coding"""
        if not obj.subscription_end_date:
            return format_html('<span style="color: #666;">Not Set</span>')

        if obj.subscription_end_date < timezone.now().date():
            return format_html('<span style="color: #e74c3c; font-weight: bold;">Expired</span>')
        elif (obj.subscription_end_date - timezone.now().date()).days <= 7:
            return format_html('<span style="color: #f39c12; font-weight: bold;">Expiring Soon</span>')
        else:
            return format_html('<span style="color: #27ae60; font-weight: bold;">Active</span>')

    subscription_status.short_description = 'Status'

    def profile_actions(self, obj):
        """Custom column for action buttons"""
        view_url = reverse('admin:auth_user_change', args=[obj.user.id])

        return format_html(
            '<div class="button-container">'
            '<a class="button" href="{}" style="margin-right: 5px; background-color: #79aec8; '
            'color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">User Details</a>'
            '<a class="button" href="{}" style="background-color: #2ecc71; color: white; '
            'padding: 4px 8px; border-radius: 4px; text-decoration: none;">Payments</a>'
            '</div>',
            view_url,
            reverse('admin:accounts_payment_changelist') + f'?user__id__exact={obj.user.id}'
        )

    profile_actions.short_description = 'Actions'

    def get_queryset(self, request):
        # Store the request object to access it in other methods
        self.request = request
        return super().get_queryset(request)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_type', 'amount', 'formatted_payment_date', 'status', 'payment_actions')
    list_filter = ('status', 'subscription_type', 'payment_date')
    search_fields = ('user__username', 'user__email', 'transaction_id')
    readonly_fields = ('payment_date',)
    date_hierarchy = 'payment_date'

    fieldsets = (
        (None, {
            'fields': ('user', 'subscription_type', 'amount')
        }),
        ('Payment Details', {
            'fields': ('status', 'transaction_id', 'payment_date'),
        }),
    )

    def formatted_payment_date(self, obj):
        """Format the payment date nicely"""
        return obj.payment_date.strftime("%b %d, %Y %H:%M")

    formatted_payment_date.short_description = 'Payment Date'

    def payment_actions(self, obj):
        """Custom column for payment action buttons"""
        if obj.status == 'pending':
            actions = f'''
                <a class="button" href="#" onclick="approvePayment({obj.id})" 
                   style="margin-right: 5px; background-color: #2ecc71; color: white; 
                   padding: 4px 8px; border-radius: 4px; text-decoration: none;">Approve</a>
                <a class="button" href="#" onclick="rejectPayment({obj.id})"
                   style="background-color: #e74c3c; color: white; 
                   padding: 4px 8px; border-radius: 4px; text-decoration: none;">Reject</a>
            '''
        else:
            actions = f'''
                <a class="button" href="{reverse('admin:accounts_payment_change', args=[obj.id])}"
                   style="background-color: #3498db; color: white; 
                   padding: 4px 8px; border-radius: 4px; text-decoration: none;">View Details</a>
            '''

        return format_html(
            '<div class="payment-actions">{}</div>'
            '<script>'
            'function approvePayment(id) {{ '
            '  if(confirm("Are you sure you want to approve this payment?")) {{ '
            '    window.location.href = "/admin/approve-payment/" + id + "/"; '
            '  }} '
            '}} '
            'function rejectPayment(id) {{ '
            '  if(confirm("Are you sure you want to reject this payment?")) {{ '
            '    window.location.href = "/admin/reject-payment/" + id + "/"; '
            '  }} '
            '}} '
            '</script>',
            actions
        )

    payment_actions.short_description = 'Actions'

    def get_queryset(self, request):
        # Store the request object
        self.request = request
        return super().get_queryset(request)


# Update the admin site header and title
admin.site.site_header = "Kurrasat Admin"
admin.site.site_title = "Kurrasat Admin Portal"
admin.site.index_title = "Welcome to Kurrasat Management Portal"