"""
Admin interface for messaging system
"""
from django.contrib import admin
from .models import Conversation, Message, MessageAttachment, MessageTemplate


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at', 'is_read')
    fields = ('sender', 'recipient', 'content', 'is_read', 'is_system_message', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'get_participants', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('subject', 'participants__username', 'participants__email')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]
    
    def get_participants(self, obj):
        return ", ".join([p.username for p in obj.participants.all()])
    get_participants.short_description = 'Participanți'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'get_content_preview', 'is_read', 'is_system_message', 'created_at')
    list_filter = ('is_read', 'is_system_message', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'content')
    readonly_fields = ('created_at',)
    
    def get_content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    get_content_preview.short_description = 'Conținut'


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'filename', 'file_size', 'content_type', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('filename', 'message__content')
    readonly_fields = ('created_at', 'file_size')


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_type', 'subject', 'is_active')
    list_filter = ('template_type', 'is_active')
    search_fields = ('subject', 'content')
    
    fieldsets = (
        (None, {
            'fields': ('template_type', 'subject', 'is_active')
        }),
        ('Conținut', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
    )
