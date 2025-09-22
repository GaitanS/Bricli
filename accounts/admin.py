from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, County, City, CraftsmanProfile, CraftsmanPortfolio


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_verified', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informații suplimentare', {
            'fields': ('user_type', 'phone_number', 'profile_picture', 'is_verified')
        }),
    )


@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'county', 'postal_code')
    list_filter = ('county',)
    search_fields = ('name', 'county__name')
    ordering = ('county__name', 'name')


class CraftsmanPortfolioInline(admin.TabularInline):
    model = CraftsmanPortfolio
    extra = 0


@admin.register(CraftsmanProfile)
class CraftsmanProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'city', 'average_rating', 'total_reviews', 'is_verified')
    list_filter = ('county', 'is_company', 'user__is_verified')
    search_fields = ('user__username', 'user__email', 'company_name')
    readonly_fields = ('average_rating', 'total_reviews', 'total_jobs_completed')
    inlines = [CraftsmanPortfolioInline]

    def is_verified(self, obj):
        return obj.user.is_verified
    is_verified.boolean = True
    is_verified.short_description = 'Verificat'
