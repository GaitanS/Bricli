"""
Smart Bill API Integration Service

Handles invoice generation for subscription payments according to Romanian fiscal law.
API Documentation: https://api.smartbill.ro/
"""

import requests
import base64
from typing import Dict, Optional
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import CraftsmanSubscription, SubscriptionLog


class SmartBillAPIError(Exception):
    """Raised when Smart Bill API returns an error."""
    pass


class MissingFiscalDataError(Exception):
    """Raised when craftsman lacks required fiscal data."""
    pass


class InvoiceService:
    """
    Service for generating Romanian fiscal invoices via Smart Bill API.

    Features:
    - TVA (19%) calculation
    - CUI/CNP validation
    - PDF invoice generation
    - Retry logic for failed invoices
    """

    API_BASE_URL = "https://ws.smartbill.ro/SBORO/api"

    @staticmethod
    def _get_auth_header() -> Dict[str, str]:
        """
        Generate HTTP Basic Auth header for Smart Bill API.

        Returns:
            Dict with Authorization header
        """
        username = settings.SMARTBILL_USERNAME
        token = settings.SMARTBILL_API_TOKEN

        credentials = f"{username}:{token}"
        encoded = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def validate_fiscal_data(craftsman) -> None:
        """
        Validate that craftsman has all required fiscal data.

        Args:
            craftsman: CraftsmanProfile instance

        Raises:
            MissingFiscalDataError: If any required field is missing
        """
        required_fields = [
            ('fiscal_type', 'Tipul fiscal (PF/PFA/SRL)'),
            ('fiscal_address_street', 'Adresa fiscală (strada)'),
            ('fiscal_address_city', 'Orașul'),
            ('fiscal_address_county', 'Județul'),
            ('fiscal_address_postal_code', 'Codul poștal'),
        ]

        missing = []
        for field, label in required_fields:
            if not getattr(craftsman, field, None):
                missing.append(label)

        # Check fiscal type-specific fields
        if craftsman.fiscal_type == 'PF':
            if not craftsman.cnp:
                missing.append('CNP (pentru Persoană Fizică)')
        else:  # PFA or SRL
            if not craftsman.cui:
                missing.append('CUI (pentru PFA/SRL)')
            if not craftsman.company_name:
                missing.append('Denumire firmă')

        if missing:
            raise MissingFiscalDataError(
                f"Lipsesc date fiscale obligatorii: {', '.join(missing)}"
            )

    @staticmethod
    def calculate_tva(total_with_tva_ron: Decimal) -> tuple:
        """
        Calculate TVA (19%) breakdown.

        Args:
            total_with_tva_ron: Total amount including TVA (e.g., 49 RON)

        Returns:
            Tuple of (base_ron, tva_ron, total_ron)
            Example: (41.18, 7.82, 49.00) for 49 RON subscription
        """
        total = Decimal(str(total_with_tva_ron))
        base = total / Decimal('1.19')
        tva = total - base

        # Round to 2 decimals
        base = base.quantize(Decimal('0.01'))
        tva = tva.quantize(Decimal('0.01'))
        total = total.quantize(Decimal('0.01'))

        return (base, tva, total)

    @classmethod
    def create_invoice(
        cls,
        subscription: CraftsmanSubscription,
        stripe_invoice_id: str,
        payment_date: Optional[timezone.datetime] = None
    ) -> Dict:
        """
        Generate Smart Bill invoice for subscription payment.

        Args:
            subscription: CraftsmanSubscription instance
            stripe_invoice_id: Stripe invoice ID for reference
            payment_date: Payment date (defaults to now)

        Returns:
            Dict with invoice data from Smart Bill API

        Raises:
            MissingFiscalDataError: If fiscal data incomplete
            SmartBillAPIError: If API call fails
        """
        craftsman = subscription.craftsman

        # Validate fiscal data
        cls.validate_fiscal_data(craftsman)

        # Calculate TVA
        total_ron = Decimal(subscription.tier.price) / 100  # Convert cents to RON
        base_ron, tva_ron, _ = cls.calculate_tva(total_ron)

        # Build client data
        client_data = {
            'name': craftsman.company_name or craftsman.user.get_full_name() or craftsman.user.username,
            'address': f"{craftsman.fiscal_address_street}, {craftsman.fiscal_address_city}, {craftsman.fiscal_address_county}",
            'postalCode': craftsman.fiscal_address_postal_code,
            'email': craftsman.user.email,
        }

        # Add CUI or CNP based on fiscal type
        if craftsman.fiscal_type == 'PF':
            client_data['cnp'] = craftsman.cnp
            client_data['isTaxPayer'] = False
        else:  # PFA or SRL
            client_data['vatCode'] = craftsman.cui
            client_data['isTaxPayer'] = True

        # Build invoice data
        invoice_data = {
            'companyVatCode': settings.SMARTBILL_COMPANY_VAT_CODE,
            'client': client_data,
            'issueDate': (payment_date or timezone.now()).strftime('%Y-%m-%d'),
            'seriesName': settings.SMARTBILL_INVOICE_SERIES,  # e.g., "SUBS"
            'isDraft': False,
            'products': [
                {
                    'name': f'Abonament {subscription.tier.display_name} - Bricli.ro',
                    'code': f'SUBS-{subscription.tier.name.upper()}',
                    'isService': True,
                    'measuringUnit': 'buc',
                    'quantity': 1,
                    'price': float(base_ron),
                    'isTaxIncluded': False,
                    'taxPercentage': 19,
                    'taxName': 'TVA',
                }
            ],
            'payment': {
                'type': 'Card',
                'value': float(total_ron)
            },
            'mentions': f'Plată Stripe: {stripe_invoice_id}. Mulțumim pentru abonament!',
        }

        try:
            # Call Smart Bill API
            response = requests.post(
                f"{cls.API_BASE_URL}/invoice",
                json=invoice_data,
                headers=cls._get_auth_header(),
                timeout=30
            )

            if response.status_code == 200:
                invoice_json = response.json()

                # Log success
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    event_type='invoice_created',
                    old_tier=subscription.tier,
                    new_tier=subscription.tier,
                    metadata={
                        'stripe_invoice_id': stripe_invoice_id,
                        'smartbill_series': invoice_json.get('series'),
                        'smartbill_number': invoice_json.get('number'),
                        'total_ron': str(total_ron),
                        'base_ron': str(base_ron),
                        'tva_ron': str(tva_ron),
                    }
                )

                return invoice_json
            else:
                # Log failure for retry
                error_msg = response.text
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    event_type='invoice_pending',
                    old_tier=subscription.tier,
                    new_tier=subscription.tier,
                    metadata={
                        'stripe_invoice_id': stripe_invoice_id,
                        'error': error_msg,
                        'retry_count': 0,
                        'status_code': response.status_code,
                    }
                )

                raise SmartBillAPIError(
                    f"Smart Bill API error (status {response.status_code}): {error_msg}"
                )

        except requests.RequestException as e:
            # Network error - log for retry
            SubscriptionLog.objects.create(
                subscription=subscription,
                event_type='invoice_pending',
                old_tier=subscription.tier,
                new_tier=subscription.tier,
                metadata={
                    'stripe_invoice_id': stripe_invoice_id,
                    'error': str(e),
                    'retry_count': 0,
                }
            )

            raise SmartBillAPIError(f"Network error calling Smart Bill: {str(e)}")

    @classmethod
    def get_invoice_pdf(cls, series: str, number: str) -> bytes:
        """
        Download PDF of generated invoice.

        Args:
            series: Invoice series (e.g., "SUBS")
            number: Invoice number (e.g., "123")

        Returns:
            PDF file content as bytes

        Raises:
            SmartBillAPIError: If API call fails
        """
        try:
            response = requests.get(
                f"{cls.API_BASE_URL}/invoice/pdf",
                params={'cif': settings.SMARTBILL_COMPANY_VAT_CODE, 'seriesname': series, 'number': number},
                headers=cls._get_auth_header(),
                timeout=30
            )

            if response.status_code == 200:
                return response.content
            else:
                raise SmartBillAPIError(
                    f"Failed to download PDF (status {response.status_code}): {response.text}"
                )

        except requests.RequestException as e:
            raise SmartBillAPIError(f"Network error downloading PDF: {str(e)}")

    @classmethod
    def retry_failed_invoice(cls, subscription_log: SubscriptionLog) -> Dict:
        """
        Retry invoice generation for a failed attempt.

        Args:
            subscription_log: SubscriptionLog with event_type='invoice_pending'

        Returns:
            Dict with invoice data from Smart Bill API

        Raises:
            SmartBillAPIError: If retry fails
        """
        metadata = subscription_log.metadata
        retry_count = metadata.get('retry_count', 0)

        # Update retry count
        metadata['retry_count'] = retry_count + 1
        subscription_log.metadata = metadata
        subscription_log.save()

        # Attempt invoice creation
        return cls.create_invoice(
            subscription=subscription_log.subscription,
            stripe_invoice_id=metadata['stripe_invoice_id']
        )
