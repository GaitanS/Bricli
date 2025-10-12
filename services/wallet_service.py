"""
Wallet Service Layer
Provides safe operations for wallet management with atomic transactions
"""

from django.db import transaction
from django.db.models import F

from .models import CreditWallet


def get_or_create_wallet(user):
    """
    Safely get or create wallet for user.

    Args:
        user: User instance

    Returns:
        CreditWallet instance
    """
    wallet, created = CreditWallet.objects.get_or_create(user=user)
    return wallet


@transaction.atomic
def top_up(user, amount_cents, reason="top_up", meta=None):
    """
    Add credits to wallet atomically.

    Args:
        user: User instance
        amount_cents: Amount in cents (positive integer)
        reason: Transaction reason
        meta: Optional metadata dict

    Returns:
        CreditWallet instance (refreshed)
    """
    wallet = get_or_create_wallet(user)

    # Use F() expression for atomic update
    CreditWallet.objects.filter(pk=wallet.pk).update(
        balance_cents=F("balance_cents") + amount_cents
    )

    # Refresh from DB
    wallet.refresh_from_db()

    # Create transaction record
    wallet.add_amount(amount_cents, reason=reason, meta=meta or {})

    return wallet


@transaction.atomic
def deduct(user, amount_cents, reason="deduction", meta=None):
    """
    Deduct credits from wallet atomically.

    Args:
        user: User instance
        amount_cents: Amount in cents (positive integer will be deducted)
        reason: Transaction reason
        meta: Optional metadata dict

    Returns:
        CreditWallet instance (refreshed)

    Raises:
        ValueError: If insufficient balance
    """
    wallet = get_or_create_wallet(user)

    # Check balance
    if wallet.balance_cents < amount_cents:
        raise ValueError(f"Insufficient balance. Required: {amount_cents}, Available: {wallet.balance_cents}")

    # Use F() expression for atomic update
    CreditWallet.objects.filter(pk=wallet.pk).update(
        balance_cents=F("balance_cents") - amount_cents
    )

    # Refresh from DB
    wallet.refresh_from_db()

    # Create transaction record (negative amount)
    wallet.add_amount(-amount_cents, reason=reason, meta=meta or {})

    return wallet


def get_balance_lei(user):
    """
    Get wallet balance in RON.

    Args:
        user: User instance

    Returns:
        float: Balance in RON
    """
    wallet = get_or_create_wallet(user)
    return wallet.balance_lei
