from django.contrib import admin
from .models import (
    ServiceCategory, Service, CraftsmanService, Order, OrderImage,
    Quote, Review, ReviewImage
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'category__name')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CraftsmanService)
class CraftsmanServiceAdmin(admin.ModelAdmin):
    list_display = ('craftsman', 'service', 'price_from', 'price_to', 'price_unit')
    list_filter = ('service__category',)
    search_fields = ('craftsman__user__username', 'service__name')


class OrderImageInline(admin.TabularInline):
    model = OrderImage
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'service', 'status', 'urgency', 'created_at')
    list_filter = ('status', 'urgency', 'service__category', 'county')
    search_fields = ('title', 'client__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderImageInline]

    fieldsets = (
        ('Informații de bază', {
            'fields': ('client', 'title', 'description', 'service')
        }),
        ('Locație', {
            'fields': ('county', 'city', 'address')
        }),
        ('Detalii', {
            'fields': ('budget_min', 'budget_max', 'urgency', 'preferred_date')
        }),
        ('Status', {
            'fields': ('status', 'assigned_craftsman')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('order', 'craftsman', 'price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__title', 'craftsman__user__username')
    readonly_fields = ('created_at', 'updated_at')


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('craftsman', 'client', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('craftsman__user__username', 'client__username', 'comment')
    readonly_fields = ('created_at',)
    inlines = [ReviewImageInline]
