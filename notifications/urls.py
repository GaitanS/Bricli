from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'notifications'

# API Router
router = DefaultRouter()

# Web URLs
urlpatterns = [
    # Web views
    path('', views.NotificationListView.as_view(), name='list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='detail'),
    path('preferences/', views.notification_preferences_view, name='preferences'),
    
    # AJAX endpoints
    path('toggle-read/<int:notification_id>/', views.toggle_notification_read, name='toggle_read'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete'),
    
    # API endpoints
    path('api/', include([
        # Notification CRUD
        path('notifications/', views.NotificationListAPIView.as_view(), name='api_list'),
        path('notifications/<int:pk>/', views.NotificationDetailAPIView.as_view(), name='api_detail'),
        path('notifications/create/', views.NotificationCreateAPIView.as_view(), name='api_create'),
        
        # Notification management
        path('notifications/mark-all-read/', views.mark_all_read, name='api_mark_all_read'),
        path('notifications/unread-count/', views.unread_count, name='api_unread_count'),
        path('notifications/bulk/', views.BulkNotificationAPIView.as_view(), name='api_bulk'),
        path('notifications/stats/', views.NotificationStatsAPIView.as_view(), name='api_stats'),
        
        # Preferences
        path('preferences/', views.NotificationPreferenceAPIView.as_view(), name='api_preferences'),
        
        # Push notifications
        path('push/subscribe/', views.PushSubscriptionAPIView.as_view(), name='api_push_subscribe'),
        path('push/test/', views.test_push_notification, name='api_push_test'),
        
        # Router URLs
        path('', include(router.urls)),
    ])),
]