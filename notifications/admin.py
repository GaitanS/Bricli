from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Notification, NotificationPreference, PushSubscription


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'recipient', 'notification_type', 'priority', 
        'is_read', 'created_at', 'action_buttons'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'created_at',
        'email_sent', 'push_sent'
    ]
    search_fields = ['title', 'message', 'recipient__username', 'recipient__email']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informații de bază', {
            'fields': ('recipient', 'sender', 'notification_type', 'priority')
        }),
        ('Conținut', {
            'fields': ('title', 'message', 'action_url')
        }),
        ('Obiect asociat', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'expires_at')
        }),
        ('Livrare', {
            'fields': ('email_sent', 'push_sent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_expired']
    
    def action_buttons(self, obj):
        """Display action buttons for each notification"""
        buttons = []
        
        if not obj.is_read:
            mark_read_url = reverse('admin:notifications_notification_change', args=[obj.pk])
            buttons.append(
                f'<a class="button" href="{mark_read_url}" '
                f'onclick="return confirm(\'Marchează ca citită?\')">Marchează citită</a>'
            )
        
        if obj.action_url:
            buttons.append(
                f'<a class="button" href="{obj.action_url}" target="_blank">Vezi acțiunea</a>'
            )
        
        return format_html(' '.join(buttons))
    action_buttons.short_description = 'Acțiuni'
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        updated = 0
        for notification in queryset.filter(is_read=False):
            notification.mark_as_read()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} notificări au fost marcate ca citite.'
        )
    mark_as_read.short_description = 'Marchează ca citite'
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(
            request,
            f'{updated} notificări au fost marcate ca necitite.'
        )
    mark_as_unread.short_description = 'Marchează ca necitite'
    
    def delete_expired(self, request, queryset):
        """Delete expired notifications"""
        now = timezone.now()
        expired_count = queryset.filter(
            expires_at__lt=now
        ).delete()[0]
        
        self.message_user(
            request,
            f'{expired_count} notificări expirate au fost șterse.'
        )
    delete_expired.short_description = 'Șterge notificările expirate'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recipient', 'sender'
        )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'digest_frequency', 'email_enabled', 'push_enabled',
        'quiet_hours', 'updated_at'
    ]
    list_filter = [
        'digest_frequency', 'email_new_orders', 'push_new_orders',
        'created_at', 'updated_at'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Utilizator', {
            'fields': ('user',)
        }),
        ('Preferințe Email', {
            'fields': (
                'email_new_orders', 'email_quotes', 'email_payments',
                'email_messages', 'email_reviews', 'email_system'
            )
        }),
        ('Preferințe Push', {
            'fields': (
                'push_new_orders', 'push_quotes', 'push_payments',
                'push_messages', 'push_reviews', 'push_system'
            )
        }),
        ('Setări generale', {
            'fields': ('digest_frequency', 'quiet_hours_start', 'quiet_hours_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def email_enabled(self, obj):
        """Check if any email notifications are enabled"""
        email_fields = [
            obj.email_new_orders, obj.email_quotes, obj.email_payments,
            obj.email_messages, obj.email_reviews, obj.email_system
        ]
        return any(email_fields)
    email_enabled.boolean = True
    email_enabled.short_description = 'Email activat'
    
    def push_enabled(self, obj):
        """Check if any push notifications are enabled"""
        push_fields = [
            obj.push_new_orders, obj.push_quotes, obj.push_payments,
            obj.push_messages, obj.push_reviews, obj.push_system
        ]
        return any(push_fields)
    push_enabled.boolean = True
    push_enabled.short_description = 'Push activat'
    
    def quiet_hours(self, obj):
        """Display quiet hours range"""
        if obj.quiet_hours_start and obj.quiet_hours_end:
            return f"{obj.quiet_hours_start.strftime('%H:%M')} - {obj.quiet_hours_end.strftime('%H:%M')}"
        return "Nu sunt setate"
    quiet_hours.short_description = 'Ore de liniște'


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'endpoint_short', 'is_active', 'created_at', 'last_used'
    ]
    list_filter = ['is_active', 'created_at', 'last_used']
    search_fields = ['user__username', 'user__email', 'endpoint']
    readonly_fields = ['created_at', 'last_used', 'endpoint', 'p256dh_key', 'auth_key']
    
    fieldsets = (
        ('Utilizator', {
            'fields': ('user', 'is_active')
        }),
        ('Detalii abonament', {
            'fields': ('endpoint', 'p256dh_key', 'auth_key', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_used'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions', 'test_push_notifications']
    
    def endpoint_short(self, obj):
        """Display shortened endpoint URL"""
        if obj.endpoint and len(obj.endpoint) > 50:
            return obj.endpoint[:50] + '...'
        return obj.endpoint or '-'
    endpoint_short.short_description = 'Endpoint'
    
    def activate_subscriptions(self, request, queryset):
        """Activate selected subscriptions"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} abonamente au fost activate cu succes.'
        )
    activate_subscriptions.short_description = 'Activează abonamentele'
    
    def deactivate_subscriptions(self, request, queryset):
        """Deactivate selected subscriptions"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} abonamente au fost dezactivate cu succes.'
        )
    deactivate_subscriptions.short_description = 'Dezactivează abonamentele'
    
    def test_push_notifications(self, request, queryset):
        """Send test push notifications to selected subscriptions"""
        from .services import PushNotificationService
        
        service = PushNotificationService()
        success_count = 0
        error_count = 0
        
        for subscription in queryset.filter(is_active=True):
            try:
                service.send_push_notification(
                    subscription.user,
                    title="Test notificare Bricli",
                    message="Aceasta este o notificare de test din panoul de administrare. Sistemul funcționează corect!",
                    notification_type="system",
                    priority="medium"
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request, 
                    f'Eroare la trimiterea notificării pentru {subscription.user}: {str(e)}',
                    level='ERROR'
                )
        
        if success_count > 0:
            self.message_user(
                request, 
                f'{success_count} notificări de test trimise cu succes.'
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f'{error_count} notificări nu au putut fi trimise din cauza erorilor.',
                level='WARNING'
            )
    test_push_notifications.short_description = 'Trimite notificări de test'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Custom admin site configuration
admin.site.site_header = 'Administrare Bricli'
admin.site.site_title = 'Bricli Admin'
admin.site.index_title = 'Panou de administrare'