"""
Phase 5: Romanian Fiscal Compliance Tests

Tests for Smart Bill API integration, invoice generation, and retry logic.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.utils import timezone
from django.contrib.auth import get_user_model

from subscriptions.models import (
    SubscriptionTier,
    CraftsmanSubscription,
    Invoice,
    SubscriptionLog,
)
from subscriptions.smartbill_service import (
    InvoiceService,
    SmartBillAPIError,
    MissingFiscalDataError,
)
from accounts.models import CraftsmanProfile, County, City

User = get_user_model()


@pytest.fixture
def county():
    """Create a County for testing"""
    return County.objects.create(name="București", slug="bucuresti")


@pytest.fixture
def city(county):
    """Create a City for testing"""
    return City.objects.create(
        name="București",
        slug="bucuresti",
        county=county
    )


@pytest.fixture
def user_with_fiscal_data():
    """Create a user with complete fiscal data"""
    user = User.objects.create_user(
        username='test_craftsman_fiscal',
        email='fiscal@example.com',
        password='testpass123',
        first_name='Ion',
        last_name='Popescu',
        user_type='craftsman'
    )
    return user


@pytest.fixture
def craftsman_with_fiscal_data(user_with_fiscal_data, county, city):
    """Create a craftsman profile with complete fiscal data"""
    profile = CraftsmanProfile.objects.create(
        user=user_with_fiscal_data,
        display_name='Ion Popescu - Constructor',
        slug='ion-popescu-constructor',
        county=county,
        city=city,
        coverage_radius_km=25,
        # Fiscal data (complete)
        fiscal_type='PFA',
        cui='12345678',
        company_name='SC Test SRL',
        fiscal_address_street='Strada Fiscala nr. 10',
        fiscal_address_city='București',
        fiscal_address_county='București',
        fiscal_address_postal_code='010101',
        phone='+40712345678',
    )
    return profile


@pytest.fixture
def craftsman_missing_fiscal_data(user_with_fiscal_data, county, city):
    """Create a craftsman profile with incomplete fiscal data"""
    profile = CraftsmanProfile.objects.create(
        user=user_with_fiscal_data,
        display_name='Ion Popescu - Constructor',
        slug='ion-popescu-constructor-2',
        county=county,
        city=city,
        coverage_radius_km=25,
        # Missing fiscal data (only type is set)
        fiscal_type='PFA',
    )
    return profile


@pytest.fixture
def plus_tier():
    """Create Plus subscription tier"""
    return SubscriptionTier.objects.create(
        name='plus',
        display_name='Plan Plus',
        price=4900,  # 49 RON
        monthly_lead_limit=None,
        stripe_price_id='price_test_plus',
    )


@pytest.fixture
def subscription_with_fiscal_data(craftsman_with_fiscal_data, plus_tier):
    """Create an active subscription for craftsman with fiscal data"""
    return CraftsmanSubscription.objects.create(
        craftsman=craftsman_with_fiscal_data,
        tier=plus_tier,
        status='active',
        stripe_subscription_id='sub_test123',
        stripe_customer_id='cus_test123',
        current_period_start=timezone.now(),
        current_period_end=timezone.now() + timezone.timedelta(days=30),
    )


@pytest.mark.django_db
class TestTVACalculation:
    """Tests for TVA (19%) calculation"""

    def test_calculate_tva_for_49_ron(self):
        """Test TVA calculation for 49 RON subscription"""
        total_ron = Decimal('49.00')
        base_ron, tva_ron, total = InvoiceService.calculate_tva(total_ron)

        # 49 / 1.19 = 41.18 (base)
        # 49 - 41.18 = 7.82 (TVA)
        assert base_ron == Decimal('41.18')
        assert tva_ron == Decimal('7.82')
        assert total == Decimal('49.00')
        assert base_ron + tva_ron == total

    def test_calculate_tva_for_149_ron(self):
        """Test TVA calculation for 149 RON subscription"""
        total_ron = Decimal('149.00')
        base_ron, tva_ron, total = InvoiceService.calculate_tva(total_ron)

        # 149 / 1.19 = 125.21 (base)
        # 149 - 125.21 = 23.79 (TVA)
        assert base_ron == Decimal('125.21')
        assert tva_ron == Decimal('23.79')
        assert total == Decimal('149.00')

    def test_calculate_tva_rounding(self):
        """Test that TVA calculation rounds to 2 decimals"""
        total_ron = Decimal('99.99')
        base_ron, tva_ron, total = InvoiceService.calculate_tva(total_ron)

        # Check all values have exactly 2 decimal places
        assert base_ron.as_tuple().exponent == -2
        assert tva_ron.as_tuple().exponent == -2
        assert total.as_tuple().exponent == -2


@pytest.mark.django_db
class TestFiscalDataValidation:
    """Tests for fiscal data validation"""

    def test_validate_fiscal_data_complete_pfa(self, craftsman_with_fiscal_data):
        """Test validation passes for complete PFA data"""
        # Should not raise any exception
        InvoiceService.validate_fiscal_data(craftsman_with_fiscal_data)

    def test_validate_fiscal_data_complete_pf(self, user_with_fiscal_data, county, city):
        """Test validation passes for complete PF (Persoană Fizică) data"""
        craftsman = CraftsmanProfile.objects.create(
            user=user_with_fiscal_data,
            display_name='Test PF',
            slug='test-pf',
            county=county,
            city=city,
            coverage_radius_km=25,
            fiscal_type='PF',
            cnp='1234567890123',  # PF uses CNP instead of CUI
            fiscal_address_street='Strada Test',
            fiscal_address_city='București',
            fiscal_address_county='București',
            fiscal_address_postal_code='010101',
        )

        # Should not raise any exception
        InvoiceService.validate_fiscal_data(craftsman)

    def test_validate_fiscal_data_missing_cui_for_pfa(self, craftsman_missing_fiscal_data):
        """Test validation fails for PFA without CUI"""
        craftsman_missing_fiscal_data.fiscal_type = 'PFA'
        craftsman_missing_fiscal_data.save()

        with pytest.raises(MissingFiscalDataError) as exc_info:
            InvoiceService.validate_fiscal_data(craftsman_missing_fiscal_data)

        assert 'CUI' in str(exc_info.value)

    def test_validate_fiscal_data_missing_address(self, craftsman_with_fiscal_data):
        """Test validation fails for missing address fields"""
        craftsman_with_fiscal_data.fiscal_address_street = None
        craftsman_with_fiscal_data.save()

        with pytest.raises(MissingFiscalDataError) as exc_info:
            InvoiceService.validate_fiscal_data(craftsman_with_fiscal_data)

        assert 'Adresa fiscală' in str(exc_info.value)


@pytest.mark.django_db
class TestInvoiceCreation:
    """Tests for Smart Bill invoice creation"""

    @patch('subscriptions.smartbill_service.requests.post')
    def test_create_invoice_success(self, mock_post, subscription_with_fiscal_data):
        """Test successful invoice creation via Smart Bill API"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'series': 'SUBS',
            'number': '12345',
            'url': 'https://smartbill.ro/invoice/12345',
        }
        mock_post.return_value = mock_response

        # Create invoice
        invoice_data = InvoiceService.create_invoice(
            subscription=subscription_with_fiscal_data,
            stripe_invoice_id='in_test123'
        )

        # Verify API was called
        assert mock_post.called
        call_args = mock_post.call_args

        # Verify invoice data structure
        payload = call_args.kwargs['json']
        assert payload['client']['vatCode'] == '12345678'
        assert payload['client']['name'] == 'SC Test SRL'
        assert payload['products'][0]['name'] == 'Abonament Plan Plus - Bricli.ro'
        assert payload['products'][0]['taxPercentage'] == 19

        # Verify TVA calculation in payload
        assert payload['products'][0]['price'] == 41.18  # Base price (49 / 1.19)

        # Verify success log was created
        log = SubscriptionLog.objects.filter(
            subscription=subscription_with_fiscal_data,
            event_type='invoice_created'
        ).first()
        assert log is not None
        assert log.metadata['stripe_invoice_id'] == 'in_test123'

        # Verify return data
        assert invoice_data['series'] == 'SUBS'
        assert invoice_data['number'] == '12345'

    @patch('subscriptions.smartbill_service.requests.post')
    def test_create_invoice_api_error(self, mock_post, subscription_with_fiscal_data):
        """Test invoice creation handles API errors correctly"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid fiscal code'
        mock_post.return_value = mock_response

        with pytest.raises(SmartBillAPIError):
            InvoiceService.create_invoice(
                subscription=subscription_with_fiscal_data,
                stripe_invoice_id='in_test123'
            )

        # Verify pending log was created for retry
        log = SubscriptionLog.objects.filter(
            subscription=subscription_with_fiscal_data,
            event_type='invoice_pending'
        ).first()
        assert log is not None
        assert log.metadata['retry_count'] == 0
        assert 'Invalid fiscal code' in log.metadata['error']

    def test_create_invoice_missing_fiscal_data(self, craftsman_missing_fiscal_data, plus_tier):
        """Test invoice creation fails gracefully for missing fiscal data"""
        subscription = CraftsmanSubscription.objects.create(
            craftsman=craftsman_missing_fiscal_data,
            tier=plus_tier,
            status='active',
            stripe_subscription_id='sub_test456',
            stripe_customer_id='cus_test456',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        with pytest.raises(MissingFiscalDataError):
            InvoiceService.create_invoice(
                subscription=subscription,
                stripe_invoice_id='in_test456'
            )


@pytest.mark.django_db
class TestInvoiceModel:
    """Tests for Invoice model"""

    def test_invoice_creation(self, subscription_with_fiscal_data):
        """Test Invoice model creation with all fields"""
        invoice = Invoice.objects.create(
            subscription=subscription_with_fiscal_data,
            stripe_invoice_id='in_test789',
            smartbill_series='SUBS',
            smartbill_number='12345',
            smartbill_url='https://smartbill.ro/invoice/12345',
            total_ron=Decimal('49.00'),
            base_ron=Decimal('41.18'),
            tva_ron=Decimal('7.82'),
            client_name='SC Test SRL',
            client_fiscal_code='12345678',
            client_address='Strada Fiscala nr. 10, București',
        )

        assert invoice.id is not None
        assert invoice.get_download_filename() == 'Factura_SUBS_12345.pdf'
        assert str(invoice) == 'Invoice SUBS-12345 - 49.00 RON'

    def test_invoice_unique_constraint(self, subscription_with_fiscal_data):
        """Test that stripe_invoice_id must be unique"""
        Invoice.objects.create(
            subscription=subscription_with_fiscal_data,
            stripe_invoice_id='in_test_unique',
            smartbill_series='SUBS',
            smartbill_number='12345',
            total_ron=Decimal('49.00'),
            base_ron=Decimal('41.18'),
            tva_ron=Decimal('7.82'),
            client_name='Test',
            client_fiscal_code='12345678',
            client_address='Test Address',
        )

        # Attempting to create another invoice with same stripe_invoice_id should fail
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Invoice.objects.create(
                subscription=subscription_with_fiscal_data,
                stripe_invoice_id='in_test_unique',  # Same ID
                smartbill_series='SUBS',
                smartbill_number='67890',
                total_ron=Decimal('49.00'),
                base_ron=Decimal('41.18'),
                tva_ron=Decimal('7.82'),
                client_name='Test',
                client_fiscal_code='12345678',
                client_address='Test Address',
            )


@pytest.mark.django_db
class TestInvoiceRetryLogic:
    """Tests for invoice retry management command"""

    def test_pending_invoice_log_structure(self, subscription_with_fiscal_data):
        """Test that pending invoice logs have correct structure"""
        log = SubscriptionLog.objects.create(
            subscription=subscription_with_fiscal_data,
            event_type='invoice_pending',
            old_tier=subscription_with_fiscal_data.tier,
            new_tier=subscription_with_fiscal_data.tier,
            metadata={
                'stripe_invoice_id': 'in_test_pending',
                'error': 'API timeout',
                'retry_count': 0,
            }
        )

        assert log.metadata['retry_count'] == 0
        assert 'stripe_invoice_id' in log.metadata
        assert 'error' in log.metadata

    @patch('subscriptions.smartbill_service.requests.post')
    def test_retry_increments_count(self, mock_post, subscription_with_fiscal_data):
        """Test that retry attempts increment retry_count"""
        # Create pending log
        log = SubscriptionLog.objects.create(
            subscription=subscription_with_fiscal_data,
            event_type='invoice_pending',
            old_tier=subscription_with_fiscal_data.tier,
            new_tier=subscription_with_fiscal_data.tier,
            metadata={
                'stripe_invoice_id': 'in_test_retry',
                'error': 'Previous error',
                'retry_count': 2,  # Already tried twice
            }
        )

        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Server error'
        mock_post.return_value = mock_response

        # Attempt retry
        with pytest.raises(SmartBillAPIError):
            InvoiceService.retry_failed_invoice(log)

        # Verify retry count was incremented
        log.refresh_from_db()
        assert log.metadata['retry_count'] == 3
        assert 'Server error' in log.metadata['last_error']


@pytest.mark.django_db
class TestInvoiceDownload:
    """Tests for invoice PDF download"""

    @patch('subscriptions.smartbill_service.requests.get')
    def test_get_invoice_pdf_success(self, mock_get):
        """Test successful PDF download from Smart Bill"""
        # Mock PDF response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'%PDF-1.4...'  # Mock PDF content
        mock_get.return_value = mock_response

        pdf_content = InvoiceService.get_invoice_pdf(
            series='SUBS',
            number='12345'
        )

        assert pdf_content == b'%PDF-1.4...'
        assert mock_get.called

    @patch('subscriptions.smartbill_service.requests.get')
    def test_get_invoice_pdf_api_error(self, mock_get):
        """Test PDF download handles API errors"""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = 'Invoice not found'
        mock_get.return_value = mock_response

        with pytest.raises(SmartBillAPIError) as exc_info:
            InvoiceService.get_invoice_pdf(
                series='SUBS',
                number='99999'
            )

        assert 'Invoice not found' in str(exc_info.value)
