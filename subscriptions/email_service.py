"""
Email Notification Service for Subscriptions

Handles all subscription-related email communications.

Email Types:
1. subscription_upgraded - Welcome to Plus/Pro
2. payment_failed - Day 0 warning
3. payment_failed_day3 - Grace period reminder
4. subscription_canceled - Downgraded to Free
5. lead_limit_warning - 4/5 leads used
6. lead_limit_reached - 5/5 - Upgrade prompt
7. invoice_generated - Monthly invoice with PDF
8. refund_request_received - Refund confirmation
"""

import logging
from typing import Optional
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .models import CraftsmanSubscription, Invoice

logger = logging.getLogger(__name__)


class SubscriptionEmailService:
    """
    Service for sending subscription-related emails.

    All emails are sent in HTML format with plain text fallback.
    """

    @staticmethod
    def _send_email(
        subject: str,
        template_name: str,
        context: dict,
        recipient_email: str,
        attachments: Optional[list] = None
    ) -> bool:
        """
        Send an email using Django's email backend.

        Args:
            subject: Email subject line
            template_name: Name of template (without .html extension)
            context: Template context dictionary
            recipient_email: Recipient email address
            attachments: List of (filename, content, mimetype) tuples

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Add common context variables
            context.update({
                'site_name': 'Bricli',
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://bricli.ro',
                'current_year': timezone.now().year,
            })

            # Render HTML email
            html_content = render_to_string(
                f'subscriptions/emails/{template_name}.html',
                context
            )

            # Create plain text version
            text_content = strip_tags(html_content)

            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            email.attach_alternative(html_content, "text/html")

            # Add attachments if provided
            if attachments:
                for filename, content, mimetype in attachments:
                    email.attach(filename, content, mimetype)

            # Send
            email.send(fail_silently=False)

            logger.info(f"Email sent successfully: {template_name} to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email {template_name} to {recipient_email}: {e}")
            return False

    @classmethod
    def send_upgrade_confirmation(cls, subscription: CraftsmanSubscription) -> bool:
        """
        Send welcome email after successful upgrade to paid tier.

        Args:
            subscription: CraftsmanSubscription instance

        Returns:
            bool: True if sent successfully
        """
        craftsman = subscription.craftsman
        user = craftsman.user

        context = {
            'user_name': user.get_full_name() or user.username,
            'tier_name': subscription.tier.display_name,
            'tier_price': subscription.tier.price / 100,  # Convert cents to RON
            'renewal_date': subscription.current_period_end,
            'features': cls._get_tier_features(subscription.tier),
            'withdrawal_deadline': subscription.withdrawal_deadline,
            'can_request_refund': subscription.can_request_refund() if hasattr(subscription, 'can_request_refund') else False,
        }

        return cls._send_email(
            subject=f'Bine ai venit la {subscription.tier.display_name}!',
            template_name='subscription_upgraded',
            context=context,
            recipient_email=user.email
        )

    @classmethod
    def send_payment_failed(cls, subscription: CraftsmanSubscription, is_reminder: bool = False) -> bool:
        """
        Send payment failed notification.

        Args:
            subscription: CraftsmanSubscription instance
            is_reminder: True if this is day 3 reminder, False if day 0

        Returns:
            bool: True if sent successfully
        """
        craftsman = subscription.craftsman
        user = craftsman.user

        days_remaining = None
        if subscription.grace_period_end:
            days_remaining = (subscription.grace_period_end - timezone.now()).days

        context = {
            'user_name': user.get_full_name() or user.username,
            'tier_name': subscription.tier.display_name,
            'tier_price': subscription.tier.price / 100,
            'grace_period_end': subscription.grace_period_end,
            'days_remaining': days_remaining,
            'is_reminder': is_reminder,
            'update_payment_url': f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/abonamente/portal/",
        }

        template = 'payment_failed_day3' if is_reminder else 'payment_failed'
        subject = f'Atenție: Plata pentru {subscription.tier.display_name} {"(Reminder)" if is_reminder else ""}'

        return cls._send_email(
            subject=subject,
            template_name=template,
            context=context,
            recipient_email=user.email
        )

    @classmethod
    def send_subscription_canceled(cls, subscription: CraftsmanSubscription, reason: str = 'manual') -> bool:
        """
        Send notification when subscription is canceled/downgraded.

        Args:
            subscription: CraftsmanSubscription instance
            reason: Reason for cancellation ('manual', 'grace_expired', 'dispute')

        Returns:
            bool: True if sent successfully
        """
        craftsman = subscription.craftsman
        user = craftsman.user

        context = {
            'user_name': user.get_full_name() or user.username,
            'old_tier_name': subscription.tier.display_name if subscription.tier.name != 'free' else 'Plan Plus/Pro',
            'new_tier_name': 'Plan Gratuit',
            'reason': reason,
            'free_lead_limit': 5,
            'upgrade_url': f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/abonamente/upgrade/plus/",
        }

        return cls._send_email(
            subject='Abonamentul tău a fost dezactivat - Bricli',
            template_name='subscription_canceled',
            context=context,
            recipient_email=user.email
        )

    @classmethod
    def send_lead_limit_warning(cls, craftsman_profile, leads_used: int, leads_limit: int) -> bool:
        """
        Send warning when craftsman approaches lead limit (4/5 leads used).

        Args:
            craftsman_profile: CraftsmanProfile instance
            leads_used: Number of leads used
            leads_limit: Total lead limit

        Returns:
            bool: True if sent successfully
        """
        user = craftsman_profile.user

        context = {
            'user_name': user.get_full_name() or user.username,
            'leads_used': leads_used,
            'leads_limit': leads_limit,
            'leads_remaining': leads_limit - leads_used,
            'upgrade_url': f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/abonamente/upgrade/plus/",
        }

        return cls._send_email(
            subject='Atenție: Ești aproape de limita de lead-uri',
            template_name='lead_limit_warning',
            context=context,
            recipient_email=user.email
        )

    @classmethod
    def send_lead_limit_reached(cls, craftsman_profile) -> bool:
        """
        Send notification when craftsman reaches lead limit (5/5 leads).

        Args:
            craftsman_profile: CraftsmanProfile instance

        Returns:
            bool: True if sent successfully
        """
        user = craftsman_profile.user

        context = {
            'user_name': user.get_full_name() or user.username,
            'upgrade_url': f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/abonamente/upgrade/plus/",
            'plus_price': 49,  # RON
            'pro_price': 149,  # RON
        }

        return cls._send_email(
            subject='Limită atinsă - Upgrade pentru lead-uri nelimitate',
            template_name='lead_limit_reached',
            context=context,
            recipient_email=user.email
        )

    @classmethod
    def send_invoice_email(cls, invoice: Invoice) -> bool:
        """
        Send monthly invoice email with PDF attachment.

        Args:
            invoice: Invoice instance

        Returns:
            bool: True if sent successfully
        """
        subscription = invoice.subscription
        craftsman = subscription.craftsman
        user = craftsman.user

        context = {
            'user_name': user.get_full_name() or user.username,
            'invoice_series': invoice.smartbill_series,
            'invoice_number': invoice.smartbill_number,
            'invoice_date': invoice.created_at,
            'total_ron': invoice.total_ron,
            'base_ron': invoice.base_ron,
            'tva_ron': invoice.tva_ron,
            'tier_name': subscription.tier.display_name,
            'invoice_url': f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/abonamente/facturi/{invoice.id}/pdf/",
        }

        # Try to get PDF attachment
        attachments = []
        try:
            from .smartbill_service import InvoiceService
            pdf_content = InvoiceService.get_invoice_pdf(
                series=invoice.smartbill_series,
                number=invoice.smartbill_number
            )
            attachments.append((
                invoice.get_download_filename(),
                pdf_content,
                'application/pdf'
            ))
        except Exception as e:
            logger.warning(f"Could not attach PDF to invoice email: {e}")
            # Continue without attachment - user can download from portal

        success = cls._send_email(
            subject=f'Factura {invoice.smartbill_series}-{invoice.smartbill_number} - Bricli',
            template_name='invoice_generated',
            context=context,
            recipient_email=user.email,
            attachments=attachments
        )

        # Mark invoice as sent
        if success:
            invoice.email_sent = True
            invoice.email_sent_at = timezone.now()
            invoice.save()

        return success

    @classmethod
    def send_refund_confirmation(cls, subscription: CraftsmanSubscription, amount_ron: float) -> bool:
        """
        Send refund confirmation email.

        Args:
            subscription: CraftsmanSubscription instance
            amount_ron: Refund amount in RON

        Returns:
            bool: True if sent successfully
        """
        craftsman = subscription.craftsman
        user = craftsman.user

        context = {
            'user_name': user.get_full_name() or user.username,
            'amount_ron': amount_ron,
            'tier_name': subscription.tier.display_name,
            'processing_days': '5-7',
        }

        return cls._send_email(
            subject='Rambursare procesată - Bricli',
            template_name='refund_request_received',
            context=context,
            recipient_email=user.email
        )

    @staticmethod
    def _get_tier_features(tier) -> list:
        """
        Get list of features for a tier.

        Args:
            tier: SubscriptionTier instance

        Returns:
            List of feature strings
        """
        features = []

        if tier.monthly_lead_limit is None:
            features.append('Lead-uri nelimitate')
        else:
            features.append(f'{tier.monthly_lead_limit} lead-uri pe lună')

        if tier.max_portfolio_images:
            features.append(f'{tier.max_portfolio_images} imagini în portofoliu')

        if tier.priority_in_search > 0:
            features.append('Prioritate în rezultatele căutării')

        if tier.show_in_featured:
            features.append('Afișare în secțiunea Featured')

        if tier.can_attach_pdf:
            features.append('Atașare documente PDF la oferte')

        if tier.analytics_access:
            features.append('Acces la Analytics avansate')

        if tier.profile_badge:
            features.append(f'Badge: {tier.profile_badge}')

        return features
