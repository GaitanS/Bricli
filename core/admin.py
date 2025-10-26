from django.contrib import admin

from .models import FAQ, BlogPost, SiteSettings, Testimonial, CityLandingPage, CityLandingFAQ


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "rating", "is_featured", "created_at")
    list_filter = ("rating", "is_featured", "created_at")
    list_editable = ("is_featured",)
    search_fields = ("name", "location", "content")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order", "is_active")
    list_filter = ("category", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("question", "answer")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "published_at", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")


class CityLandingFAQInline(admin.TabularInline):
    """Inline admin for FAQs on City Landing Pages"""
    model = CityLandingFAQ
    extra = 1
    fields = ('question', 'answer', 'order', 'is_active')


@admin.register(CityLandingPage)
class CityLandingPageAdmin(admin.ModelAdmin):
    """Admin for SEO City Landing Pages"""
    list_display = ("profession", "city_name", "is_active", "craftsmen_count", "reviews_count", "created_at")
    list_filter = ("profession", "city_name", "is_active", "created_at")
    search_fields = ("profession", "city_name", "meta_title", "meta_description")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [CityLandingFAQInline]

    fieldsets = (
        ('Informații Bază', {
            'fields': ('city_name', 'city_slug', 'profession', 'profession_slug', 'is_active')
        }),
        ('SEO Meta Tags', {
            'fields': ('meta_title', 'meta_description', 'h1_title')
        }),
        ('Conținut', {
            'fields': ('intro_text', 'services_text', 'prices_text', 'how_it_works_text')
        }),
        ('Statistici', {
            'fields': ('craftsmen_count', 'reviews_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CityLandingFAQ)
class CityLandingFAQAdmin(admin.ModelAdmin):
    """Admin for City Landing FAQs"""
    list_display = ("landing_page", "question", "order", "is_active")
    list_filter = ("landing_page__profession", "landing_page__city_name", "is_active")
    search_fields = ("question", "answer", "landing_page__city_name", "landing_page__profession")
    list_editable = ("order", "is_active")
