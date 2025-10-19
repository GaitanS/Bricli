"""
Phase 2: Wallet Removal Tests

These tests verify that the wallet system has been completely removed from the codebase.
"""

import pytest
from django.db import connection
from django.apps import apps


@pytest.mark.django_db
class TestWalletRemoval:
    """Tests to verify wallet models have been removed from database."""

    def test_wallet_tables_do_not_exist(self):
        """Verify CreditWallet and WalletTransaction tables no longer exist."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            # Assert wallet tables are gone
            assert "services_creditwallet" not in tables, "CreditWallet table should be removed"
            assert "services_wallettransaction" not in tables, "WalletTransaction table should be removed"
            assert "services_paymentintent" not in tables, "PaymentIntent table should be removed"
            assert "services_paymentmethod" not in tables, "PaymentMethod table should be removed"
            assert "services_stripecustomer" not in tables, "StripeCustomer table should be removed"

    def test_wallet_models_not_in_registry(self):
        """Verify wallet models are not registered in Django apps."""
        try:
            apps.get_model("services", "CreditWallet")
            pytest.fail("CreditWallet model should not be registered")
        except LookupError:
            pass  # Expected - model should not exist

        try:
            apps.get_model("services", "WalletTransaction")
            pytest.fail("WalletTransaction model should not be registered")
        except LookupError:
            pass  # Expected - model should not exist

    def test_subscription_models_exist(self):
        """Verify subscription models exist as replacement."""
        # These should succeed - subscription models should exist
        tier_model = apps.get_model("subscriptions", "SubscriptionTier")
        subscription_model = apps.get_model("subscriptions", "CraftsmanSubscription")

        assert tier_model is not None, "SubscriptionTier model should exist"
        assert subscription_model is not None, "CraftsmanSubscription model should exist"


@pytest.mark.django_db
class TestWalletCodeRemoval:
    """Tests to verify wallet-related code has been removed/archived."""

    def test_wallet_service_files_archived(self):
        """Verify wallet service files are archived."""
        import os

        base_path = "services"

        # Files should be archived with .REMOVED_PHASE2 extension
        assert os.path.exists(f"{base_path}/wallet_service.py.REMOVED_PHASE2"), \
            "wallet_service.py should be archived"
        assert os.path.exists(f"{base_path}/lead_fee_service.py.REMOVED_PHASE2"), \
            "lead_fee_service.py should be archived"
        assert os.path.exists(f"{base_path}/payment_views.py.REMOVED_PHASE2"), \
            "payment_views.py should be archived"
        assert os.path.exists(f"{base_path}/payment_urls.py.REMOVED_PHASE2"), \
            "payment_urls.py should be archived"

        # Active files should not import wallet models
        assert not os.path.exists(f"{base_path}/wallet_service.py"), \
            "wallet_service.py should be archived, not active"
        assert not os.path.exists(f"{base_path}/lead_fee_service.py"), \
            "lead_fee_service.py should be archived, not active"

    def test_wallet_templates_archived(self):
        """Verify wallet templates are archived."""
        import os

        base_path = "templates/services"

        # Templates should be archived
        assert os.path.exists(f"{base_path}/wallet.html.REMOVED_PHASE2"), \
            "wallet.html should be archived"
        assert os.path.exists(f"{base_path}/wallet_topup.html.REMOVED_PHASE2"), \
            "wallet_topup.html should be archived"
        assert os.path.exists(f"{base_path}/payment_success.html.REMOVED_PHASE2"), \
            "payment_success.html should be archived"
        assert os.path.exists(f"{base_path}/payment_cancel.html.REMOVED_PHASE2"), \
            "payment_cancel.html should be archived"

        # Active templates should not exist
        assert not os.path.exists(f"{base_path}/wallet.html"), \
            "wallet.html should be archived, not active"


@pytest.mark.django_db
class TestWalletDataExport:
    """Tests to verify wallet data was exported before removal."""

    def test_wallet_export_files_exist(self):
        """Verify wallet export CSV files were created."""
        import os
        import glob

        # Check for wallet export CSV files
        wallet_exports = glob.glob("wallet_export_*_wallets.csv")
        transaction_exports = glob.glob("wallet_export_*_transactions.csv")

        assert len(wallet_exports) > 0, "Wallet export CSV should exist"
        assert len(transaction_exports) > 0, "Transaction export CSV should exist"

        # Verify CSVs have correct headers
        if wallet_exports:
            with open(wallet_exports[0], 'r') as f:
                header = f.readline().strip()
                assert "User Email" in header, "Wallet CSV should have User Email column"
                assert "Balance (RON)" in header, "Wallet CSV should have Balance column"

        if transaction_exports:
            with open(transaction_exports[0], 'r') as f:
                header = f.readline().strip()
                assert "User Email" in header, "Transaction CSV should have User Email column"
                assert "Amount (RON)" in header, "Transaction CSV should have Amount column"
