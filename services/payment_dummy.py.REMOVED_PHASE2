"""
Dummy Payment Provider for Local Development

This module provides a mock payment provider that simulates Stripe functionality
without requiring actual Stripe API keys. Useful for local development and testing.

Usage:
    When STRIPE_SECRET_KEY is missing or is a placeholder, payment_views.py
    automatically switches to DummyPaymentProvider.
"""

import logging
import secrets
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class DummyPaymentIntent:
    """
    Simulates a Stripe PaymentIntent object.

    Attributes:
        id: Unique payment intent ID (dummy_pi_xxx)
        client_secret: Client secret for frontend (dummy_secret_xxx)
        amount: Amount in cents
        currency: Currency code (default: ron)
        status: Payment status (requires_payment_method, succeeded, failed)
        metadata: Additional data attached to the payment
    """

    def __init__(
        self, amount: int, currency: str = "ron", customer: str | None = None, metadata: dict[str, Any] | None = None
    ):
        self.id = f"dummy_pi_{secrets.token_urlsafe(16)}"
        self.client_secret = f"dummy_secret_{secrets.token_urlsafe(24)}"
        self.amount = amount
        self.currency = currency
        self.customer = customer or f"dummy_cus_{secrets.token_urlsafe(8)}"
        self.status = "requires_payment_method"
        self.metadata = metadata or {}
        self.payment_method_types = ["card"]
        self.created = int(datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (Stripe API response format)"""
        return {
            "id": self.id,
            "client_secret": self.client_secret,
            "amount": self.amount,
            "currency": self.currency,
            "customer": self.customer,
            "status": self.status,
            "metadata": self.metadata,
            "payment_method_types": self.payment_method_types,
            "created": self.created,
        }


class DummyPaymentProvider:
    """
    Mock payment provider that simulates Stripe API.

    Features:
    - Simulates successful payments (90% success rate by default)
    - Generates realistic payment intent IDs
    - Logs all transactions for debugging
    - No external API calls, fully local

    Example:
        provider = DummyPaymentProvider()
        intent = provider.create_payment_intent(
            amount=5000,
            currency='ron',
            metadata={'user_id': 123}
        )
    """

    def __init__(self, success_rate: float = 0.95):
        """
        Initialize dummy payment provider.

        Args:
            success_rate: Probability of successful payment (0.0 to 1.0)
                         Default 0.95 means 95% of payments succeed
        """
        self.success_rate = success_rate
        self._intents: dict[str, DummyPaymentIntent] = {}
        logger.info("🔧 DummyPaymentProvider initialized (local dev mode)")

    def create_payment_intent(
        self,
        amount: int,
        currency: str = "ron",
        customer: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> DummyPaymentIntent:
        """
        Create a mock payment intent.

        Args:
            amount: Amount in cents (e.g., 5000 = 50 RON)
            currency: Currency code (default: ron)
            customer: Customer ID (generated if None)
            metadata: Additional data
            **kwargs: Other Stripe parameters (ignored)

        Returns:
            DummyPaymentIntent object
        """
        intent = DummyPaymentIntent(amount=amount, currency=currency, customer=customer, metadata=metadata)

        self._intents[intent.id] = intent

        logger.info(
            f"💳 Dummy Payment Intent Created: {intent.id} | "
            f"Amount: {amount/100:.2f} {currency.upper()} | "
            f"Metadata: {metadata}"
        )

        return intent

    def retrieve_payment_intent(self, payment_intent_id: str) -> DummyPaymentIntent:
        """
        Retrieve a payment intent by ID.

        Args:
            payment_intent_id: Intent ID to retrieve

        Returns:
            DummyPaymentIntent object

        Raises:
            ValueError: If payment intent not found
        """
        if payment_intent_id not in self._intents:
            # Auto-succeed for testing
            logger.warning(f"⚠️ Payment intent {payment_intent_id} not found, auto-creating as succeeded")
            intent = DummyPaymentIntent(amount=5000, currency="ron")
            intent.id = payment_intent_id
            intent.status = "succeeded"
            self._intents[payment_intent_id] = intent

        return self._intents[payment_intent_id]

    def confirm_payment_intent(self, payment_intent_id: str) -> DummyPaymentIntent:
        """
        Confirm (process) a payment intent.

        Args:
            payment_intent_id: Intent ID to confirm

        Returns:
            DummyPaymentIntent with updated status
        """
        intent = self.retrieve_payment_intent(payment_intent_id)

        # Simulate payment processing
        import random

        if random.random() < self.success_rate:
            intent.status = "succeeded"
            logger.info(f"✅ Payment Succeeded: {payment_intent_id}")
        else:
            intent.status = "failed"
            logger.warning(f"❌ Payment Failed: {payment_intent_id}")

        return intent

    @staticmethod
    def is_active() -> bool:
        """Check if dummy provider is active (for conditional UI)"""
        return True


# Singleton instance
_dummy_provider = DummyPaymentProvider()


def get_dummy_provider() -> DummyPaymentProvider:
    """Get the global dummy provider instance"""
    return _dummy_provider


def is_dummy_mode() -> bool:
    """
    Check if application is in dummy payment mode.

    Returns:
        True if using dummy payments, False if using real Stripe
    """
    from django.conf import settings

    stripe_key = getattr(settings, "STRIPE_SECRET_KEY", "")

    # Consider it dummy mode if:
    # 1. Key is empty or None
    # 2. Key contains placeholder text
    # 3. Key is the default test key from settings
    is_dummy = (
        not stripe_key
        or "your-" in stripe_key.lower()
        or "test_51234567890abcdef" in stripe_key
        or "placeholder" in stripe_key.lower()
    )

    if is_dummy:
        logger.info("🔧 Dummy payment mode active (Stripe keys not configured)")

    return is_dummy
