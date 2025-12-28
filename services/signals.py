"""
Signal handlers for services app
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import Quote
from .logic import notify_new_quote


@receiver(post_save, sender=Quote)
def notify_client_new_quote(sender, instance, created, **kwargs):
    """
    Send notification to client when a new quote is received
    """
    if created:  # Only for new quotes, not updates
        notify_new_quote(instance)
