from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationType(models.TextChoices):
    """Types of notifications available in the system"""

    NEW_ORDER = "new_order", "Comandă nouă"
    ORDER_UPDATE = "order_update", "Actualizare comandă"
    NEW_QUOTE = "new_quote", "Ofertă nouă"
    QUOTE_ACCEPTED = "quote_accepted", "Ofertă acceptată"
    QUOTE_REJECTED = "quote_rejected", "Ofertă respinsă"
    PAYMENT_RECEIVED = "payment_received", "Plată primită"
    PAYMENT_REQUIRED = "payment_required", "Plată necesară"
    REVIEW_RECEIVED = "review_received", "Recenzie primită"
    MESSAGE_RECEIVED = "message_received", "Mesaj nou"
    ACCOUNT_VERIFIED = "account_verified", "Cont verificat"
    SYSTEM_ANNOUNCEMENT = "system_announcement", "Anunț sistem"
    REMINDER = "reminder", "Memento"


class NotificationPriority(models.TextChoices):
    """Priority levels for notifications"""

    LOW = "low", "Scăzută"
    NORMAL = "normal", "Normală"
    HIGH = "high", "Înaltă"
    URGENT = "urgent", "Urgentă"


class Notification(models.Model):
    """Model for storing user notifications"""

    # Core fields
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_notifications", verbose_name="Destinatar"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_user_notifications",
        verbose_name="Expeditor",
    )

    # Notification content
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices, verbose_name="Tip notificare")
    title = models.CharField(max_length=200, verbose_name="Titlu")
    message = models.TextField(verbose_name="Mesaj")

    # Priority and status
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name="Prioritate",
    )
    is_read = models.BooleanField(default=False, verbose_name="Citită")

    # Related objects (generic foreign keys for flexibility)
    related_object_type = models.CharField(
        max_length=50, blank=True, null=True, help_text="Type of related object (order, quote, message, etc.)"
    )
    related_object_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID of the related object")

    # Action URL
    action_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Link acțiune",
        help_text="URL where user should be redirected when clicking notification",
    )

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Creat la")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Citit la")
    expires_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Expiră la", help_text="Optional expiration date for the notification"
    )

    # Delivery options
    email_sent = models.BooleanField(default=False, verbose_name="Email trimis")
    push_sent = models.BooleanField(default=False, verbose_name="Push trimis")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notificare"
        verbose_name_plural = "Notificări"
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["priority"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def get_priority_class(self):
        """Get CSS class for priority styling"""
        priority_classes = {
            NotificationPriority.LOW: "text-muted",
            NotificationPriority.NORMAL: "text-info",
            NotificationPriority.HIGH: "text-warning",
            NotificationPriority.URGENT: "text-danger",
        }
        return priority_classes.get(self.priority, "text-info")

    def get_type_icon(self):
        """Get FontAwesome icon for notification type"""
        type_icons = {
            NotificationType.NEW_ORDER: "fas fa-shopping-cart",
            NotificationType.ORDER_UPDATE: "fas fa-edit",
            NotificationType.NEW_QUOTE: "fas fa-file-invoice-dollar",
            NotificationType.QUOTE_ACCEPTED: "fas fa-check-circle",
            NotificationType.QUOTE_REJECTED: "fas fa-times-circle",
            NotificationType.PAYMENT_RECEIVED: "fas fa-money-bill-wave",
            NotificationType.PAYMENT_REQUIRED: "fas fa-exclamation-triangle",
            NotificationType.REVIEW_RECEIVED: "fas fa-star",
            NotificationType.MESSAGE_RECEIVED: "fas fa-envelope",
            NotificationType.ACCOUNT_VERIFIED: "fas fa-user-check",
            NotificationType.SYSTEM_ANNOUNCEMENT: "fas fa-bullhorn",
            NotificationType.REMINDER: "fas fa-bell",
        }
        return type_icons.get(self.notification_type, "fas fa-info-circle")


class NotificationPreference(models.Model):
    """User preferences for different types of notifications"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name="Utilizator",
    )

    # Email preferences
    email_new_orders = models.BooleanField(default=True, verbose_name="Email pentru comenzi noi")
    email_quotes = models.BooleanField(default=True, verbose_name="Email pentru oferte")
    email_payments = models.BooleanField(default=True, verbose_name="Email pentru plăți")
    email_messages = models.BooleanField(default=True, verbose_name="Email pentru mesaje")
    email_reviews = models.BooleanField(default=True, verbose_name="Email pentru recenzii")
    email_system = models.BooleanField(default=True, verbose_name="Email pentru anunțuri sistem")

    # Push notification preferences
    push_new_orders = models.BooleanField(default=True, verbose_name="Push pentru comenzi noi")
    push_quotes = models.BooleanField(default=True, verbose_name="Push pentru oferte")
    push_payments = models.BooleanField(default=True, verbose_name="Push pentru plăți")
    push_messages = models.BooleanField(default=True, verbose_name="Push pentru mesaje")
    push_reviews = models.BooleanField(default=True, verbose_name="Push pentru recenzii")
    push_system = models.BooleanField(default=False, verbose_name="Push pentru anunțuri sistem")

    # General preferences
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ("never", "Niciodată"),
            ("daily", "Zilnic"),
            ("weekly", "Săptămânal"),
        ],
        default="daily",
        verbose_name="Frecvența rezumatului",
    )

    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Ora de început liniște",
        help_text="Nu trimite notificări push în acest interval",
    )
    quiet_hours_end = models.TimeField(null=True, blank=True, verbose_name="Ora de sfârșit liniște")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")

    class Meta:
        verbose_name = "Preferință notificare"
        verbose_name_plural = "Preferințe notificări"

    def __str__(self):
        return f"Preferințe notificări - {self.user.username}"

    def should_send_email(self, notification_type):
        """Check if email should be sent for this notification type"""
        email_mapping = {
            NotificationType.NEW_ORDER: self.email_new_orders,
            NotificationType.ORDER_UPDATE: self.email_new_orders,
            NotificationType.NEW_QUOTE: self.email_quotes,
            NotificationType.QUOTE_ACCEPTED: self.email_quotes,
            NotificationType.QUOTE_REJECTED: self.email_quotes,
            NotificationType.PAYMENT_RECEIVED: self.email_payments,
            NotificationType.PAYMENT_REQUIRED: self.email_payments,
            NotificationType.REVIEW_RECEIVED: self.email_reviews,
            NotificationType.MESSAGE_RECEIVED: self.email_messages,
            NotificationType.SYSTEM_ANNOUNCEMENT: self.email_system,
        }
        return email_mapping.get(notification_type, True)

    def should_send_push(self, notification_type):
        """Check if push notification should be sent for this notification type"""
        push_mapping = {
            NotificationType.NEW_ORDER: self.push_new_orders,
            NotificationType.ORDER_UPDATE: self.push_new_orders,
            NotificationType.NEW_QUOTE: self.push_quotes,
            NotificationType.QUOTE_ACCEPTED: self.push_quotes,
            NotificationType.QUOTE_REJECTED: self.push_quotes,
            NotificationType.PAYMENT_RECEIVED: self.push_payments,
            NotificationType.PAYMENT_REQUIRED: self.push_payments,
            NotificationType.REVIEW_RECEIVED: self.push_reviews,
            NotificationType.MESSAGE_RECEIVED: self.push_messages,
            NotificationType.SYSTEM_ANNOUNCEMENT: self.push_system,
        }
        return push_mapping.get(notification_type, True)


class PushSubscription(models.Model):
    """Store push notification subscriptions for web push"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions", verbose_name="Utilizator"
    )

    endpoint = models.URLField(verbose_name="Endpoint")
    p256dh_key = models.TextField(verbose_name="Cheie P256DH")
    auth_key = models.TextField(verbose_name="Cheie Auth")

    user_agent = models.TextField(blank=True, verbose_name="User Agent")

    is_active = models.BooleanField(default=True, verbose_name="Activ")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Creat la")
    last_used = models.DateTimeField(default=timezone.now, verbose_name="Ultima utilizare")

    class Meta:
        unique_together = ["user", "endpoint"]
        verbose_name = "Abonament Push"
        verbose_name_plural = "Abonamente Push"

    def __str__(self):
        return f"Push subscription - {self.user.username}"
