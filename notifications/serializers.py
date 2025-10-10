from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Notification, NotificationPreference, PushSubscription

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""

    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    time_since = serializers.SerializerMethodField()
    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "notification_type_display",
            "priority",
            "priority_display",
            "is_read",
            "action_url",
            "sender_name",
            "sender_username",
            "created_at",
            "read_at",
            "time_since",
            "expires_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "read_at",
            "sender_name",
            "sender_username",
            "time_since",
            "notification_type_display",
            "priority_display",
        ]

    def get_time_since(self, obj):
        """Get human-readable time since notification was created"""
        from django.utils import timezone

        now = timezone.now()
        time_diff = now - obj.created_at

        if time_diff.days > 0:
            return f"acum {time_diff.days} {'zi' if time_diff.days == 1 else 'zile'}"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            return f"acum {hours} {'oră' if hours == 1 else 'ore'}"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            return f"acum {minutes} {'minut' if minutes == 1 else 'minute'}"
        else:
            return "acum câteva secunde"


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""

    class Meta:
        model = Notification
        fields = [
            "recipient",
            "title",
            "message",
            "notification_type",
            "priority",
            "action_url",
            "related_object_type",
            "related_object_id",
            "expires_at",
        ]

    def validate_recipient(self, value):
        """Validate that recipient exists and is active"""
        if not value.is_active:
            raise serializers.ValidationError("Destinatarul nu este activ.")
        return value

    def validate(self, data):
        """Validate notification data"""
        # Check if related object fields are both provided or both empty
        related_type = data.get("related_object_type")
        related_id = data.get("related_object_id")

        if bool(related_type) != bool(related_id):
            raise serializers.ValidationError("Atât tipul obiectului cât și ID-ul trebuie să fie furnizate împreună.")

        return data


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model"""

    class Meta:
        model = NotificationPreference
        fields = [
            "id",
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
            "quiet_hours_start",
            "quiet_hours_end",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate notification preferences"""
        quiet_start = data.get("quiet_hours_start")
        quiet_end = data.get("quiet_hours_end")

        # If one quiet hour is set, both must be set
        if bool(quiet_start) != bool(quiet_end):
            raise serializers.ValidationError(
                "Atât ora de început cât și ora de sfârșit pentru orele de liniște trebuie să fie setate."
            )

        return data


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for PushSubscription model"""

    class Meta:
        model = PushSubscription
        fields = ["id", "endpoint", "p256dh_key", "auth_key", "user_agent", "is_active", "created_at", "last_used"]
        read_only_fields = ["id", "created_at", "last_used"]

    def validate_endpoint(self, value):
        """Validate push subscription endpoint"""
        if not value.startswith(("https://", "http://")):
            raise serializers.ValidationError("Endpoint-ul trebuie să fie o URL validă.")
        return value

    def create(self, validated_data):
        """Create or update push subscription"""
        user = self.context["request"].user
        endpoint = validated_data["endpoint"]

        # Check if subscription already exists for this user and endpoint
        subscription, created = PushSubscription.objects.get_or_create(
            user=user, endpoint=endpoint, defaults=validated_data
        )

        if not created:
            # Update existing subscription
            for key, value in validated_data.items():
                setattr(subscription, key, value)
            subscription.is_active = True
            subscription.save()

        return subscription


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""

    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    notifications_today = serializers.IntegerField()
    notifications_this_week = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_priority = serializers.DictField()


class BulkNotificationSerializer(serializers.Serializer):
    """Serializer for bulk notification operations"""

    notification_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1, max_length=100)
    action = serializers.ChoiceField(
        choices=[("mark_read", "Marchează ca citite"), ("mark_unread", "Marchează ca necitite"), ("delete", "Șterge")]
    )

    def validate_notification_ids(self, value):
        """Validate that all notification IDs exist and belong to the user"""
        user = self.context["request"].user
        existing_ids = set(Notification.objects.filter(id__in=value, recipient=user).values_list("id", flat=True))

        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"Notificările cu ID-urile {list(invalid_ids)} nu există sau nu vă aparțin."
            )

        return value


class NotificationDigestSerializer(serializers.Serializer):
    """Serializer for notification digest"""

    period = serializers.ChoiceField(choices=[("daily", "Zilnic"), ("weekly", "Săptămânal"), ("monthly", "Lunar")])
    notifications = NotificationSerializer(many=True, read_only=True)
    summary = serializers.DictField(read_only=True)
    user_preferences = NotificationPreferenceSerializer(read_only=True)
