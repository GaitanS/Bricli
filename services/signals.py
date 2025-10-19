"""
Signal handlers for services app
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import Quote
from notifications.services import NotificationService


@receiver(post_save, sender=Quote)
def notify_client_new_quote(sender, instance, created, **kwargs):
    """
    Send notification to client when a new quote is received
    """
    if created:  # Only for new quotes, not updates
        quote = instance
        client = quote.order.client
        craftsman = quote.craftsman
        order = quote.order

        # Get craftsman name
        craftsman_name = craftsman.user.get_full_name() or craftsman.user.username

        # Create notification
        NotificationService.create_notification(
            recipient=client,
            title=f"🎉 Ai primit o ofertă nouă!",
            message=f"{craftsman_name} a trimis o ofertă de {quote.price} RON pentru comanda ta '{order.title}'.",
            notification_type="quote",
            priority="high",
            sender=craftsman.user,
            action_url=reverse("services:order_detail", kwargs={"pk": order.pk}),
            related_object_type="quote",
            related_object_id=quote.pk,
            data={
                "quote_id": quote.pk,
                "order_id": order.pk,
                "craftsman_id": craftsman.pk,
                "price": str(quote.price),
            },
            send_email=False,  # Optional: enable if you want email notifications
            send_push=True,    # Send web push notification
        )
