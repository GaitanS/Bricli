"""
Admin interface for moderation system
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    RateLimit, IPBlock, Report, ModerationAction, ImageModerationQueue
)


@admin.register(RateLimit)
class RateLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'limit_type', 'count', 'get_max_limit', 'window_start', 'is_within_window')
    list_filter = ('limit_type', 'window_start')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('window_start',)
    
    def get_max_limit(self, obj):
        return obj.get_max_limit()
    get_max_limit.short_description = 'Limită maximă'
    
    def is_within_window(self, obj):
        return obj.is_within_window()
    is_within_window.boolean = True
    is_within_window.short_description = 'În fereastră'


@admin.register(IPBlock)
class IPBlockAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'reason', 'blocked_at', 'blocked_until', 'is_permanent', 'is_active_status')
    list_filter = ('reason', 'is_permanent', 'blocked_at')
    search_fields = ('ip_address', 'user_agent')
    readonly_fields = ('blocked_at',)
    
    fieldsets = (
        (None, {
            'fields': ('ip_address', 'reason', 'is_permanent')
        }),
        ('Detalii blocare', {
            'fields': ('blocked_until', 'user_agent', 'notes')
        }),
        ('Moderare', {
            'fields': ('blocked_by', 'blocked_at')
        }),
    )
    
    def is_active_status(self, obj):
        is_active = obj.is_active()
        if is_active:
            return format_html('<span style="color: red;">Activ</span>')
        else:
            return format_html('<span style="color: green;">Expirat</span>')
    is_active_status.short_description = 'Status'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'report_type', 'get_content_object', 'status', 'created_at')
    list_filter = ('report_type', 'status', 'created_at')
    search_fields = ('reporter__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('reporter', 'report_type', 'status')
        }),
        ('Conținut raportat', {
            'fields': ('content_type', 'object_id', 'description')
        }),
        ('Moderare', {
            'fields': ('reviewed_by', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_content_object(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return "Obiect șters"
    get_content_object.short_description = 'Conținut raportat'
    
    actions = ['mark_as_resolved', 'mark_as_dismissed']
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(
            status='resolved',
            reviewed_by=request.user,
            updated_at=timezone.now()
        )
        self.message_user(request, f'{updated} raportări marcate ca rezolvate.')
    mark_as_resolved.short_description = 'Marchează ca rezolvate'
    
    def mark_as_dismissed(self, request, queryset):
        updated = queryset.update(
            status='dismissed',
            reviewed_by=request.user,
            updated_at=timezone.now()
        )
        self.message_user(request, f'{updated} raportări respinse.')
    mark_as_dismissed.short_description = 'Respinge raportările'


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'moderator', 'target_user', 'action_type', 'created_at', 'expires_at', 'is_active')
    list_filter = ('action_type', 'is_active', 'created_at')
    search_fields = ('moderator__username', 'target_user__username', 'reason')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('moderator', 'target_user', 'action_type')
        }),
        ('Detalii', {
            'fields': ('reason', 'duration_hours', 'expires_at')
        }),
        ('Conținut (opțional)', {
            'fields': ('content_type', 'object_id')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nou obiect
            obj.moderator = request.user
            
            # Calculează data de expirare dacă e specificată durata
            if obj.duration_hours:
                from datetime import timedelta
                obj.expires_at = timezone.now() + timedelta(hours=obj.duration_hours)
        
        super().save_model(request, obj, form, change)


@admin.register(ImageModerationQueue)
class ImageModerationQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_content_object', 'status', 'has_faces', 'has_text', 'confidence_score', 'created_at')
    list_filter = ('status', 'has_faces', 'has_text', 'created_at')
    search_fields = ('image_path',)
    readonly_fields = ('created_at', 'reviewed_at')
    
    fieldsets = (
        (None, {
            'fields': ('status', 'image_path')
        }),
        ('Conținut', {
            'fields': ('content_type', 'object_id')
        }),
        ('Analiză automată', {
            'fields': ('has_faces', 'has_text', 'confidence_score')
        }),
        ('Moderare manuală', {
            'fields': ('reviewed_by', 'review_notes', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def get_content_object(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return "Obiect șters"
    get_content_object.short_description = 'Conținut'
    
    actions = ['approve_images', 'reject_images']
    
    def approve_images(self, request, queryset):
        updated = queryset.update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} imagini aprobate.')
    approve_images.short_description = 'Aprobă imaginile'
    
    def reject_images(self, request, queryset):
        updated = queryset.update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} imagini respinse.')
    reject_images.short_description = 'Respinge imaginile'


# Customize admin site
admin.site.site_header = "Bricli - Administrare"
admin.site.site_title = "Bricli Admin"
admin.site.index_title = "Panou de administrare"
