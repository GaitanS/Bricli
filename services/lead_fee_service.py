"""
Lead Fee Service - Handles automatic wallet deduction for shortlist/contact reveal.

This service manages the business logic for charging craftsmen when clients
add them to shortlists or reveal their contact information.
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class InsufficientBalanceError(Exception):
    """Raised when wallet balance is insufficient for lead fee."""
    def __init__(self, required_cents, available_cents):
        self.required_cents = required_cents
        self.available_cents = available_cents
        super().__init__(
            f"Sold insuficient: necesar {required_cents/100:.2f} RON, "
            f"disponibil {available_cents/100:.2f} RON"
        )


class LeadFeeService:
    """
    Service for managing lead fees and wallet deductions.

    Business Rules:
    - Default lead fee: 2000 cents (20 RON)
    - Fee charged when craftsman is added to shortlist
    - Wallet balance must be sufficient before deduction
    - All operations are atomic (database transactions)
    """

    DEFAULT_LEAD_FEE_CENTS = 2000  # 20 RON

    @classmethod
    def get_lead_fee_amount(cls, order=None, craftsman=None):
        """
        Get the lead fee amount for a given order/craftsman.

        Args:
            order: Order instance (optional, for future dynamic pricing)
            craftsman: CraftsmanProfile instance (optional, for future dynamic pricing)

        Returns:
            int: Lead fee amount in cents
        """
        # Future enhancement: dynamic pricing based on order category, location, etc.
        return cls.DEFAULT_LEAD_FEE_CENTS

    @classmethod
    def get_or_create_wallet(cls, user):
        """
        Get or create wallet for user.

        Args:
            user: User instance

        Returns:
            CreditWallet: User's wallet
        """
        from .models import CreditWallet

        wallet, created = CreditWallet.objects.get_or_create(
            user=user,
            defaults={'balance_cents': 0}
        )

        if created:
            logger.info(f"Created new wallet for user {user.id}")

        return wallet

    @classmethod
    @transaction.atomic
    def charge_shortlist_fee(cls, order, craftsman_user):
        """
        Charge lead fee when craftsman is added to shortlist.

        This is the main entry point for charging lead fees. It:
        1. Gets/creates the craftsman's wallet
        2. Calculates the lead fee
        3. Checks if balance is sufficient
        4. Deducts the fee from wallet
        5. Creates/updates the Shortlist record
        6. Records the transaction

        Args:
            order: Order instance
            craftsman_user: User instance (must have user_type='craftsman')

        Returns:
            Shortlist: The created/updated shortlist entry

        Raises:
            InsufficientBalanceError: If wallet balance < lead fee
            ValueError: If user is not a craftsman
        """
        from .models import Shortlist

        # Validation
        if craftsman_user.user_type != 'craftsman':
            raise ValueError(f"User {craftsman_user.id} is not a craftsman")

        # Get wallet
        wallet = cls.get_or_create_wallet(craftsman_user)

        # Calculate fee
        lead_fee = cls.get_lead_fee_amount(order=order, craftsman=craftsman_user)

        # Check balance
        if not wallet.has_sufficient_balance(lead_fee):
            logger.warning(
                f"Insufficient balance for user {craftsman_user.id}: "
                f"required {lead_fee}, available {wallet.balance_cents}"
            )
            raise InsufficientBalanceError(lead_fee, wallet.balance_cents)

        # Deduct from wallet
        wallet.deduct_amount(
            amount_cents=lead_fee,
            reason='lead_fee',
            meta={
                'order_id': order.id,
                'order_title': order.title,
                'client_id': order.client.id,
            }
        )

        logger.info(
            f"Deducted {lead_fee} cents from wallet {wallet.id} "
            f"for order {order.id}"
        )

        # Create/update shortlist entry
        shortlist, created = Shortlist.objects.get_or_create(
            order=order,
            craftsman=craftsman_user,
            defaults={
                'lead_fee_amount': lead_fee,
                'charged_at': timezone.now(),
            }
        )

        if not created:
            # Update existing shortlist
            shortlist.lead_fee_amount = lead_fee
            shortlist.charged_at = timezone.now()
            shortlist.save(update_fields=['lead_fee_amount', 'charged_at'])
            logger.info(f"Updated existing shortlist {shortlist.id}")
        else:
            logger.info(f"Created new shortlist {shortlist.id}")

        return shortlist

    @classmethod
    def can_afford_shortlist(cls, craftsman_user, order=None):
        """
        Check if craftsman can afford to be shortlisted.

        Args:
            craftsman_user: User instance
            order: Order instance (optional)

        Returns:
            tuple: (can_afford: bool, balance_cents: int, fee_cents: int)
        """
        try:
            wallet = cls.get_or_create_wallet(craftsman_user)
            fee = cls.get_lead_fee_amount(order=order, craftsman=craftsman_user)
            can_afford = wallet.has_sufficient_balance(fee)

            return (can_afford, wallet.balance_cents, fee)
        except Exception as e:
            logger.error(f"Error checking affordability: {e}")
            return (False, 0, cls.DEFAULT_LEAD_FEE_CENTS)

    @classmethod
    def get_shortlist_status(cls, order, craftsman_user):
        """
        Get shortlist status for craftsman and order.

        Args:
            order: Order instance
            craftsman_user: User instance

        Returns:
            dict: Status information including:
                - is_shortlisted: bool
                - charged_at: datetime or None
                - fee_amount: int (cents)
                - can_afford: bool
        """
        from .models import Shortlist

        try:
            shortlist = Shortlist.objects.get(order=order, craftsman=craftsman_user)
            is_shortlisted = True
            charged_at = shortlist.charged_at
            fee_amount = shortlist.lead_fee_amount
        except Shortlist.DoesNotExist:
            is_shortlisted = False
            charged_at = None
            fee_amount = cls.get_lead_fee_amount(order=order, craftsman=craftsman_user)

        can_afford, balance, _ = cls.can_afford_shortlist(craftsman_user, order)

        return {
            'is_shortlisted': is_shortlisted,
            'charged_at': charged_at,
            'fee_amount': fee_amount,
            'fee_lei': fee_amount / 100,
            'can_afford': can_afford,
            'wallet_balance_cents': balance,
            'wallet_balance_lei': balance / 100,
        }
