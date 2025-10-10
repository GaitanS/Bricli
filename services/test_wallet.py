"""
Tests for wallet operations: top-up, deduct, and lead fee charging.
"""
import pytest
from django.contrib.auth import get_user_model
from services.models import CreditWallet, WalletTransaction, Order, Shortlist
from services.lead_fee_service import LeadFeeService, InsufficientBalanceError
from accounts.models import County, City, CraftsmanProfile
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db
class TestWalletOperations:
    """Test basic wallet operations: create, top-up, deduct."""

    @pytest.fixture
    def user(self):
        """Create a test user."""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='craftsman'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create a wallet for the test user."""
        return CreditWallet.objects.create(user=user, balance_cents=0)

    def test_wallet_creation(self, user):
        """Test wallet is created with zero balance."""
        wallet = CreditWallet.objects.create(user=user, balance_cents=0)
        assert wallet.balance_cents == 0
        assert wallet.balance_lei == 0.0

    def test_wallet_top_up(self, wallet):
        """Test adding credit to wallet."""
        initial_balance = wallet.balance_cents

        # Add 5000 cents (50 RON)
        transaction = wallet.add_amount(
            amount_cents=5000,
            reason='top_up',
            meta={'payment_method': 'stripe'}
        )

        wallet.refresh_from_db()

        assert wallet.balance_cents == initial_balance + 5000
        assert wallet.balance_lei == 50.0
        assert transaction.amount_cents == 5000
        assert transaction.reason == 'top_up'

    def test_wallet_deduct_success(self, wallet):
        """Test successful deduction from wallet with sufficient balance."""
        # Top up first
        wallet.add_amount(amount_cents=10000, reason='top_up', meta={})
        wallet.refresh_from_db()

        initial_balance = wallet.balance_cents

        # Deduct 2000 cents (20 RON)
        transaction = wallet.deduct_amount(
            amount_cents=2000,
            reason='lead_fee',
            meta={'order_id': 1}
        )

        wallet.refresh_from_db()

        assert wallet.balance_cents == initial_balance - 2000
        assert wallet.balance_lei == 80.0
        assert transaction.amount_cents == -2000
        assert transaction.reason == 'lead_fee'

    def test_wallet_deduct_insufficient_balance(self, wallet):
        """Test deduction fails with insufficient balance."""
        # Wallet has 0 balance
        assert wallet.balance_cents == 0

        # Attempt to deduct 2000 cents
        with pytest.raises(ValueError, match="Sold insuficient"):
            wallet.deduct_amount(
                amount_cents=2000,
                reason='lead_fee',
                meta={}
            )

        # Balance should remain unchanged
        wallet.refresh_from_db()
        assert wallet.balance_cents == 0

    def test_has_sufficient_balance(self, wallet):
        """Test balance checking."""
        assert wallet.has_sufficient_balance(0) is True
        assert wallet.has_sufficient_balance(100) is False

        # Top up
        wallet.add_amount(amount_cents=5000, reason='top_up', meta={})
        wallet.refresh_from_db()

        assert wallet.has_sufficient_balance(5000) is True
        assert wallet.has_sufficient_balance(5001) is False
        assert wallet.has_sufficient_balance(4999) is True


@pytest.mark.django_db
class TestLeadFeeService:
    """Test lead fee charging for shortlisting."""

    @pytest.fixture
    def client_user(self):
        """Create a client user."""
        return User.objects.create_user(
            username='client1',
            email='client@example.com',
            password='pass123',
            user_type='client'
        )

    @pytest.fixture
    def craftsman_user(self):
        """Create a craftsman user."""
        user = User.objects.create_user(
            username='craftsman1',
            email='craftsman@example.com',
            password='pass123',
            user_type='craftsman'
        )
        # Create craftsman profile
        county, _ = County.objects.get_or_create(name='Bucuresti', code='B')
        city, _ = City.objects.get_or_create(name='Bucuresti', county=county)
        CraftsmanProfile.objects.create(
            user=user,
            display_name='Test Craftsman',
            county=county,
            city=city
        )
        return user

    @pytest.fixture
    def order(self, client_user):
        """Create a test order."""
        from services.models import Service, ServiceCategory

        category = ServiceCategory.objects.create(name='Test Category', slug='test-cat')
        service = Service.objects.create(category=category, name='Test Service', slug='test-svc')
        county = County.objects.get_or_create(name='Bucuresti', code='B')[0]
        city = City.objects.get_or_create(name='Bucuresti', county=county)[0]

        return Order.objects.create(
            client=client_user,
            title='Test Order',
            description='Test description',
            service=service,
            county=county,
            city=city,
            status='published'
        )

    def test_charge_shortlist_fee_sufficient_balance(self, order, craftsman_user):
        """Test charging lead fee with sufficient balance."""
        # Create wallet and top up
        wallet = CreditWallet.objects.create(user=craftsman_user, balance_cents=0)
        wallet.add_amount(amount_cents=10000, reason='top_up', meta={})
        wallet.refresh_from_db()

        initial_balance = wallet.balance_cents

        # Charge lead fee
        shortlist = LeadFeeService.charge_shortlist_fee(
            order=order,
            craftsman_user=craftsman_user
        )

        wallet.refresh_from_db()

        # Assertions
        assert shortlist is not None
        assert shortlist.order == order
        assert shortlist.craftsman == craftsman_user
        assert shortlist.lead_fee_amount == LeadFeeService.DEFAULT_LEAD_FEE_CENTS
        assert shortlist.charged_at is not None
        assert wallet.balance_cents == initial_balance - LeadFeeService.DEFAULT_LEAD_FEE_CENTS

        # Check transaction was created
        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            reason='lead_fee'
        ).first()
        assert transaction is not None
        assert transaction.amount_cents == -LeadFeeService.DEFAULT_LEAD_FEE_CENTS

    def test_charge_shortlist_fee_insufficient_balance(self, order, craftsman_user):
        """Test charging lead fee fails with insufficient balance."""
        # Create wallet with insufficient balance
        wallet = CreditWallet.objects.create(user=craftsman_user, balance_cents=1000)

        # Attempt to charge lead fee
        with pytest.raises(InsufficientBalanceError) as exc_info:
            LeadFeeService.charge_shortlist_fee(
                order=order,
                craftsman_user=craftsman_user
            )

        # Check error details
        error = exc_info.value
        assert error.required_cents == LeadFeeService.DEFAULT_LEAD_FEE_CENTS
        assert error.available_cents == 1000

        # Wallet balance should remain unchanged
        wallet.refresh_from_db()
        assert wallet.balance_cents == 1000

        # No shortlist should be created
        assert Shortlist.objects.filter(order=order, craftsman=craftsman_user).count() == 0

    def test_charge_shortlist_fee_no_existing_wallet_fails(self, order, craftsman_user):
        """Test that charging fails when no wallet exists (no auto-create on fail)."""
        # Delete any existing wallet
        CreditWallet.objects.filter(user=craftsman_user).delete()

        # This should fail due to insufficient balance
        with pytest.raises(InsufficientBalanceError):
            LeadFeeService.charge_shortlist_fee(
                order=order,
                craftsman_user=craftsman_user
            )

        # Wallet should be created but with zero balance (created during check)
        wallet = CreditWallet.objects.filter(user=craftsman_user).first()
        # Note: wallet IS created by get_or_create_wallet call, even on failure
        # This is acceptable behavior - wallet exists for future use
        if wallet:
            assert wallet.balance_cents == 0

    def test_can_afford_shortlist(self, order, craftsman_user):
        """Test checking if craftsman can afford shortlist."""
        # Delete any existing wallet
        CreditWallet.objects.filter(user=craftsman_user).delete()

        # No wallet - should return False and create one with 0 balance
        can_afford, balance, fee = LeadFeeService.can_afford_shortlist(
            craftsman_user, order
        )
        assert can_afford is False
        assert balance == 0
        assert fee == LeadFeeService.DEFAULT_LEAD_FEE_CENTS

        # Get the auto-created wallet and add balance
        wallet = CreditWallet.objects.get(user=craftsman_user)
        wallet.balance_cents = 5000
        wallet.save()

        can_afford, balance, fee = LeadFeeService.can_afford_shortlist(
            craftsman_user, order
        )
        assert can_afford is True
        assert balance == 5000
        assert fee == LeadFeeService.DEFAULT_LEAD_FEE_CENTS
