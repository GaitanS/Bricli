"""
Subscription Service - Business logic for subscription management

Handles:
- Stripe customer creation
- Subscription upgrades/downgrades
- Cancellations
- Refunds (14-day withdrawal right - OUG 34/2014)
- Monthly usage resets
"""

import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
import stripe

from .models import CraftsmanSubscription, SubscriptionTier, SubscriptionLog
from .email_service import SubscriptionEmailService

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionError(Exception):
    """Base exception for subscription-related errors."""
    pass


class InsufficientQuotaError(SubscriptionError):
    """Raised when craftsman has used all free tier leads."""
    pass


class MissingFiscalDataError(SubscriptionError):
    """Raised when fiscal data is required but missing."""
    pass


class RefundNotAllowedError(SubscriptionError):
    """Raised when refund is requested outside 14-day window."""
    pass


class SubscriptionService:
    """Service for managing craftsman subscriptions."""

    @staticmethod
    def create_stripe_customer(craftsman):
        """
        Create a Stripe customer for the craftsman.

        Args:
            craftsman: CraftsmanProfile instance

        Returns:
            str: Stripe customer ID

        Raises:
            SubscriptionError: If customer creation fails
        """
        try:
            customer = stripe.Customer.create(
                email=craftsman.user.email,
                name=craftsman.user.get_full_name() or craftsman.user.username,
                metadata={
                    'craftsman_id': craftsman.id,
                    'user_id': craftsman.user.id,
                    'fiscal_type': craftsman.fiscal_type or 'PF',
                },
                description=f"Craftsman: {craftsman.user.get_full_name()}",
            )

            logger.info(f"Created Stripe customer {customer.id} for craftsman {craftsman.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed for craftsman {craftsman.id}: {e}")
            raise SubscriptionError(f"Failed to create payment account: {str(e)}")

    @staticmethod
    def validate_fiscal_data(craftsman):
        """
        Validate that craftsman has required fiscal data for invoicing.

        Args:
            craftsman: CraftsmanProfile instance

        Raises:
            MissingFiscalDataError: If required fiscal data is missing
        """
        required_fields = [
            'fiscal_type',
            'fiscal_address_street',
            'fiscal_address_city',
            'fiscal_address_county',
            'phone',
        ]

        missing_fields = []
        for field in required_fields:
            if not getattr(craftsman, field, None):
                missing_fields.append(field)

        # Check CUI for PFA/SRL or CNP for PF
        if craftsman.fiscal_type in ['PFA', 'SRL']:
            if not craftsman.cui:
                missing_fields.append('cui')
            if not craftsman.company_name:
                missing_fields.append('company_name')
        elif craftsman.fiscal_type == 'PF':
            if not craftsman.cnp:
                missing_fields.append('cnp')

        if missing_fields:
            raise MissingFiscalDataError(
                f"Missing required fiscal data: {', '.join(missing_fields)}. "
                "Please complete your fiscal information before upgrading."
            )

    @staticmethod
    @transaction.atomic
    def upgrade_to_paid(craftsman, tier_name, payment_method_id, waive_withdrawal=False):
        """
        Upgrade craftsman to a paid tier.

        Args:
            craftsman: CraftsmanProfile instance
            tier_name: 'plus' or 'pro'
            payment_method_id: Stripe payment method ID from frontend
            waive_withdrawal: Boolean - if True, craftsman waives 14-day refund right

        Returns:
            CraftsmanSubscription: Updated subscription

        Raises:
            SubscriptionError: If upgrade fails
            MissingFiscalDataError: If fiscal data is incomplete
        """
        # Validate fiscal data first
        SubscriptionService.validate_fiscal_data(craftsman)

        # Get the target tier
        try:
            tier = SubscriptionTier.objects.get(name=tier_name)
        except SubscriptionTier.DoesNotExist:
            raise SubscriptionError(f"Tier '{tier_name}' does not exist")

        if tier.name == 'free':
            raise SubscriptionError("Cannot upgrade to free tier")

        # Get or create subscription record
        subscription = CraftsmanSubscription.objects.select_for_update().get(
            craftsman=craftsman
        )

        old_tier = subscription.tier

        # Create or get Stripe customer
        if not subscription.stripe_customer_id:
            subscription.stripe_customer_id = SubscriptionService.create_stripe_customer(craftsman)
            subscription.save(update_fields=['stripe_customer_id'])

        try:
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=subscription.stripe_customer_id,
            )

            # Set as default payment method
            stripe.Customer.modify(
                subscription.stripe_customer_id,
                invoice_settings={'default_payment_method': payment_method_id},
            )

            # Cancel existing Stripe subscription if any
            if subscription.stripe_subscription_id:
                stripe.Subscription.delete(subscription.stripe_subscription_id)

            # Create new Stripe subscription with proration
            stripe_subscription = stripe.Subscription.create(
                customer=subscription.stripe_customer_id,
                items=[{'price': tier.stripe_price_id}],
                proration_behavior='create_prorations',  # Mid-month upgrades prorated
                expand=['latest_invoice.payment_intent'],
            )

            # Update local subscription record
            subscription.tier = tier
            subscription.stripe_subscription_id = stripe_subscription.id
            subscription.status = 'active'
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_start, tz=timezone.get_current_timezone()
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_end, tz=timezone.get_current_timezone()
            )

            # Set withdrawal right deadline (14 days from now)
            subscription.withdrawal_right_waived = waive_withdrawal
            if not waive_withdrawal:
                subscription.withdrawal_deadline = timezone.now() + timedelta(days=14)
            else:
                subscription.withdrawal_deadline = None

            # Reset monthly usage on upgrade
            subscription.leads_used_this_month = 0
            subscription.grace_period_end = None

            subscription.save()

            # Log the upgrade
            SubscriptionLog.objects.create(
                subscription=subscription,
                event_type='upgrade',
                old_tier=old_tier,
                new_tier=tier,
                metadata={
                    'stripe_subscription_id': stripe_subscription.id,
                    'withdrawal_waived': waive_withdrawal,
                    'payment_method_id': payment_method_id[-4:],  # Last 4 digits only
                },
            )

            logger.info(
                f"Craftsman {craftsman.id} upgraded from {old_tier.name} to {tier.name}. "
                f"Stripe subscription: {stripe_subscription.id}"
            )

            # Send upgrade confirmation email
            SubscriptionEmailService.send_upgrade_confirmation(subscription)

            return subscription

        except stripe.error.CardError as e:
            # Card was declined
            logger.warning(f"Card declined for craftsman {craftsman.id}: {e}")
            raise SubscriptionError(f"Payment declined: {e.user_message}")

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error during upgrade for craftsman {craftsman.id}: {e}")
            raise SubscriptionError(f"Payment processing failed: {str(e)}")

    @staticmethod
    @transaction.atomic
    def cancel_subscription(craftsman, immediate=False):
        """
        Cancel craftsman's subscription.

        Args:
            craftsman: CraftsmanProfile instance
            immediate: If True, cancel immediately. If False, cancel at period end.

        Returns:
            CraftsmanSubscription: Updated subscription
        """
        subscription = CraftsmanSubscription.objects.select_for_update().get(
            craftsman=craftsman
        )

        old_tier = subscription.tier
        free_tier = SubscriptionTier.objects.get(name='free')

        if subscription.stripe_subscription_id:
            try:
                if immediate:
                    # Cancel immediately
                    stripe.Subscription.delete(subscription.stripe_subscription_id)

                    # Downgrade to free tier now
                    subscription.tier = free_tier
                    subscription.status = 'canceled'
                    subscription.stripe_subscription_id = None
                    subscription.current_period_start = timezone.now()
                    subscription.current_period_end = None
                    subscription.grace_period_end = None
                    subscription.withdrawal_deadline = None

                else:
                    # Cancel at period end
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True,
                    )

                    subscription.status = 'canceled'

                subscription.save()

                # Log the cancellation
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    event_type='cancel',
                    old_tier=old_tier,
                    new_tier=free_tier if immediate else old_tier,
                    metadata={
                        'immediate': immediate,
                        'stripe_subscription_id': subscription.stripe_subscription_id,
                    },
                )

                logger.info(
                    f"Craftsman {craftsman.id} canceled subscription. "
                    f"Immediate: {immediate}, Tier: {old_tier.name} -> "
                    f"{'free' if immediate else 'pending cancellation'}"
                )

                return subscription

            except stripe.error.StripeError as e:
                logger.error(f"Stripe error during cancellation for craftsman {craftsman.id}: {e}")
                raise SubscriptionError(f"Cancellation failed: {str(e)}")

        else:
            # No Stripe subscription, just downgrade locally
            subscription.tier = free_tier
            subscription.status = 'active'
            subscription.save()

            logger.info(f"Craftsman {craftsman.id} downgraded to free tier (no Stripe subscription)")
            return subscription

    @staticmethod
    @transaction.atomic
    def request_refund(craftsman):
        """
        Process refund request for craftsman (14-day withdrawal right - OUG 34/2014).

        Args:
            craftsman: CraftsmanProfile instance

        Returns:
            dict: Refund details {refund_id, amount, status}

        Raises:
            RefundNotAllowedError: If refund window expired or not eligible
        """
        subscription = CraftsmanSubscription.objects.select_for_update().get(
            craftsman=craftsman
        )

        # Check if refund is allowed
        can_refund, reason = subscription.can_request_refund()
        if not can_refund:
            raise RefundNotAllowedError(reason)

        old_tier = subscription.tier
        free_tier = SubscriptionTier.objects.get(name='free')

        try:
            # Get the latest invoice from Stripe
            invoices = stripe.Invoice.list(
                customer=subscription.stripe_customer_id,
                limit=1,
            )

            if not invoices.data:
                raise SubscriptionError("No invoice found for refund")

            latest_invoice = invoices.data[0]

            if not latest_invoice.charge:
                raise SubscriptionError("No charge found on latest invoice")

            # Create refund
            refund = stripe.Refund.create(
                charge=latest_invoice.charge,
                reason='requested_by_customer',
                metadata={
                    'craftsman_id': craftsman.id,
                    'withdrawal_right': 'OUG_34_2014',
                },
            )

            # Cancel subscription immediately
            if subscription.stripe_subscription_id:
                stripe.Subscription.delete(subscription.stripe_subscription_id)

            # Update subscription
            subscription.tier = free_tier
            subscription.status = 'refunded'
            subscription.stripe_subscription_id = None
            subscription.current_period_start = timezone.now()
            subscription.current_period_end = None
            subscription.grace_period_end = None
            subscription.withdrawal_deadline = None
            subscription.withdrawal_right_waived = False
            subscription.save()

            # Log the refund
            SubscriptionLog.objects.create(
                subscription=subscription,
                event_type='refund',
                old_tier=old_tier,
                new_tier=free_tier,
                metadata={
                    'refund_id': refund.id,
                    'amount_cents': refund.amount,
                    'amount_ron': refund.amount / 100,
                    'charge_id': latest_invoice.charge,
                },
            )

            logger.info(
                f"Refund processed for craftsman {craftsman.id}. "
                f"Refund ID: {refund.id}, Amount: {refund.amount / 100} RON"
            )

            # Send refund confirmation email
            SubscriptionEmailService.send_refund_confirmation(
                subscription=subscription,
                amount_ron=refund.amount / 100
            )

            return {
                'refund_id': refund.id,
                'amount_cents': refund.amount,
                'amount_ron': refund.amount / 100,
                'status': refund.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund error for craftsman {craftsman.id}: {e}")
            raise SubscriptionError(f"Refund processing failed: {str(e)}")

    @staticmethod
    def reset_monthly_usage(subscription):
        """
        Reset monthly lead usage counter.

        Called by webhook when invoice.payment_succeeded event is received.

        Args:
            subscription: CraftsmanSubscription instance
        """
        subscription.leads_used_this_month = 0
        subscription.save(update_fields=['leads_used_this_month'])

        logger.info(f"Reset monthly usage for subscription {subscription.id}")
