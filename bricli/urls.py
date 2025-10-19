"""
URL configuration for bricli project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.api_views import HealthCheckAPIView
from blog.sitemaps import BlogPostSitemap, BlogCategorySitemap

# Sitemap configuration for SEO
sitemaps = {
    'blog': BlogPostSitemap,
    'blog_categories': BlogCategorySitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/health/", HealthCheckAPIView.as_view(), name="api_health"),
    # App URLs - Romanian ASCII paths with separate namespaces
    path("", include("core.urls")),
    # Auth URLs at root (namespace: 'auth')
    path("", include("accounts.auth_urls")),  # /inregistrare/, /autentificare/
    # Profile URLs under /conturi/ (namespace: 'accounts')
    path("conturi/", include("accounts.profile_urls")),  # /conturi/profil/, /conturi/meseriasi/
    # Services, messaging, etc.
    path("servicii/", include("services.urls")),  # /servicii/categorii/
    path("mesaje/", include("messaging.urls")),  # /mesaje/conversatie/
    path("moderation/", include("moderation.urls")),
    path("notifications/", include("notifications.urls")),
    # Subscriptions (webhooks and management)
    path("abonamente/", include("subscriptions.urls")),  # /abonamente/webhook/stripe/
    # Blog - SEO-optimized content for organic traffic
    path("blog/", include("blog.urls")),  # /blog/articol-slug/
    # SEO - Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

# Custom error handlers
handler404 = "core.views.custom_404_view"
handler500 = "core.views.custom_500_view"

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None
    )
