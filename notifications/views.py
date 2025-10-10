from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationPreference
from .serializers import (
    BulkNotificationSerializer,
    NotificationCreateSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
    NotificationStatsSerializer,
    PushSubscriptionSerializer,
)
from .services import PushNotificationService


class NotificationListView(LoginRequiredMixin, ListView):
    """View for listing user notifications"""

    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            Notification.objects.filter(recipient=self.request.user).select_related("sender").order_by("-created_at")
        )

        # Filter by type if specified
        notification_type = self.request.GET.get("type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by read status
        is_read = self.request.GET.get("read")
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == "true")

        # Search functionality
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(message__icontains=search))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notification_types"] = Notification.NOTIFICATION_TYPES
        context["current_type"] = self.request.GET.get("type", "")
        context["current_read"] = self.request.GET.get("read", "")
        context["search_query"] = self.request.GET.get("search", "")

        # Add statistics
        user_notifications = Notification.objects.filter(recipient=self.request.user)
        context["stats"] = {
            "total": user_notifications.count(),
            "unread": user_notifications.filter(is_read=False).count(),
            "today": user_notifications.filter(created_at__date=timezone.now().date()).count(),
        }

        return context


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """View for displaying notification details"""

    model = Notification
    template_name = "notifications/notification_detail.html"
    context_object_name = "notification"

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Mark as read when viewed
        if not obj.is_read:
            obj.mark_as_read()
        return obj


@login_required
def notification_preferences_view(request):
    """View for managing notification preferences"""
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Update preferences
        for field in [
            "digest_frequency",
            "email_new_orders",
            "email_quotes",
            "email_payments",
            "email_messages",
            "email_reviews",
            "email_system",
            "push_new_orders",
            "push_quotes",
            "push_payments",
            "push_messages",
            "push_reviews",
            "push_system",
        ]:
            if field in request.POST:
                if field.startswith(("email_", "push_")):
                    setattr(preferences, field, request.POST.get(field) == "on")
                else:
                    setattr(preferences, field, request.POST.get(field))

        # Handle quiet hours
        quiet_start = request.POST.get("quiet_hours_start")
        quiet_end = request.POST.get("quiet_hours_end")

        if quiet_start and quiet_end:
            preferences.quiet_hours_start = datetime.strptime(quiet_start, "%H:%M").time()
            preferences.quiet_hours_end = datetime.strptime(quiet_end, "%H:%M").time()
        else:
            preferences.quiet_hours_start = None
            preferences.quiet_hours_end = None

        preferences.save()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Preferințele au fost salvate."})

    context = {"preferences": preferences, "digest_choices": NotificationPreference.DIGEST_FREQUENCY_CHOICES}

    return render(request, "notifications/preferences.html", context)


# API Views
class NotificationListAPIView(generics.ListAPIView):
    """API view for listing notifications"""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = (
            Notification.objects.filter(recipient=self.request.user).select_related("sender").order_by("-created_at")
        )

        # Apply filters
        notification_type = self.request.query_params.get("type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        is_read = self.request.query_params.get("read")
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == "true")

        return queryset


class NotificationDetailAPIView(generics.RetrieveUpdateAPIView):
    """API view for notification details"""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Mark as read when accessed via API
        if not instance.is_read:
            instance.mark_as_read()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NotificationCreateAPIView(generics.CreateAPIView):
    """API view for creating notifications (admin only)"""

    serializer_class = NotificationCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class NotificationPreferenceAPIView(generics.RetrieveUpdateAPIView):
    """API view for notification preferences"""

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        preferences, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return preferences


class PushSubscriptionAPIView(generics.CreateAPIView):
    """API view for managing push subscriptions"""

    serializer_class = PushSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class NotificationStatsAPIView(APIView):
    """API view for notification statistics"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(recipient=user)

        # Calculate statistics
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)

        stats = {
            "total_notifications": notifications.count(),
            "unread_notifications": notifications.filter(is_read=False).count(),
            "notifications_today": notifications.filter(created_at__date=today).count(),
            "notifications_this_week": notifications.filter(created_at__gte=week_ago).count(),
            "notifications_by_type": dict(
                notifications.values("notification_type")
                .annotate(count=Count("id"))
                .values_list("notification_type", "count")
            ),
            "notifications_by_priority": dict(
                notifications.values("priority").annotate(count=Count("id")).values_list("priority", "count")
            ),
        }

        serializer = NotificationStatsSerializer(stats)
        return Response(serializer.data)


class BulkNotificationAPIView(APIView):
    """API view for bulk notification operations"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = BulkNotificationSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            notification_ids = serializer.validated_data["notification_ids"]
            action = serializer.validated_data["action"]

            notifications = Notification.objects.filter(id__in=notification_ids, recipient=request.user)

            if action == "mark_read":
                updated = 0
                for notification in notifications.filter(is_read=False):
                    notification.mark_as_read()
                    updated += 1
                message = f"{updated} notificări au fost marcate ca citite."

            elif action == "mark_unread":
                updated = notifications.filter(is_read=True).update(is_read=False, read_at=None)
                message = f"{updated} notificări au fost marcate ca necitite."

            elif action == "delete":
                deleted_count = notifications.delete()[0]
                message = f"{deleted_count} notificări au fost șterse."

            return Response({"success": True, "message": message})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_all_read(request):
    """Mark all notifications as read for the current user"""
    updated = 0
    notifications = Notification.objects.filter(recipient=request.user, is_read=False)

    for notification in notifications:
        notification.mark_as_read()
        updated += 1

    return Response(
        {"success": True, "message": f"{updated} notificări au fost marcate ca citite.", "updated_count": updated}
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def unread_count(request):
    """Get unread notification count for the current user"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    return Response({"unread_count": count})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def test_push_notification(request):
    """Test push notification for the current user"""
    try:
        service = PushNotificationService()
        success = service.send_push_notification(
            user=request.user,
            title="Test Notification",
            message="Aceasta este o notificare de test.",
            action_url="/notifications/",
        )

        if success:
            return Response({"success": True, "message": "Notificarea push de test a fost trimisă cu succes."})
        else:
            return Response(
                {"success": False, "message": "Nu s-a putut trimite notificarea push de test."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        return Response(
            {"success": False, "message": f"Eroare la trimiterea notificării: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# AJAX Views
@require_http_methods(["POST"])
@login_required
@csrf_exempt
def toggle_notification_read(request, notification_id):
    """Toggle notification read status via AJAX"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)

        if notification.is_read:
            notification.is_read = False
            notification.read_at = None
            notification.save()
            message = "Notificarea a fost marcată ca necitită."
        else:
            notification.mark_as_read()
            message = "Notificarea a fost marcată ca citită."

        return JsonResponse({"success": True, "message": message, "is_read": notification.is_read})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Eroare: {str(e)}"}, status=500)


@require_http_methods(["DELETE"])
@login_required
@csrf_exempt
def delete_notification(request, notification_id):
    """Delete notification via AJAX"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)

        notification.delete()

        return JsonResponse({"success": True, "message": "Notificarea a fost ștearsă cu succes."})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Eroare: {str(e)}"}, status=500)
