"""
Stripe Webhook Handler with Idempotency

Handles all Stripe webhook events for subscription lifecycle.

CRITICAL FEATURES:
- Idempotency via StripeWebhookEvent.event_id
- Signature verification
- Rate limiting
- Comprehensive error handling
- Audit logging
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import mail_admins
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
import stripe

from .models import (
    CraftsmanSubscription,
    SubscriptionTier,
    StripeWebhookEvent,
    SubscriptionLog,
    Invoice,
)
from .smartbill_service import InvoiceService, SmartBillAPIError, MissingFiscalDataError
from .email_service import SubscriptionEmailService

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
@require_POST
@ratelimit(key='ip', rate='100/m', block=True)
def stripe_webhook(request):
    """
    Stripe webhook endpoint with idempotency and comprehensive event handling.

    Handles:
    - invoice.payment_succeeded: Reset monthly usage, clear grace period
    - invoice.payment_failed: Set grace period (7 days)
    - customer.subscription.deleted: Downgrade to Free
    - charge.dispute.created: Suspend account (fraud detection)

    Returns:
        HttpResponse: 200 OK on success, 400/500 on error
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    # Step 1: Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        logger.error("Invalid webhook payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        logger.error("Invalid webhook signature")
        return HttpResponse(status=400)

    # Step 2: Check idempotency - prevent duplicate processing
    if StripeWebhookEvent.objects.filter(event_id=event.id).exists():
        logger.info(f"Webhook event {event.id} already processed, skipping")
        return HttpResponse(status=200)

    # Step 3: Process event based on type
    try:
        if event.type == 'invoice.payment_succeeded':
            handle_payment_succeeded(event)

        elif event.type == 'invoice.payment_failed':
            handle_payment_failed(event)

        elif event.type == 'customer.subscription.deleted':
            handle_subscription_deleted(event)

        elif event.type == 'customer.subscription.updated':
            handle_subscription_updated(event)

        elif event.type == 'charge.dispute.created':
            handle_dispute_created(event)

        else:
            # Log unhandled event types for monitoring
            logger.info(f"Unhandled webhook event type: {event.type}")

        # Step 4: Log successful processing
        StripeWebhookEvent.objects.create(
            event_id=event.id,
            event_type=event.type,
            event_data=event.to_dict(),
            status='success',
        )

        logger.info(f"Successfully processed webhook event {event.id} ({event.type})")
        return HttpResponse(status=200)

    except Exception as e:
        # Step 5: Log failure and alert admins
        logger.error(f"Webhook processing failed for event {event.id}: {e}", exc_info=True)

        StripeWebhookEvent.objects.create(
            event_id=event.id,
            event_type=event.type,
            event_data=event.to_dict(),
            status='failed',
        )

        # Alert admins for critical failures
        mail_admins(
            subject=f"Stripe Webhook Failure: {event.type}",
            message=f"Event ID: {event.id}\nError: {str(e)}\n\nSee logs for details.",
        )

        # Return 500 so Stripe retries
        return HttpResponse(status=500)


def handle_payment_succeeded(event):
    """
    Handle successful payment: Reset monthly usage, activate subscription.

    Args:
        event: Stripe Event object
    """
    invoice = event.data.object
    subscription_id = invoice.subscription

    if not subscription_id:
        logger.warning(f"Invoice {invoice.id} has no subscription ID")
        return

    try:
        subscription = CraftsmanSubscription.objects.get(
            stripe_subscription_id=subscription_id
        )

        # Reset monthly usage counter
        subscription.leads_used_this_month = 0

        # Clear grace period if any
        subscription.grace_period_end = None

        # Ensure status is active
        subscription.status = 'active'

        # Update period dates from Stripe
        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        subscription.current_period_start = timezone.datetime.fromtimestamp(
            stripe_sub.current_period_start, tz=timezone.get_current_timezone()
        )
        subscription.current_period_end = timezone.datetime.fromtimestamp(
            stripe_sub.current_period_end, tz=timezone.get_current_timezone()
        )

        subscription.save()

        # Log the event
        SubscriptionLog.objects.create(
            subscription=subscription,
            event_type='payment_succeeded',
            old_tier=subscription.tier,
            new_tier=subscription.tier,
            metadata={
                'invoice_id': invoice.id,
                'amount_paid': invoice.amount_paid,
                'period_start': stripe_sub.current_period_start,
                'period_end': stripe_sub.current_period_end,
            },
        )

        logger.info(
            f"Payment succeeded for subscription {subscription.id}. "
            f"Usage reset, grace period cleared."
        )

        # Phase 5: Generate Smart Bill invoice
        try:
            # Generate invoice via Smart Bill API
            invoice_data = InvoiceService.create_invoice(
                subscription=subscription,
                stripe_invoice_id=invoice.id
            )

            # Save invoice record
            from decimal import Decimal
            total_ron = Decimal(subscription.tier.price) / 100
            base_ron, tva_ron, _ = InvoiceService.calculate_tva(total_ron)

            craftsman = subscription.craftsman
            Invoice.objects.create(
                subscription=subscription,
                stripe_invoice_id=invoice.id,
                smartbill_series=invoice_data.get('series', ''),
                smartbill_number=str(invoice_data.get('number', '')),
                smartbill_url=invoice_data.get('url', ''),
                total_ron=total_ron,
                base_ron=base_ron,
                tva_ron=tva_ron,
                client_name=craftsman.company_name or craftsman.user.get_full_name(),
                client_fiscal_code=craftsman.cui or craftsman.cnp,
                client_address=f"{craftsman.fiscal_address_street}, {craftsman.fiscal_address_city}",
            )

            logger.info(
                f"Smart Bill invoice created: {invoice_data.get('series')}-{invoice_data.get('number')} "
                f"for subscription {subscription.id}"
            )

            # Phase 6: Send invoice email with PDF
            invoice_record = Invoice.objects.get(stripe_invoice_id=invoice.id)
            SubscriptionEmailService.send_invoice_email(invoice_record)

        except MissingFiscalDataError as e:
            # Missing fiscal data - log for admin follow-up
            logger.error(
                f"Cannot generate invoice for subscription {subscription.id}: {e}"
            )
            mail_admins(
                subject=f"Missing Fiscal Data for Invoice - Subscription {subscription.id}",
                message=f"Subscription: {subscription.id}\n"
                        f"Craftsman: {subscription.craftsman.user.email}\n"
                        f"Error: {e}\n\n"
                        f"Please contact craftsman to complete fiscal data.",
            )

        except SmartBillAPIError as e:
            # API error - invoice marked as pending in SubscriptionLog by InvoiceService
            logger.error(
                f"Smart Bill API error for subscription {subscription.id}: {e}"
            )
            # Will be retried by cron job (retry_failed_invoices)

    except CraftsmanSubscription.DoesNotExist:
        logger.error(f"No subscription found for Stripe subscription {subscription_id}")


def handle_payment_failed(event):
    """
    Handle failed payment: Set 7-day grace period, send warning email.

    Args:
        event: Stripe Event object
    """
    invoice = event.data.object
    subscription_id = invoice.subscription

    if not subscription_id:
        logger.warning(f"Invoice {invoice.id} has no subscription ID")
        return

    try:
        subscription = CraftsmanSubscription.objects.get(
            stripe_subscription_id=subscription_id
        )

        # Set status to past_due
        subscription.status = 'past_due'

        # Set 7-day grace period
        subscription.grace_period_end = timezone.now() + timedelta(days=7)

        subscription.save()

        # Log the event
        SubscriptionLog.objects.create(
            subscription=subscription,
            event_type='payment_failed',
            old_tier=subscription.tier,
            new_tier=subscription.tier,
            metadata={
                'invoice_id': invoice.id,
                'amount_due': invoice.amount_due,
                'grace_period_end': subscription.grace_period_end.isoformat(),
                'attempt_count': invoice.attempt_count,
            },
        )

        logger.warning(
            f"Payment failed for subscription {subscription.id}. "
            f"Grace period set until {subscription.grace_period_end}. "
            f"Attempt {invoice.attempt_count}"
        )

        # Phase 6: Send payment failed email (Day 0 warning)
        SubscriptionEmailService.send_payment_failed(subscription, is_reminder=False)

    except CraftsmanSubscription.DoesNotExist:
        logger.error(f"No subscription found for Stripe subscription {subscription_id}")


def handle_subscription_deleted(event):
    """
    Handle subscription cancellation: Downgrade to Free tier.

    Args:
        event: Stripe Event object
    """
    stripe_subscription = event.data.object
    subscription_id = stripe_subscription.id

    try:
        subscription = CraftsmanSubscription.objects.get(
            stripe_subscription_id=subscription_id
        )

        old_tier = subscription.tier
        free_tier = SubscriptionTier.objects.get(name='free')

        # Downgrade to free
        subscription.tier = free_tier
        subscription.status = 'canceled'
        subscription.stripe_subscription_id = None
        subscription.current_period_end = None
        subscription.grace_period_end = None
        subscription.withdrawal_deadline = None

        subscription.save()

        # Log the event
        SubscriptionLog.objects.create(
            subscription=subscription,
            event_type='subscription_deleted',
            old_tier=old_tier,
            new_tier=free_tier,
            metadata={
                'stripe_subscription_id': subscription_id,
                'canceled_at': stripe_subscription.canceled_at,
            },
        )

        logger.info(
            f"Subscription {subscription.id} deleted. "
            f"Downgraded from {old_tier.name} to free."
        )

        # Phase 6: Send subscription canceled email
        reason = 'grace_expired' if subscription.grace_period_end else 'manual'
        SubscriptionEmailService.send_subscription_canceled(subscription, reason=reason)

    except CraftsmanSubscription.DoesNotExist:
        logger.error(f"No subscription found for Stripe subscription {subscription_id}")


def handle_subscription_updated(event):
    """
    Handle subscription updates: Sync status and period dates.

    Args:
        event: Stripe Event object
    """
    stripe_subscription = event.data.object
    subscription_id = stripe_subscription.id

    try:
        subscription = CraftsmanSubscription.objects.get(
            stripe_subscription_id=subscription_id
        )

        # Update period dates
        subscription.current_period_start = timezone.datetime.fromtimestamp(
            stripe_subscription.current_period_start, tz=timezone.get_current_timezone()
        )
        subscription.current_period_end = timezone.datetime.fromtimestamp(
            stripe_subscription.current_period_end, tz=timezone.get_current_timezone()
        )

        # Sync status
        status_mapping = {
            'active': 'active',
            'past_due': 'past_due',
            'canceled': 'canceled',
            'unpaid': 'past_due',
        }
        subscription.status = status_mapping.get(stripe_subscription.status, 'active')

        subscription.save()

        logger.info(f"Subscription {subscription.id} updated from Stripe")

    except CraftsmanSubscription.DoesNotExist:
        logger.error(f"No subscription found for Stripe subscription {subscription_id}")


def handle_dispute_created(event):
    """
    Handle chargeback/dispute: Suspend account immediately (fraud detection).

    Args:
        event: Stripe Event object
    """
    charge = event.data.object
    customer_id = charge.customer

    try:
        subscription = CraftsmanSubscription.objects.get(
            stripe_customer_id=customer_id
        )

        # Suspend user account immediately
        subscription.craftsman.user.is_active = False
        subscription.craftsman.user.save()

        # Log the event
        SubscriptionLog.objects.create(
            subscription=subscription,
            event_type='dispute_created',
            old_tier=subscription.tier,
            new_tier=subscription.tier,
            metadata={
                'charge_id': charge.id,
                'dispute_id': charge.dispute,
                'amount': charge.amount,
                'reason': charge.outcome.get('reason') if charge.outcome else None,
            },
        )

        logger.critical(
            f"FRAUD ALERT: Dispute created for subscription {subscription.id}. "
            f"User account suspended. Charge: {charge.id}"
        )

        # Alert admins immediately
        mail_admins(
            subject="FRAUD ALERT: Stripe Dispute Created",
            message=f"Subscription: {subscription.id}\n"
                    f"Craftsman: {subscription.craftsman.user.email}\n"
                    f"Charge: {charge.id}\n"
                    f"Dispute: {charge.dispute}\n"
                    f"Amount: {charge.amount / 100} RON\n\n"
                    f"User account has been suspended.",
        )

    except CraftsmanSubscription.DoesNotExist:
        logger.error(f"No subscription found for Stripe customer {customer_id}")
