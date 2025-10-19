"""
Phase 3: Business Logic & Services Tests

Tests for SubscriptionService, LeadQuotaService, and related functionality.
"""

import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import CraftsmanProfile
from subscriptions.models import SubscriptionTier, CraftsmanSubscription, SubscriptionLog
from subscriptions.services import (
    SubscriptionService,
    SubscriptionError,
    MissingFiscalDataError,
    RefundNotAllowedError,
)
from services.lead_quota_service import LeadQuotaService, InsufficientQuotaError
from services.models import Order, ServiceCategory

User = get_user_model()


@pytest.fixture
def craftsman_user(db):
    """Create a craftsman user with profile."""
    from accounts.models import County, City

    user = User.objects.create_user(
        username='testcraftsman',
        email='craftsman@test.com',
        password='testpass123',
        user_type='craftsman',
        first_name='Test',
        last_name='Craftsman',
    )

    # Get or create county and city
    county, _ = County.objects.get_or_create(name='București')
    city, _ = City.objects.get_or_create(name='București', county=county)

    profile = CraftsmanProfile.objects.create(
        user=user,
        display_name='Test Craftsman',
        slug='test-craftsman',
        county=county,
        city=city,
        coverage_radius_km=25,
        # Fiscal data
        fiscal_type='PF',
        cnp='1234567890123',
        fiscal_address_street='Str. Test 123',
        fiscal_address_city='București',
        fiscal_address_county='București',
        fiscal_address_postal_code='012345',
        phone='+40712345678',
    )

    return user


@pytest.fixture
def free_tier(db):
    """Get free tier."""
    return SubscriptionTier.objects.get(name='free')


@pytest.fixture
def plus_tier(db):
    """Get plus tier."""
    return SubscriptionTier.objects.get(name='plus')


@pytest.fixture
def pro_tier(db):
    """Get pro tier."""
    return SubscriptionTier.objects.get(name='pro')


@pytest.fixture
def test_order(db):
    """Create a test order."""
    category = ServiceCategory.objects.create(name='Test Category', icon='fa-wrench')
    client = User.objects.create_user(
        username='testclient',
        email='client@test.com',
        password='testpass123',
        user_type='client',
    )

    order = Order.objects.create(
        client=client,
        service=category,
        title='Test Order',
        description='Test description',
        budget_max=1000,
    )

    return order


@pytest.mark.django_db
class TestSubscriptionServiceValidation:
    """Tests for subscription service validation."""

    def test_validate_fiscal_data_complete(self, craftsman_user):
        """Test validation passes with complete fiscal data."""
        profile = craftsman_user.craftsmanprofile

        # Should not raise exception
        SubscriptionService.validate_fiscal_data(profile)

    def test_validate_fiscal_data_missing_address(self, craftsman_user):
        """Test validation fails with missing address."""
        profile = craftsman_user.craftsmanprofile
        profile.fiscal_address_street = None
        profile.save()

        with pytest.raises(MissingFiscalDataError) as exc_info:
            SubscriptionService.validate_fiscal_data(profile)

        assert 'fiscal_address_street' in str(exc_info.value)

    def test_validate_fiscal_data_pf_missing_cnp(self, craftsman_user):
        """Test validation fails for PF without CNP."""
        profile = craftsman_user.craftsmanprofile
        profile.fiscal_type = 'PF'
        profile.cnp = None
        profile.save()

        with pytest.raises(MissingFiscalDataError) as exc_info:
            SubscriptionService.validate_fiscal_data(profile)

        assert 'cnp' in str(exc_info.value)

    def test_validate_fiscal_data_pfa_missing_cui(self, craftsman_user):
        """Test validation fails for PFA without CUI."""
        profile = craftsman_user.craftsmanprofile
        profile.fiscal_type = 'PFA'
        profile.cui = None
        profile.company_name = 'Test Company'
        profile.save()

        with pytest.raises(MissingFiscalDataError) as exc_info:
            SubscriptionService.validate_fiscal_data(profile)

        assert 'cui' in str(exc_info.value)


@pytest.mark.django_db
class TestSubscriptionServiceUpgrade:
    """Tests for subscription upgrade functionality."""

    @patch('stripe.Customer.create')
    @patch('stripe.PaymentMethod.attach')
    @patch('stripe.Customer.modify')
    @patch('stripe.Subscription.create')
    def test_upgrade_to_plus_creates_stripe_customer(
        self,
        mock_sub_create,
        mock_customer_modify,
        mock_pm_attach,
        mock_customer_create,
        craftsman_user,
        plus_tier,
    ):
        """Test upgrading creates Stripe customer if not exists."""
        # Mock Stripe responses
        mock_customer_create.return_value = MagicMock(id='cus_test123')
        mock_sub_create.return_value = MagicMock(
            id='sub_test123',
            current_period_start=int(timezone.now().timestamp()),
            current_period_end=int((timezone.now() + timedelta(days=30)).timestamp()),
        )

        # Set Stripe price ID for plus tier
        plus_tier.stripe_price_id = 'price_test_plus'
        plus_tier.save()

        # Get craftsman profile
        profile = craftsman_user.craftsmanprofile

        # Upgrade
        subscription = SubscriptionService.upgrade_to_paid(
            profile,
            'plus',
            'pm_test_card',
            waive_withdrawal=False,
        )

        # Verify Stripe customer was created
        mock_customer_create.assert_called_once()
        assert subscription.stripe_customer_id == 'cus_test123'
        assert subscription.stripe_subscription_id == 'sub_test123'
        assert subscription.tier == plus_tier
        assert subscription.status == 'active'

    @patch('stripe.PaymentMethod.attach')
    @patch('stripe.Customer.modify')
    @patch('stripe.Subscription.create')
    def test_upgrade_sets_withdrawal_deadline(
        self,
        mock_sub_create,
        mock_customer_modify,
        mock_pm_attach,
        craftsman_user,
        plus_tier,
    ):
        """Test upgrade sets 14-day withdrawal deadline."""
        mock_sub_create.return_value = MagicMock(
            id='sub_test123',
            current_period_start=int(timezone.now().timestamp()),
            current_period_end=int((timezone.now() + timedelta(days=30)).timestamp()),
        )

        plus_tier.stripe_price_id = 'price_test_plus'
        plus_tier.save()

        profile = craftsman_user.craftsmanprofile

        # Set existing customer ID to skip customer creation
        subscription = CraftsmanSubscription.objects.get(craftsman=profile)
        subscription.stripe_customer_id = 'cus_existing'
        subscription.save()

        # Upgrade without waiving withdrawal
        subscription = SubscriptionService.upgrade_to_paid(
            profile,
            'plus',
            'pm_test_card',
            waive_withdrawal=False,
        )

        # Check withdrawal deadline is ~14 days from now
        assert subscription.withdrawal_deadline is not None
        assert subscription.withdrawal_right_waived is False

        deadline_days = (subscription.withdrawal_deadline - timezone.now()).days
        assert 13 <= deadline_days <= 14

    def test_upgrade_with_waived_withdrawal(self, craftsman_user, plus_tier):
        """Test upgrade with waived withdrawal right."""
        with patch.multiple(
            'stripe',
            PaymentMethod=MagicMock(),
            Customer=MagicMock(),
            Subscription=MagicMock(
                create=MagicMock(
                    return_value=MagicMock(
                        id='sub_test123',
                        current_period_start=int(timezone.now().timestamp()),
                        current_period_end=int((timezone.now() + timedelta(days=30)).timestamp()),
                    )
                )
            ),
        ):
            plus_tier.stripe_price_id = 'price_test_plus'
            plus_tier.save()

            profile = craftsman_user.craftsmanprofile

            # Set existing customer ID
            subscription = CraftsmanSubscription.objects.get(craftsman=profile)
            subscription.stripe_customer_id = 'cus_existing'
            subscription.save()

            # Upgrade with waived withdrawal
            subscription = SubscriptionService.upgrade_to_paid(
                profile,
                'plus',
                'pm_test_card',
                waive_withdrawal=True,
            )

            assert subscription.withdrawal_right_waived is True
            assert subscription.withdrawal_deadline is None


@pytest.mark.django_db
class TestSubscriptionServiceCancellation:
    """Tests for subscription cancellation."""

    @patch('stripe.Subscription.delete')
    def test_cancel_subscription_immediate(self, mock_delete, craftsman_user, free_tier):
        """Test immediate subscription cancellation."""
        profile = craftsman_user.craftsmanprofile
        subscription = CraftsmanSubscription.objects.get(craftsman=profile)

        # Set up paid subscription
        subscription.stripe_subscription_id = 'sub_test123'
        subscription.tier = SubscriptionTier.objects.get(name='plus')
        subscription.status = 'active'
        subscription.save()

        # Cancel immediately
        subscription = SubscriptionService.cancel_subscription(profile, immediate=True)

        # Verify
        mock_delete.assert_called_once_with('sub_test123')
        assert subscription.tier == free_tier
        assert subscription.status == 'canceled'
        assert subscription.stripe_subscription_id is None

    @patch('stripe.Subscription.modify')
    def test_cancel_subscription_at_period_end(self, mock_modify, craftsman_user):
        """Test cancellation at period end."""
        profile = craftsman_user.craftsmanprofile
        subscription = CraftsmanSubscription.objects.get(craftsman=profile)

        # Set up paid subscription
        subscription.stripe_subscription_id = 'sub_test123'
        subscription.tier = SubscriptionTier.objects.get(name='plus')
        subscription.status = 'active'
        subscription.save()

        # Cancel at period end
        subscription = SubscriptionService.cancel_subscription(profile, immediate=False)

        # Verify
        mock_modify.assert_called_once_with(
            'sub_test123',
            cancel_at_period_end=True,
        )
        assert subscription.status == 'canceled'


@pytest.mark.django_db
class TestSubscriptionServiceRefund:
    """Tests for refund functionality."""

    @patch('stripe.Invoice.list')
    @patch('stripe.Refund.create')
    @patch('stripe.Subscription.delete')
    def test_request_refund_within_window(
        self,
        mock_sub_delete,
        mock_refund_create,
        mock_invoice_list,
        craftsman_user,
        plus_tier,
    ):
        """Test successful refund within 14-day window."""
        # Setup mocks
        mock_invoice_list.return_value = MagicMock(
            data=[MagicMock(charge='ch_test123')]
        )
        mock_refund_create.return_value = MagicMock(
            id='re_test123',
            amount=4900,
            status='succeeded',
        )

        profile = craftsman_user.craftsmanprofile
        subscription = CraftsmanSubscription.objects.get(craftsman=profile)

        # Set up paid subscription within refund window
        subscription.tier = plus_tier
        subscription.stripe_customer_id = 'cus_test123'
        subscription.stripe_subscription_id = 'sub_test123'
        subscription.withdrawal_deadline = timezone.now() + timedelta(days=10)
        subscription.withdrawal_right_waived = False
        subscription.save()

        # Request refund
        refund = SubscriptionService.request_refund(profile)

        # Verify
        assert refund['refund_id'] == 're_test123'
        assert refund['amount_ron'] == 49.0
        assert refund['status'] == 'succeeded'

        # Verify subscription downgraded
        subscription.refresh_from_db()
        assert subscription.tier.name == 'free'
        assert subscription.status == 'refunded'

    def test_request_refund_outside_window(self, craftsman_user, plus_tier):
        """Test refund rejection outside 14-day window."""
        profile = craftsman_user.craftsmanprofile
        subscription = CraftsmanSubscription.objects.get(craftsman=profile)

        # Set up paid subscription outside refund window
        subscription.tier = plus_tier
        subscription.stripe_customer_id = 'cus_test123'
        subscription.stripe_subscription_id = 'sub_test123'
        subscription.withdrawal_deadline = timezone.now() - timedelta(days=1)  # Expired
        subscription.withdrawal_right_waived = False
        subscription.save()

        # Request refund should fail
        with pytest.raises(RefundNotAllowedError):
            SubscriptionService.request_refund(profile)

    def test_request_refund_with_waived_right(self, craftsman_user, plus_tier):
        """Test refund rejection when withdrawal right was waived."""
        profile = craftsman_user.craftsmanprofile
        subscription = CraftsmanSubscription.objects.get(craftsman=profile)

        # Set up paid subscription with waived withdrawal
        subscription.tier = plus_tier
        subscription.stripe_customer_id = 'cus_test123'
        subscription.stripe_subscription_id = 'sub_test123'
        subscription.withdrawal_right_waived = True
        subscription.withdrawal_deadline = None
        subscription.save()

        # Request refund should fail
        with pytest.raises(RefundNotAllowedError):
            SubscriptionService.request_refund(profile)


@pytest.mark.django_db
class TestLeadQuotaService:
    """Tests for lead quota management."""

    def test_can_receive_lead_free_tier_under_limit(self, craftsman_user):
        """Test free tier can receive lead when under limit."""
        subscription = CraftsmanSubscription.objects.get(craftsman__user=craftsman_user)
        subscription.leads_used_this_month = 3
        subscription.save()

        can_receive, error_msg = LeadQuotaService.can_receive_lead(craftsman_user)

        assert can_receive is True
        assert error_msg is None

    def test_can_receive_lead_free_tier_at_limit(self, craftsman_user):
        """Test free tier blocked when at limit."""
        subscription = CraftsmanSubscription.objects.get(craftsman__user=craftsman_user)
        subscription.leads_used_this_month = 5
        subscription.save()

        can_receive, error_msg = LeadQuotaService.can_receive_lead(craftsman_user)

        assert can_receive is False
        assert 'limit reached' in error_msg.lower()

    def test_can_receive_lead_plus_tier_unlimited(self, craftsman_user, plus_tier):
        """Test plus tier has unlimited leads."""
        subscription = CraftsmanSubscription.objects.get(craftsman__user=craftsman_user)
        subscription.tier = plus_tier
        subscription.leads_used_this_month = 1000  # High number
        subscription.save()

        can_receive, error_msg = LeadQuotaService.can_receive_lead(craftsman_user)

        assert can_receive is True
        assert error_msg is None

    def test_can_receive_lead_grace_period_active(self, craftsman_user):
        """Test grace period allows access after payment failure."""
        subscription = CraftsmanSubscription.objects.get(craftsman__user=craftsman_user)
        subscription.status = 'past_due'
        subscription.grace_period_end = timezone.now() + timedelta(days=5)
        subscription.save()

        can_receive, error_msg = LeadQuotaService.can_receive_lead(craftsman_user)

        assert can_receive is True
        assert error_msg is None

    def test_can_receive_lead_grace_period_expired(self, craftsman_user):
        """Test access blocked after grace period expires."""
        subscription = CraftsmanSubscription.objects.get(craftsman__user=craftsman_user)
        subscription.status = 'past_due'
        subscription.grace_period_end = timezone.now() - timedelta(days=1)
        subscription.save()

        can_receive, error_msg = LeadQuotaService.can_receive_lead(craftsman_user)

        assert can_receive is False
        assert 'grace period expired' in error_msg.lower()

    def test_process_shortlist_increments_usage(self, craftsman_user, test_order):
        """Test shortlisting increments lead usage for free tier."""
        subscription = CraftsmanSubscription.objects.get(craftsman__user=craftsman_user)
        initial_usage = subscription.leads_used_this_month

        # Process shortlist
        shortlist = LeadQuotaService.process_shortlist(craftsman_user, test_order)

        # Verify
        assert shortlist is not None
        subscription.refresh_from_db()
        assert subscription.leads_used_this_month == initial_usage + 1

    def test_process_shortlist_blocks_at_limit(self, craftsman_user, test_order):
        """Test shortlisting blocked when limit reached."""
        subscription = CraftsmanSubscription.objects.get(craftsman__user=craftsman_user)
        subscription.leads_used_this_month = 5
        subscription.save()

        # Should raise error
        with pytest.raises(InsufficientQuotaError):
            LeadQuotaService.process_shortlist(craftsman_user, test_order)

    def test_get_quota_status_free_tier(self, craftsman_user):
        """Test quota status for free tier."""
        subscription = CraftsmanSubscription.objects.get(craftsman__user=craftsman_user)
        subscription.leads_used_this_month = 3
        subscription.save()

        status = LeadQuotaService.get_quota_status(craftsman_user)

        assert status['tier_name'] == 'free'
        assert status['leads_used'] == 3
        assert status['leads_limit'] == 5
        assert status['leads_remaining'] == 2
        assert status['can_receive'] is True


@pytest.mark.django_db
class TestSubscriptionSignals:
    """Tests for subscription signals."""

    @patch('stripe.Customer.modify')
    def test_sync_user_to_stripe_on_email_change(self, mock_modify, craftsman_user):
        """Test user email change syncs to Stripe."""
        subscription = CraftsmanSubscription.objects.get(craftsman__user=craftsman_user)
        subscription.stripe_customer_id = 'cus_test123'
        subscription.save()

        # Change user email
        craftsman_user.email = 'newemail@test.com'
        craftsman_user.save()

        # Verify Stripe customer was updated
        mock_modify.assert_called_once()
        call_args = mock_modify.call_args
        assert call_args[0][0] == 'cus_test123'
        assert call_args[1]['email'] == 'newemail@test.com'
