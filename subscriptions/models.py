from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta


class SubscriptionTier(models.Model):
    """
    Defines the 3 subscription tiers: Free, Plus, Pro

    Tier configuration determines feature access and limits for craftsmen.
    """

    TIER_CHOICES = [
        ('free', 'Free'),
        ('plus', 'Plus'),
        ('pro', 'Pro'),
    ]

    name = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        unique=True,
        help_text="Internal tier identifier"
    )
    display_name = models.CharField(
        max_length=50,
        help_text="Display name for users (e.g., 'Plan Gratuit', 'Plan Plus')"
    )
    price = models.IntegerField(
        help_text="Price in cents (e.g., 4900 for 49 RON)"
    )

    # Feature Limits
    monthly_lead_limit = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum leads per month (NULL = unlimited)"
    )
    max_portfolio_images = models.IntegerField(
        default=3,
        help_text="Maximum portfolio images allowed"
    )

    # Feature Flags
    profile_badge = models.CharField(
        max_length=50,
        blank=True,
        help_text="Badge text to display on profile (e.g., 'Verificat', 'Top Pro')"
    )
    priority_in_search = models.IntegerField(
        default=0,
        help_text="Search result priority (0=normal, 1=medium, 2=high)"
    )
    show_in_featured = models.BooleanField(
        default=False,
        help_text="Show in featured craftsmen section on homepage"
    )
    can_attach_pdf = models.BooleanField(
        default=False,
        help_text="Allow PDF attachments in quotes"
    )
    analytics_access = models.BooleanField(
        default=False,
        help_text="Access to advanced analytics dashboard"
    )

    # Stripe Integration
    stripe_price_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Stripe Price ID (e.g., price_xxxPLUS)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_tiers'
        ordering = ['price']
        indexes = [
            models.Index(fields=['priority_in_search'], name='tier_priority_idx'),
        ]

    def __str__(self):
        return f"{self.display_name} - {self.get_price_ron()} RON/lună"

    def get_price_ron(self):
        """Convert cents to RON"""
        return self.price / 100


class CraftsmanSubscription(models.Model):
    """
    Active subscription for each craftsman

    Tracks subscription status, billing cycle, and usage metrics.
    """

    STATUS_CHOICES = [
        ('active', 'Activă'),
        ('past_due', 'Întârziată'),
        ('canceled', 'Anulată'),
        ('refunded', 'Rambursată'),
    ]

    craftsman = models.OneToOneField(
        'accounts.CraftsmanProfile',
        on_delete=models.CASCADE,
        related_name='subscription',
        help_text="Craftsman who owns this subscription"
    )
    tier = models.ForeignKey(
        SubscriptionTier,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        help_text="Current subscription tier"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Stripe Data
    stripe_subscription_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Stripe Subscription ID (sub_xxx)"
    )
    stripe_customer_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Stripe Customer ID (cus_xxx)"
    )

    # Billing Cycle
    current_period_start = models.DateTimeField(
        help_text="Start of current billing period"
    )
    current_period_end = models.DateTimeField(
        help_text="End of current billing period"
    )

    # Usage Tracking (for Free tier with limits)
    leads_used_this_month = models.IntegerField(
        default=0,
        help_text="Number of leads received this billing period"
    )

    # Grace Period (for failed payments)
    grace_period_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="End of 7-day grace period for failed payments"
    )

    # Withdrawal Right (OUG 34/2014 - Romanian law)
    withdrawal_right_waived = models.BooleanField(
        default=False,
        help_text="User explicitly waived 14-day withdrawal right"
    )
    withdrawal_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Deadline for 14-day withdrawal right (NULL if waived)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'craftsman_subscriptions'
        indexes = [
            models.Index(fields=['status', 'current_period_end'], name='sub_status_end_idx'),
            models.Index(fields=['grace_period_end'], name='sub_grace_idx'),
            models.Index(fields=['withdrawal_deadline'], name='sub_withdrawal_idx'),
            models.Index(fields=['craftsman', 'status'], name='sub_craftsman_status_idx'),
            models.Index(fields=['tier', 'status'], name='sub_tier_status_idx'),
        ]

    def __str__(self):
        return f"{self.craftsman.user.get_full_name()} - {self.tier.display_name}"

    def can_receive_lead(self):
        """
        Check if craftsman can receive a lead based on tier limits and grace period

        Returns:
            bool: True if can receive lead, False otherwise
        """
        # Check if in grace period (still has access during grace)
        if self.status == 'past_due' and self.grace_period_end:
            if timezone.now() <= self.grace_period_end:
                # Still in grace period, allow access
                pass
            else:
                # Grace period expired
                return False

        # Check tier limits
        if self.tier.monthly_lead_limit is None:
            # Unlimited leads (Plus/Pro tier)
            return True

        # Free tier with limit
        return self.leads_used_this_month < self.tier.monthly_lead_limit

    def increment_lead_usage(self):
        """Increment lead usage counter for current month"""
        self.leads_used_this_month += 1
        self.save(update_fields=['leads_used_this_month', 'updated_at'])

    def reset_monthly_usage(self):
        """Reset lead usage counter (called on billing cycle renewal)"""
        self.leads_used_this_month = 0
        self.save(update_fields=['leads_used_this_month', 'updated_at'])

    def can_request_refund(self):
        """
        Check if craftsman can request refund within 14-day withdrawal period

        Per OUG 34/2014 (Romanian consumer law), users have 14 days to withdraw
        unless they explicitly waived this right.

        Returns:
            bool: True if within withdrawal window, False otherwise
        """
        if self.withdrawal_right_waived:
            return False

        if not self.withdrawal_deadline:
            return False

        return timezone.now() <= self.withdrawal_deadline


class StripeWebhookEvent(models.Model):
    """
    Log of processed Stripe webhook events (for idempotency)

    Prevents duplicate processing when Stripe retries failed webhooks.
    """

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    event_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Stripe Event ID (evt_xxx) - UNIQUE constraint ensures idempotency"
    )
    event_type = models.CharField(
        max_length=100,
        help_text="Event type (e.g., invoice.payment_succeeded)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='success'
    )
    event_data = models.JSONField(
        help_text="Full event payload from Stripe"
    )
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stripe_webhook_events'
        ordering = ['-processed_at']
        indexes = [
            models.Index(fields=['event_type', 'processed_at'], name='webhook_type_date_idx'),
            models.Index(fields=['status'], name='webhook_status_idx'),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.event_id} ({self.status})"


class SubscriptionLog(models.Model):
    """
    Audit trail for all subscription changes

    Used for debugging, analytics, and compliance.
    """

    EVENT_CHOICES = [
        ('migration_to_free', 'Migration to Free'),
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade'),
        ('cancel', 'Cancel'),
        ('payment_failed', 'Payment Failed'),
        ('payment_succeeded', 'Payment Succeeded'),
        ('refund_requested', 'Refund Requested'),
        ('invoice_created', 'Invoice Created'),
        ('invoice_pending', 'Invoice Pending'),
    ]

    subscription = models.ForeignKey(
        CraftsmanSubscription,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text="Subscription this log entry belongs to"
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_CHOICES,
        help_text="Type of subscription event"
    )
    old_tier = models.ForeignKey(
        SubscriptionTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_old',
        help_text="Previous tier (NULL for new subscriptions)"
    )
    new_tier = models.ForeignKey(
        SubscriptionTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_new',
        help_text="New tier"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event data (invoice numbers, error messages, etc.)"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscription_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['subscription', 'timestamp'], name='log_sub_time_idx'),
            models.Index(fields=['event_type', 'timestamp'], name='log_event_time_idx'),
        ]

    def __str__(self):
        return f"{self.subscription.craftsman.user.email} - {self.event_type} at {self.timestamp}"


class Invoice(models.Model):
    """
    Romanian fiscal invoice generated via Smart Bill API

    Stores invoice data for subscription payments according to Romanian law.
    """

    subscription = models.ForeignKey(
        CraftsmanSubscription,
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text="Subscription this invoice belongs to"
    )
    stripe_invoice_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Stripe Invoice ID (in_xxx)"
    )

    # Smart Bill Data
    smartbill_series = models.CharField(
        max_length=20,
        help_text="Invoice series (e.g., 'SUBS')"
    )
    smartbill_number = models.CharField(
        max_length=50,
        help_text="Invoice number"
    )
    smartbill_url = models.URLField(
        blank=True,
        help_text="Public URL to view invoice (if available)"
    )

    # Amounts (in RON)
    total_ron = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount including TVA (e.g., 49.00)"
    )
    base_ron = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base amount without TVA (e.g., 41.18)"
    )
    tva_ron = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="TVA amount at 19% (e.g., 7.82)"
    )

    # Fiscal Data Snapshot (for auditing)
    client_name = models.CharField(
        max_length=255,
        help_text="Client name at time of invoice"
    )
    client_fiscal_code = models.CharField(
        max_length=20,
        help_text="CUI or CNP at time of invoice"
    )
    client_address = models.TextField(
        help_text="Full address at time of invoice"
    )

    # PDF Storage (optional - can store locally or link to Smart Bill)
    pdf_file = models.FileField(
        upload_to='invoices/%Y/%m/',
        blank=True,
        null=True,
        help_text="Local copy of PDF invoice"
    )

    # Email Tracking
    email_sent = models.BooleanField(
        default=False,
        help_text="Whether invoice email was sent to client"
    )
    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when invoice email was sent"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_invoices'
        ordering = ['-created_at']
        unique_together = [['smartbill_series', 'smartbill_number']]
        indexes = [
            models.Index(fields=['subscription', 'created_at'], name='invoice_sub_date_idx'),
            models.Index(fields=['email_sent'], name='invoice_email_idx'),
        ]

    def __str__(self):
        return f"Invoice {self.smartbill_series}-{self.smartbill_number} - {self.total_ron} RON"

    def get_download_filename(self):
        """Generate filename for PDF download"""
        return f"Factura_{self.smartbill_series}_{self.smartbill_number}.pdf"
