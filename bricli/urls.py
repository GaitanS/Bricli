"""
URL configuration for bricli project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.api_views import HealthCheckAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/health/", HealthCheckAPIView.as_view(), name="api_health"),
    # App URLs
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("services/", include("services.urls")),
    path("messages/", include("messaging.urls")),
    path("moderation/", include("moderation.urls")),
    path("notifications/", include("notifications.urls")),
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
