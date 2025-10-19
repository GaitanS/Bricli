"""
Lead Quota Service - Manages lead distribution based on subscription tiers

Replaces the old wallet-based LeadFeeService.
Now uses subscription tier limits instead of wallet deductions.
"""

import logging

from django.db import transaction
from django.utils import timezone

from subscriptions.models import CraftsmanSubscription
from subscriptions.services import InsufficientQuotaError
from subscriptions.email_service import SubscriptionEmailService

logger = logging.getLogger(__name__)


class LeadQuotaService:
    """
    Service for managing lead quota and distribution.

    Business Rules:
    - Free tier: 5 leads/month, then blocked
    - Plus tier: Unlimited leads
    - Pro tier: Unlimited leads + priority
    - Grace period: 7 days after payment failure
    """

    @classmethod
    def can_receive_lead(cls, craftsman_user):
        """
        Check if craftsman can receive a new lead.

        Args:
            craftsman_user: User instance (must have user_type='craftsman')

        Returns:
            tuple: (can_receive: bool, error_message: str or None)
        """
        # Validation
        if craftsman_user.user_type != 'craftsman':
            return (False, "User is not a craftsman")

        try:
            subscription = CraftsmanSubscription.objects.select_related('tier').get(
                craftsman__user=craftsman_user
            )

            # Check if subscription is active or in grace period
            if subscription.status == 'refunded':
                return (False, "Subscription was refunded. Please upgrade to receive leads.")

            if subscription.status == 'canceled':
                # Check if still within current period
                if subscription.current_period_end and timezone.now() > subscription.current_period_end:
                    return (False, "Subscription expired. Please renew to receive leads.")

            # Check grace period for past_due subscriptions
            if subscription.status == 'past_due':
                if subscription.grace_period_end:
                    if timezone.now() > subscription.grace_period_end:
                        return (
                            False,
                            "Payment failed and grace period expired. "
                            "Please update payment method to receive leads."
                        )
                    # Still in grace period - allow access
                else:
                    # No grace period set, block immediately
                    return (False, "Payment failed. Please update payment method to receive leads.")

            # Check tier limits
            tier = subscription.tier

            # Free tier has monthly limit
            if tier.monthly_lead_limit is not None:
                if subscription.leads_used_this_month >= tier.monthly_lead_limit:
                    return (
                        False,
                        f"Monthly lead limit reached ({tier.monthly_lead_limit}/{tier.monthly_lead_limit}). "
                        "Upgrade to Plus or Pro for unlimited leads."
                    )

            # All checks passed
            return (True, None)

        except CraftsmanSubscription.DoesNotExist:
            logger.error(f"No subscription found for craftsman user {craftsman_user.id}")
            return (False, "No active subscription found. Please contact support.")

    @classmethod
    @transaction.atomic
    def process_shortlist(cls, craftsman_user, order):
        """
        Process shortlist request - check quota and increment usage.

        This method should be called when a client adds a craftsman to their shortlist.

        Args:
            craftsman_user: User instance (craftsman)
            order: Order instance

        Returns:
            Shortlist: The created/updated shortlist entry

        Raises:
            InsufficientQuotaError: If craftsman has no available quota
            ValueError: If user is not a craftsman
        """
        from services.models import Shortlist

        # Check if can receive lead
        can_receive, error_msg = cls.can_receive_lead(craftsman_user)

        if not can_receive:
            logger.warning(
                f"Craftsman {craftsman_user.id} cannot receive lead for order {order.id}: {error_msg}"
            )
            raise InsufficientQuotaError(error_msg)

        # Get subscription with row-level lock to prevent race conditions
        subscription = CraftsmanSubscription.objects.select_for_update().get(
            craftsman__user=craftsman_user
        )

        # Create/update shortlist entry
        shortlist, created = Shortlist.objects.get_or_create(
            order=order,
            craftsman=craftsman_user,
            defaults={
                'lead_fee_amount': 0,  # No fee charged with subscription model
                'charged_at': timezone.now(),
            },
        )

        if not created:
            # Update existing shortlist
            shortlist.charged_at = timezone.now()
            shortlist.save(update_fields=['charged_at'])
            logger.info(f"Updated existing shortlist {shortlist.id}")
        else:
            logger.info(f"Created new shortlist {shortlist.id}")

        # Increment usage counter for free tier
        if subscription.tier.monthly_lead_limit is not None:
            subscription.increment_lead_usage()

            # Log warning if approaching limit
            if subscription.leads_used_this_month == subscription.tier.monthly_lead_limit - 1:
                logger.warning(
                    f"Craftsman {craftsman_user.id} used {subscription.leads_used_this_month} / "
                    f"{subscription.tier.monthly_lead_limit} leads. One lead remaining!"
                )

                # Phase 6: Send "4/5 leads used" notification email
                SubscriptionEmailService.send_lead_limit_warning(
                    craftsman_profile=subscription.craftsman,
                    leads_used=subscription.leads_used_this_month,
                    leads_limit=subscription.tier.monthly_lead_limit
                )

            elif subscription.leads_used_this_month >= subscription.tier.monthly_lead_limit:
                logger.warning(
                    f"Craftsman {craftsman_user.id} reached lead limit "
                    f"({subscription.leads_used_this_month} / {subscription.tier.monthly_lead_limit})"
                )

                # Phase 6: Send "5/5 leads used - upgrade now" notification email
                SubscriptionEmailService.send_lead_limit_reached(
                    craftsman_profile=subscription.craftsman
                )

        return shortlist

    @classmethod
    def get_quota_status(cls, craftsman_user):
        """
        Get quota status for craftsman.

        Args:
            craftsman_user: User instance

        Returns:
            dict: Status information including:
                - tier_name: str
                - leads_used: int
                - leads_limit: int or None (None = unlimited)
                - leads_remaining: int or None
                - can_receive: bool
                - error_message: str or None
        """
        try:
            subscription = CraftsmanSubscription.objects.select_related('tier').get(
                craftsman__user=craftsman_user
            )

            can_receive, error_msg = cls.can_receive_lead(craftsman_user)

            leads_limit = subscription.tier.monthly_lead_limit
            leads_remaining = None

            if leads_limit is not None:
                leads_remaining = max(0, leads_limit - subscription.leads_used_this_month)

            return {
                'tier_name': subscription.tier.name,
                'tier_display': subscription.tier.display_name,
                'leads_used': subscription.leads_used_this_month,
                'leads_limit': leads_limit,
                'leads_remaining': leads_remaining,
                'can_receive': can_receive,
                'error_message': error_msg,
                'status': subscription.status,
                'period_end': subscription.current_period_end,
            }

        except CraftsmanSubscription.DoesNotExist:
            return {
                'tier_name': None,
                'tier_display': None,
                'leads_used': 0,
                'leads_limit': 0,
                'leads_remaining': 0,
                'can_receive': False,
                'error_message': 'No active subscription',
                'status': None,
                'period_end': None,
            }
