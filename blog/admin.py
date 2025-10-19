from django.contrib import admin
from .models import BlogCategory, BlogTag, BlogPost


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Informații Bază', {
            'fields': ('name', 'slug', 'description', 'icon', 'is_active')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'published_at', 'views_count']
    list_filter = ['status', 'category', 'published_at', 'created_at']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    date_hierarchy = 'published_at'
    readonly_fields = ['views_count', 'created_at', 'updated_at']

    fieldsets = (
        ('Conținut', {
            'fields': ('title', 'slug', 'author', 'category', 'tags', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt')
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'read_time_minutes')
        }),
        ('SEO - Meta Tags', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('SEO - Open Graph', {
            'fields': ('og_image', 'og_title', 'og_description'),
            'classes': ('collapse',)
        }),
        ('Analytics & Schema', {
            'fields': ('views_count', 'schema_type', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)
