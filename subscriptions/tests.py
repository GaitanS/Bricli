"""
Tests for subscription models and business logic (Phase 1)

Coverage:
- SubscriptionTier model and methods
- CraftsmanSubscription model and business logic
- Fiscal validation (CUI, CNP, phone)
- Webhook idempotency
- Subscription logs audit trail
"""

import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from accounts.models import User, CraftsmanProfile, County, City
from subscriptions.models import (
    SubscriptionTier,
    CraftsmanSubscription,
    StripeWebhookEvent,
    SubscriptionLog,
)


@pytest.fixture
def free_tier():
    """Create Free tier"""
    return SubscriptionTier.objects.create(
        name='free',
        display_name='Plan Gratuit',
        price=0,
        monthly_lead_limit=5,
        max_portfolio_images=3,
        priority_in_search=0,
    )


@pytest.fixture
def plus_tier():
    """Create Plus tier"""
    return SubscriptionTier.objects.create(
        name='plus',
        display_name='Plan Plus',
        price=4900,
        monthly_lead_limit=None,  # Unlimited
        max_portfolio_images=10,
        profile_badge='Verificat',
        priority_in_search=1,
        can_attach_pdf=True,
    )


@pytest.fixture
def pro_tier():
    """Create Pro tier"""
    return SubscriptionTier.objects.create(
        name='pro',
        display_name='Plan Pro',
        price=14900,
        monthly_lead_limit=None,  # Unlimited
        max_portfolio_images=50,
        profile_badge='Top Pro',
        priority_in_search=2,
        show_in_featured=True,
        can_attach_pdf=True,
        analytics_access=True,
    )


@pytest.fixture
def craftsman_user(db):
    """Create a craftsman user"""
    user = User.objects.create_user(
        username='testcraftsman',
        email='craftsman@test.com',
        password='testpass123',
        first_name='Test',
        last_name='Craftsman',
        user_type='craftsman',
    )
    return user


@pytest.fixture
def county(db):
    """Create a test county"""
    county, _ = County.objects.get_or_create(name='Bucuresti', code='B')
    return county


@pytest.fixture
def city(db, county):
    """Create a test city"""
    city, _ = City.objects.get_or_create(name='Bucuresti', county=county)
    return city


@pytest.fixture
def craftsman_profile(craftsman_user):
    """Create a craftsman profile with valid fiscal data"""
    profile = CraftsmanProfile.objects.create(
        user=craftsman_user,
        years_experience=5,
        fiscal_type='PF',
        cnp='1234567890123',
        phone='+40712345678',
    )
    return profile


@pytest.mark.django_db
class TestSubscriptionTier:
    """Test SubscriptionTier model"""

    def test_tier_creation(self, free_tier):
        """Test tier can be created with all fields"""
        assert free_tier.name == 'free'
        assert free_tier.price == 0
        assert free_tier.monthly_lead_limit == 5

    def test_tier_price_conversion(self, plus_tier):
        """Test cents to RON conversion"""
        assert plus_tier.get_price_ron() == 49.0

    def test_tier_unlimited_leads(self, plus_tier):
        """Test unlimited tier has NULL monthly_lead_limit"""
        assert plus_tier.monthly_lead_limit is None

    def test_tier_feature_flags(self, pro_tier):
        """Test Pro tier has all premium features"""
        assert pro_tier.can_attach_pdf is True
        assert pro_tier.analytics_access is True
        assert pro_tier.show_in_featured is True
        assert pro_tier.priority_in_search == 2


@pytest.mark.django_db
class TestCraftsmanSubscription:
    """Test CraftsmanSubscription model and business logic"""

    def test_subscription_creation(self, craftsman_profile, free_tier):
        """Test subscription can be created"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=free_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        assert subscription.status == 'active'
        assert subscription.leads_used_this_month == 0

    def test_can_receive_lead_free_tier_under_limit(self, craftsman_profile, free_tier):
        """Test Free tier can receive leads when under limit"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=free_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            leads_used_this_month=3,  # Under 5-lead limit
        )
        assert subscription.can_receive_lead() is True

    def test_can_receive_lead_free_tier_at_limit(self, craftsman_profile, free_tier):
        """Test Free tier cannot receive leads at limit"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=free_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            leads_used_this_month=5,  # At 5-lead limit
        )
        assert subscription.can_receive_lead() is False

    def test_can_receive_lead_plus_tier_unlimited(self, craftsman_profile, plus_tier):
        """Test Plus tier can receive unlimited leads"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=plus_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            leads_used_this_month=999,  # Any number
        )
        assert subscription.can_receive_lead() is True

    def test_increment_lead_usage(self, craftsman_profile, free_tier):
        """Test lead usage counter increments correctly"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=free_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        assert subscription.leads_used_this_month == 0
        subscription.increment_lead_usage()
        subscription.refresh_from_db()
        assert subscription.leads_used_this_month == 1

    def test_reset_monthly_usage(self, craftsman_profile, free_tier):
        """Test monthly usage reset"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=free_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            leads_used_this_month=5,
        )
        subscription.reset_monthly_usage()
        subscription.refresh_from_db()
        assert subscription.leads_used_this_month == 0

    def test_can_request_refund_within_window(self, craftsman_profile, plus_tier):
        """Test refund allowed within 14-day withdrawal window"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=plus_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            withdrawal_right_waived=False,
            withdrawal_deadline=now + timedelta(days=14),
        )
        assert subscription.can_request_refund() is True

    def test_can_request_refund_expired(self, craftsman_profile, plus_tier):
        """Test refund denied after 14-day window expires"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=plus_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            withdrawal_right_waived=False,
            withdrawal_deadline=now - timedelta(days=1),  # Expired
        )
        assert subscription.can_request_refund() is False

    def test_can_request_refund_waived(self, craftsman_profile, plus_tier):
        """Test refund denied when withdrawal right was waived"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=plus_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            withdrawal_right_waived=True,  # User waived right
            withdrawal_deadline=now + timedelta(days=14),
        )
        assert subscription.can_request_refund() is False

    def test_grace_period_allows_lead_access(self, craftsman_profile, plus_tier):
        """Test that past_due subscription still allows leads during grace period"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=plus_tier,
            status='past_due',
            current_period_start=now - timedelta(days=30),
            current_period_end=now - timedelta(days=1),
            grace_period_end=now + timedelta(days=6),  # Still in grace
        )
        assert subscription.can_receive_lead() is True

    def test_grace_period_expired_blocks_leads(self, craftsman_profile, plus_tier):
        """Test that expired grace period blocks lead access"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=plus_tier,
            status='past_due',
            current_period_start=now - timedelta(days=30),
            current_period_end=now - timedelta(days=1),
            grace_period_end=now - timedelta(days=1),  # Grace expired
        )
        assert subscription.can_receive_lead() is False


@pytest.mark.django_db
class TestFiscalValidation:
    """Test Romanian fiscal data validation"""

    def test_pf_requires_cnp(self, craftsman_user):
        """Test that PF (Persoană Fizică) requires CNP"""
        profile = CraftsmanProfile(
            user=craftsman_user,
            fiscal_type='PF',
            cnp='',  # Missing CNP
        )
        with pytest.raises(ValidationError) as exc:
            profile.clean()
        assert 'cnp' in exc.value.error_dict

    def test_pfa_requires_cui(self, craftsman_user):
        """Test that PFA requires CUI"""
        profile = CraftsmanProfile(
            user=craftsman_user,
            fiscal_type='PFA',
            cui='',  # Missing CUI
        )
        with pytest.raises(ValidationError) as exc:
            profile.clean()
        assert 'cui' in exc.value.error_dict

    def test_phone_validation_invalid_format(self, craftsman_user):
        """Test phone validation rejects invalid format"""
        profile = CraftsmanProfile(
            user=craftsman_user,
            fiscal_type='PF',
            cnp='1234567890123',
            phone='123456789',  # Invalid format
        )
        with pytest.raises(ValidationError) as exc:
            profile.clean()
        assert 'phone' in exc.value.error_dict

    def test_phone_normalization(self, craftsman_user):
        """Test phone number normalization to +40 format"""
        profile = CraftsmanProfile(
            user=craftsman_user,
            fiscal_type='PF',
            cnp='1234567890123',
            phone='0712345678',  # Should normalize to +40712345678
        )
        profile.clean()
        assert profile.phone == '+40712345678'


@pytest.mark.django_db
class TestWebhookIdempotency:
    """Test Stripe webhook event deduplication"""

    def test_webhook_event_creation(self):
        """Test webhook event can be created"""
        event = StripeWebhookEvent.objects.create(
            event_id='evt_test123',
            event_type='invoice.payment_succeeded',
            status='success',
            event_data={'test': 'data'},
        )
        assert event.event_id == 'evt_test123'

    def test_webhook_event_uniqueness(self):
        """Test event_id UNIQUE constraint prevents duplicate processing"""
        StripeWebhookEvent.objects.create(
            event_id='evt_test456',
            event_type='invoice.payment_succeeded',
            status='success',
            event_data={'test': 'data'},
        )

        # Attempt to create duplicate
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            StripeWebhookEvent.objects.create(
                event_id='evt_test456',  # Duplicate event_id
                event_type='invoice.payment_succeeded',
                status='success',
                event_data={'test': 'data2'},
            )


@pytest.mark.django_db
class TestSubscriptionLog:
    """Test subscription audit trail"""

    def test_log_creation(self, craftsman_profile, free_tier, plus_tier):
        """Test subscription log entry creation"""
        now = timezone.now()
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_profile,
            tier=free_tier,
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

        log = SubscriptionLog.objects.create(
            subscription=subscription,
            event_type='upgrade',
            old_tier=free_tier,
            new_tier=plus_tier,
            metadata={'reason': 'User initiated upgrade'},
        )

        assert log.event_type == 'upgrade'
        assert log.old_tier == free_tier
        assert log.new_tier == plus_tier
        assert 'reason' in log.metadata
