import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal, receiver

from .models import NotificationPreference
from .services import NotificationService

User = get_user_model()
logger = logging.getLogger(__name__)

# Custom signals
notification_bulk_created = Signal()
notification_maintenance = Signal()

# Service instance
notification_service = NotificationService()


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create default notification preferences for new users"""
    if created:
        try:
            NotificationPreference.objects.create(user=instance)
            logger.info(f"Created notification preferences for user {instance.username}")

            # Send welcome notification
            notification_service.create_notification(
                recipient=instance,
                title="Bun venit pe Bricli!",
                message="Vă mulțumim că v-ați alăturat platformei noastre. Explorați serviciile disponibile și găsiți meșterii potriviți pentru proiectele dvs.",
                notification_type="system",
                priority="medium",
                action_url="/services/",
            )
        except Exception as e:
            logger.error(f"Error creating notification preferences for user {instance.username}: {str(e)}")


# Lazy loading of models to avoid circular imports
def get_order_model():
    try:
        from services.models import Order

        return Order
    except ImportError:
        return None


def get_quote_model():
    try:
        from services.models import Quote

        return Quote
    except ImportError:
        return None


def get_review_model():
    try:
        from services.models import Review

        return Review
    except ImportError:
        return None


def get_message_model():
    try:
        from messaging.models import Message

        return Message
    except ImportError:
        return None


# Order notifications
@receiver(post_save)
def handle_order_notifications(sender, instance, created, **kwargs):
    """Handle notifications for order events"""
    Order = get_order_model()
    if not Order or sender != Order:
        return

    try:
        if created:
            # Notify about new order
            notification_service.create_notification(
                recipient=instance.client,
                title="Comandă creată cu succes",
                message=f"Comanda dvs. #{instance.id} a fost creată și va fi vizibilă pentru meșteri.",
                notification_type="order",
                priority="medium",
                action_url=f"/services/order/{instance.id}/",
                data={"order_id": instance.id},
            )
        else:
            # Handle status changes
            if hasattr(instance, "_original_status"):
                old_status = instance._original_status
                if old_status != instance.status:
                    _handle_order_status_change(instance, old_status)
    except Exception as e:
        logger.error(f"Error handling order notifications: {str(e)}")


@receiver(pre_save)
def track_order_status_changes(sender, instance, **kwargs):
    """Track original status for comparison"""
    Order = get_order_model()
    if not Order or sender != Order:
        return

    if instance.pk:
        try:
            original = Order.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Order.DoesNotExist:
            instance._original_status = None


def _handle_order_status_change(order, old_status):
    """Handle notifications for order status changes"""
    status_messages = {
        "published": "Comanda dvs. este acum vizibilă pentru meșteri.",
        "in_progress": "Comanda dvs. este în lucru.",
        "completed": "Comanda dvs. a fost finalizată cu succes.",
        "cancelled": "Comanda dvs. a fost anulată.",
    }

    if order.status in status_messages:
        notification_service.create_notification(
            recipient=order.client,
            title=f"Actualizare comandă #{order.id}",
            message=status_messages[order.status],
            notification_type="order",
            priority="high" if order.status in ["completed", "cancelled"] else "medium",
            action_url=f"/services/order/{order.id}/",
            data={"order_id": order.id, "status": order.status},
        )


# Quote notifications
@receiver(post_save)
def handle_quote_notifications(sender, instance, created, **kwargs):
    """Handle notifications for quote events"""
    Quote = get_quote_model()
    if not Quote or sender != Quote:
        return

    try:
        if created:
            # Notify client about new quote
            notification_service.create_notification(
                recipient=instance.order.client,
                title="Ofertă nouă primită",
                message=f"Ați primit o ofertă nouă de la {instance.craftsman.user.get_full_name() or instance.craftsman.user.username} pentru comanda #{instance.order.id}.",
                notification_type="quote",
                priority="high",
                sender=instance.craftsman.user,
                action_url=f"/services/order/{instance.order.id}/",
                data={"quote_id": instance.id, "order_id": instance.order.id},
            )
        else:
            # Handle status changes
            if hasattr(instance, "_original_status"):
                old_status = instance._original_status
                if old_status != instance.status:
                    _handle_quote_status_change(instance, old_status)
    except Exception as e:
        logger.error(f"Error handling quote notifications: {str(e)}")


@receiver(pre_save)
def track_quote_status_changes(sender, instance, **kwargs):
    """Track original status for comparison"""
    Quote = get_quote_model()
    if not Quote or sender != Quote:
        return

    if instance.pk:
        try:
            original = Quote.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Quote.DoesNotExist:
            instance._original_status = None


def _handle_quote_status_change(quote, old_status):
    """Handle notifications for quote status changes"""
    if quote.status == "accepted":
        # Notify craftsman
        notification_service.create_notification(
            recipient=quote.craftsman.user,
            title="Ofertă acceptată",
            message=f"Oferta dvs. pentru comanda #{quote.order.id} a fost acceptată!",
            notification_type="quote",
            priority="high",
            action_url=f"/services/order/{quote.order.id}/",
            data={"quote_id": quote.id, "order_id": quote.order.id},
        )
    elif quote.status == "rejected":
        # Notify craftsman
        notification_service.create_notification(
            recipient=quote.craftsman.user,
            title="Ofertă respinsă",
            message=f"Oferta dvs. pentru comanda #{quote.order.id} a fost respinsă.",
            notification_type="quote",
            priority="medium",
            action_url=f"/services/order/{quote.order.id}/",
            data={"quote_id": quote.id, "order_id": quote.order.id},
        )


# Message notifications
@receiver(post_save)
def handle_message_notifications(sender, instance, created, **kwargs):
    """Handle notifications for new messages"""
    Message = get_message_model()
    if not Message or sender != Message:
        return

    if created:
        try:
            # Notify recipient about new message
            notification_service.create_notification(
                recipient=instance.recipient,
                title="Mesaj nou",
                message=f"Ați primit un mesaj nou de la {instance.sender.get_full_name() or instance.sender.username}.",
                notification_type="message",
                priority="medium",
                sender=instance.sender,
                action_url=f"/messages/conversation/{instance.conversation.id}/",
                data={"message_id": instance.id, "conversation_id": instance.conversation.id},
            )
        except Exception as e:
            logger.error(f"Error handling message notifications: {str(e)}")


# Review notifications
@receiver(post_save)
def handle_review_notifications(sender, instance, created, **kwargs):
    """Handle notifications for new reviews"""
    Review = get_review_model()
    if not Review or sender != Review:
        return

    if created:
        try:
            # Notify craftsman about new review
            notification_service.create_notification(
                recipient=instance.craftsman.user,
                title="Recenzie nouă",
                message=f"Ați primit o recenzie nouă de la {instance.client.get_full_name() or instance.client.username}.",
                notification_type="review",
                priority="medium",
                sender=instance.client,
                action_url=f"/accounts/profile/{instance.craftsman.user.username}/",
                data={"review_id": instance.id, "rating": instance.rating},
            )
        except Exception as e:
            logger.error(f"Error handling review notifications: {str(e)}")


# System notifications
@receiver(notification_bulk_created)
def handle_bulk_notifications(sender, **kwargs):
    """Handle bulk notification creation"""
    try:
        users = kwargs.get("users", [])
        title = kwargs.get("title", "Notificare sistem")
        message = kwargs.get("message", "")
        notification_type = kwargs.get("notification_type", "system")
        priority = kwargs.get("priority", "medium")

        for user in users:
            notification_service.create_notification(
                recipient=user, title=title, message=message, notification_type=notification_type, priority=priority
            )

        logger.info(f"Created bulk notifications for {len(users)} users")
    except Exception as e:
        logger.error(f"Error handling bulk notifications: {str(e)}")


@receiver(notification_maintenance)
def handle_maintenance_notifications(sender, **kwargs):
    """Handle maintenance notifications"""
    try:
        maintenance_type = kwargs.get("type", "general")
        start_time = kwargs.get("start_time")
        end_time = kwargs.get("end_time")

        if maintenance_type == "scheduled":
            title = "Mentenanță programată"
            message = f"Platforma va fi în mentenanță între {start_time} și {end_time}. Vă rugăm să vă planificați activitățile în consecință."
        else:
            title = "Notificare sistem"
            message = kwargs.get("message", "Actualizare sistem în curs.")

        # Notify all active users
        active_users = User.objects.filter(is_active=True)
        for user in active_users:
            notification_service.create_notification(
                recipient=user, title=title, message=message, notification_type="system", priority="high"
            )

        logger.info(f"Created maintenance notifications for {active_users.count()} users")
    except Exception as e:
        logger.error(f"Error handling maintenance notifications: {str(e)}")
