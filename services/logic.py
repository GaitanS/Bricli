from typing import TYPE_CHECKING, Any, Dict, Optional
import logging

from notifications.services import NotificationService

if TYPE_CHECKING:
    from .models import Order, Quote
    from accounts.models import CraftsmanProfile

logger = logging.getLogger(__name__)

def notify_new_quote(quote: 'Quote') -> Any:
    """Notify client about new quote using centralized NotificationService"""
    return NotificationService().create_notification(
        recipient=quote.order.client,
        title=f'Ofertă nouă pentru "{quote.order.title}"',
        message=(
            f"{quote.craftsman.user.get_full_name() or quote.craftsman.user.username} "
            f"a trimis o ofertă de {quote.price} RON."
        ),
        notification_type="new_quote",
        priority="high",
        sender=quote.craftsman.user,
        action_url=f"/servicii/comanda/{quote.order.id}/",
        related_object_type="quote",
        related_object_id=quote.id,
        data={"order_id": quote.order.id, "quote_id": quote.id, "price": float(quote.price)},
    )


def notify_quote_accepted(quote: 'Quote') -> Any:
    """Notify craftsman about accepted quote using centralized NotificationService"""
    return NotificationService().create_notification(
        recipient=quote.craftsman.user,
        title="Oferta ta a fost acceptată!",
        message=(
            f'Clientul a acceptat oferta ta pentru "{quote.order.title}". '
            "Te rugăm să confirmi că poți prelua această comandă."
        ),
        notification_type="quote_accepted",
        priority="high",
        action_url=f"/servicii/comanda/{quote.order.id}/",
        related_object_type="quote",
        related_object_id=quote.id,
        data={"order_id": quote.order.id, "quote_id": quote.id},
    )


def notify_quote_rejected(quote: 'Quote') -> Any:
    """Notify craftsman about rejected quote using centralized NotificationService"""
    return NotificationService().create_notification(
        recipient=quote.craftsman.user,
        title="Oferta ta a fost respinsă",
        message=(f'Din păcate, oferta ta pentru "{quote.order.title}" nu a fost acceptată.'),
        notification_type="quote_rejected",
        priority="medium",
        action_url=f"/servicii/comanda/{quote.order.id}/",
        related_object_type="quote",
        related_object_id=quote.id,
        data={"order_id": quote.order.id, "quote_id": quote.id},
    )


def notify_order_request(order: 'Order', craftsman: 'CraftsmanProfile') -> Any:
    """Notify craftsman about new personal/direct order request using NotificationService"""
    return NotificationService().create_notification(
        recipient=craftsman.user,
        notification_type="personal_order",
        title="Solicitare personală de ofertă",
        message=(
            f'Ai primit o solicitare personală de ofertă pentru "{order.title}" în '
            f"{order.city.name}, {order.county.name}. Clientul {order.client.get_full_name() or order.client.username} "
            "te-a ales special pentru această lucrare!"
        ),
        priority="high",
        sender=order.client,
        action_url=f"/servicii/comanda/{order.id}/",
        related_object_type="order",
        related_object_id=order.id,
        data={"order_id": order.id, "is_personal_request": True, "invited_craftsman_id": craftsman.user.id},
    )


def notify_new_order_to_craftsmen(order: 'Order') -> int:
    """
    Notify all craftsmen who have the order's service registered that a new order is available.

    Args:
        order: Order instance that was just published

    Returns:
        int: Number of notifications successfully sent
    """
    # Import locally to avoid circular imports (logic -> models -> logic)
    from accounts.models import CraftsmanProfile
    from .models import Quote

    # Get all craftsmen who have this service registered
    craftsmen_with_service = CraftsmanProfile.objects.filter(
        services__service=order.service,
        user__is_active=True
    ).select_related('user').distinct()

    # Exclude craftsmen who already quoted on this order
    craftsmen_who_quoted = Quote.objects.filter(
        order=order
    ).values_list('craftsman_id', flat=True)

    eligible_craftsmen = craftsmen_with_service.exclude(
        id__in=craftsmen_who_quoted
    )[:50]  # Limit to 50 to avoid overwhelming the system

    if not eligible_craftsmen.exists():
        logger.info(f"No eligible craftsmen to notify for order {order.id}")
        return 0

    # Determine notification priority based on order urgency
    is_urgent = order.urgency in ['urgent', 'high']
    priority = "urgent" if is_urgent else "normal"

    # Prepare notification content
    budget_text = ""
    if order.budget_min and order.budget_max:
        budget_text = f" Buget: {order.budget_min}-{order.budget_max} RON."
    elif order.budget_max:
        budget_text = f" Buget: până la {order.budget_max} RON."

    urgency_text = {
        'urgent': ' URGENT!',
        'high': ' (În următoarele zile)',
        'medium': '',
        'low': ''
    }.get(order.urgency, '')

    title = f"Comandă nouă: {order.service.name}{urgency_text}"
    message = (
        f'Comandă nouă în {order.city.name}, {order.county.name}: "{order.title}".{budget_text} '
        f'Click pentru a vedea detalii și a trimite ofertă!'
    )

    # Send notifications
    notifications_sent = 0
    for craftsman in eligible_craftsmen:
        try:
            NotificationService.create_notification(
                recipient=craftsman.user,
                title=title,
                message=message,
                notification_type="new_order",
                priority=priority,
                sender=None,  # System notification
                action_url=f"/servicii/comanda/{order.id}/",
                related_object_type="order",
                related_object_id=order.id,
                send_email=is_urgent,  # Only send email for urgent/high urgency orders
                send_push=True,  # Always send push notification
                data={
                    "order_id": order.id,
                    "service_id": order.service.id,
                    "service_name": order.service.name,
                    "location": f"{order.city.name}, {order.county.name}",
                    "urgency": order.urgency
                }
            )
            notifications_sent += 1
        except Exception as e:
            logger.error(f"Failed to notify craftsman {craftsman.user.id} about order {order.id}: {str(e)}")
            continue

    logger.info(f"Notified {notifications_sent} craftsmen about new order {order.id}")
    return notifications_sent
