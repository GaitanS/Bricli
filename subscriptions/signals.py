"""
Subscription signals - Auto-sync user changes to Stripe

Ensures Stripe customer data stays in sync with local user data.
"""

import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import stripe

from accounts.models import User
from .models import CraftsmanSubscription

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@receiver(post_save, sender=User)
def sync_user_to_stripe(sender, instance, created, **kwargs):
    """
    Sync user email/name changes to Stripe customer.

    Triggered when User model is saved.

    Args:
        sender: User model class
        instance: User instance
        created: Boolean - True if new user
        **kwargs: Additional signal kwargs
    """
    # Skip if new user (no Stripe customer yet)
    if created:
        return

    # Only sync for craftsmen with active subscriptions
    if instance.user_type != 'craftsman':
        return

    try:
        # Get craftsman subscription
        subscription = CraftsmanSubscription.objects.get(
            craftsman__user=instance
        )

        # Skip if no Stripe customer ID
        if not subscription.stripe_customer_id:
            return

        # Update Stripe customer
        stripe.Customer.modify(
            subscription.stripe_customer_id,
            email=instance.email,
            name=instance.get_full_name() or instance.username,
        )

        logger.info(
            f"Synced user {instance.id} to Stripe customer {subscription.stripe_customer_id}"
        )

    except CraftsmanSubscription.DoesNotExist:
        # No subscription yet, skip
        pass

    except stripe.error.StripeError as e:
        # Log error but don't block user update
        logger.error(f"Failed to sync user {instance.id} to Stripe: {e}")
