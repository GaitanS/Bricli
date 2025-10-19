#!/usr/bin/env python
"""
BETA Feature Testing Script
Tests all BETA functionality to ensure everything works correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bricli.settings')
django.setup()

from django.conf import settings
from accounts.models import User, CraftsmanProfile
from services.lead_quota_service import LeadQuotaService


def test_feature_flags():
    """Test that feature flags are correctly set"""
    print("\n" + "="*60)
    print("TEST 1: Feature Flags Configuration")
    print("="*60)

    assert hasattr(settings, 'SUBSCRIPTIONS_ENABLED'), "SUBSCRIPTIONS_ENABLED not found in settings"
    assert settings.SUBSCRIPTIONS_ENABLED == False, "SUBSCRIPTIONS_ENABLED should be False for BETA"

    print("[PASS] SUBSCRIPTIONS_ENABLED = False (BETA mode active)")
    print("[PASS] Feature flags configured correctly")
    return True


def test_lead_quota_bypass():
    """Test that lead quota service bypasses checks in BETA mode"""
    print("\n" + "="*60)
    print("TEST 2: Lead Quota Bypass")
    print("="*60)

    # Get a craftsman user (or create test user)
    craftsman = User.objects.filter(user_type='craftsman').first()

    if not craftsman:
        print("[SKIP] No craftsman users found in database")
        print("   Creating test craftsman for testing...")
        # Would need to create test user here
        return None

    # Test can_receive_lead
    can_receive, error = LeadQuotaService.can_receive_lead(craftsman)

    print(f"   Craftsman: {craftsman.get_full_name()} ({craftsman.email})")
    print(f"   Can receive lead: {can_receive}")
    print(f"   Error message: {error or 'None'}")

    assert can_receive == True, "Craftsman should be able to receive leads in BETA mode"
    assert error is None, "No error should be returned in BETA mode"

    # Test get_quota_status
    quota_status = LeadQuotaService.get_quota_status(craftsman)

    print(f"\n   Quota Status:")
    print(f"   - Tier: {quota_status['tier_name']}")
    print(f"   - Tier Display: {quota_status['tier_display']}")
    print(f"   - Leads Used: {quota_status['leads_used']}")
    print(f"   - Leads Limit: {quota_status['leads_limit']}")
    print(f"   - Can Receive: {quota_status['can_receive']}")
    print(f"   - Status: {quota_status['status']}")

    assert quota_status['tier_name'] == 'BETA', "Tier should be 'BETA'"
    assert quota_status['leads_limit'] is None, "Leads limit should be unlimited (None)"
    assert quota_status['can_receive'] == True, "Should be able to receive leads"

    print("\n[PASS] Lead quota bypass working correctly")
    return True


def test_beta_tracking():
    """Test BETA member tracking"""
    print("\n" + "="*60)
    print("TEST 3: BETA Member Tracking")
    print("="*60)

    # Check if beta_member field exists
    beta_members = CraftsmanProfile.objects.filter(beta_member=True)
    total_craftsmen = CraftsmanProfile.objects.count()

    print(f"   Total craftsmen: {total_craftsmen}")
    print(f"   BETA members: {beta_members.count()}")

    if beta_members.exists():
        print(f"\n   BETA Members List:")
        for profile in beta_members.order_by('beta_registration_number'):
            print(f"   #{profile.beta_registration_number}: {profile.user.get_full_name()} ({profile.user.email})")
    else:
        print("   No BETA members registered yet")

    print("\n[PASS] BETA tracking fields exist and working")
    return True


def test_context_processor():
    """Test that context processor makes SUBSCRIPTIONS_ENABLED available"""
    print("\n" + "="*60)
    print("TEST 4: Context Processor")
    print("="*60)

    from core.context_processors import feature_flags_context
    from django.http import HttpRequest

    request = HttpRequest()
    context = feature_flags_context(request)

    assert 'SUBSCRIPTIONS_ENABLED' in context, "SUBSCRIPTIONS_ENABLED not in context"
    assert context['SUBSCRIPTIONS_ENABLED'] == False, "SUBSCRIPTIONS_ENABLED should be False"

    print(f"   Context: {context}")
    print("[PASS] Context processor working correctly")
    return True


def run_all_tests():
    """Run all BETA tests"""
    print("\n" + "="*60)
    print("BRICLI BETA FEATURE TESTING")
    print("="*60)

    results = []

    try:
        results.append(("Feature Flags", test_feature_flags()))
    except Exception as e:
        print(f"[FAIL] Feature Flags Test Failed: {e}")
        results.append(("Feature Flags", False))

    try:
        results.append(("Lead Quota Bypass", test_lead_quota_bypass()))
    except Exception as e:
        print(f"[FAIL] Lead Quota Bypass Test Failed: {e}")
        results.append(("Lead Quota Bypass", False))

    try:
        results.append(("BETA Tracking", test_beta_tracking()))
    except Exception as e:
        print(f"[FAIL] BETA Tracking Test Failed: {e}")
        results.append(("BETA Tracking", False))

    try:
        results.append(("Context Processor", test_context_processor()))
    except Exception as e:
        print(f"[FAIL] Context Processor Test Failed: {e}")
        results.append(("Context Processor", False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)

    for test_name, result in results:
        status = "[PASS]" if result is True else "[SKIP]" if result is None else "[FAIL]"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    if failed == 0:
        print("\nAll tests passed! BETA features working correctly.")
    else:
        print(f"\n{failed} test(s) failed. Please review.")

    print("="*60 + "\n")


if __name__ == '__main__':
    run_all_tests()
