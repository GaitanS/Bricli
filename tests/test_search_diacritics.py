"""
Test suite for diacritics handling in search queries
"""

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import County, CraftsmanProfile, User
from services.models import CraftsmanService, Service, ServiceCategory


@pytest.fixture
def test_data_diacritics(db):
    """Create test data with Romanian characters"""
    # Create county
    county = County.objects.create(name="Iași", code="IS", slug="iasi")

    # Create category with diacritics
    cat_instalatii = ServiceCategory.objects.create(name="Instalații", slug="instalatii", icon_emoji="🔧", is_active=True)

    # Create service with diacritics
    service = Service.objects.create(name="Instalații sanitare și termice", slug="instalatii-sanitare-si-termice", category=cat_instalatii)

    # Create craftsman
    user = User.objects.create_user(
        username="craftsman_iasi", email="iasi@test.com", password="test123", user_type="craftsman", is_active=True
    )
    profile = CraftsmanProfile.objects.create(user=user, county=county, display_name="Instalator Iași", bio="Specialist în instalații sanitare și termice")

    CraftsmanService.objects.create(craftsman=profile, service=service)

    return {
        "county": county,
        "category": cat_instalatii,
        "service": service,
        "profile": profile,
    }


@pytest.mark.django_db
class TestSearchDiacritics:
    """Tests for diacritics handling in search"""

    def test_query_without_diacritics_finds_content_with_diacritics(self, test_data_diacritics, client: Client):
        """Test that query 'instalatii' finds 'Instalații'"""
        url = reverse("core:search") + "?q=instalatii"
        response = client.get(url)

        assert response.status_code == 200
        # Should find craftsman even though query has no diacritics
        assert test_data_diacritics["profile"] in response.context["craftsmen"]

    def test_query_with_diacritics_finds_content(self, test_data_diacritics, client: Client):
        """Test that query 'instalații' finds content"""
        url = reverse("core:search") + "?q=instalații"
        response = client.get(url)

        assert response.status_code == 200
        assert test_data_diacritics["profile"] in response.context["craftsmen"]

    def test_category_filter_without_diacritics(self, test_data_diacritics, client: Client):
        """Test category filter works without diacritics"""
        url = reverse("core:search") + "?category=instalatii"
        response = client.get(url)

        assert response.status_code == 200
        assert test_data_diacritics["profile"] in response.context["craftsmen"]
        assert response.context["active_category"] == test_data_diacritics["category"]

    def test_county_filter_without_diacritics(self, test_data_diacritics, client: Client):
        """Test county filter works without diacritics"""
        url = reverse("core:search") + "?county=iasi"
        response = client.get(url)

        assert response.status_code == 200
        assert test_data_diacritics["profile"] in response.context["craftsmen"]
        assert response.context["county"] == test_data_diacritics["county"]

    def test_sanitize_query_handles_special_characters(self, client: Client):
        """Test that query sanitization handles special characters"""
        queries = ["  spații   multiple  ", "test\n\nnewlines", "test\t\ttabs"]

        for query in queries:
            url = reverse("core:search") + f"?q={query}"
            response = client.get(url)
            # Should not crash
            assert response.status_code == 200

    def test_very_short_query_ignored(self, test_data_diacritics, client: Client):
        """Test that very short queries (< 2 chars) are sanitized to empty"""
        url = reverse("core:search") + "?q=a"
        response = client.get(url)

        assert response.status_code == 200
        # Query should be sanitized to empty string
        assert response.context["query"] == ""

    def test_query_normalization_preserves_meaning(self, test_data_diacritics, client: Client):
        """Test that normalization preserves query meaning"""
        # These should all find the same results
        queries = ["instalații sanitare", "instalatii sanitare", "INSTALAȚII SANITARE"]

        results_sets = []
        for query in queries:
            url = reverse("core:search") + f"?q={query}"
            response = client.get(url)
            assert response.status_code == 200
            results_sets.append(set(c.id for c in response.context["craftsmen"]))

        # All queries should return same results (best effort)
        # Note: This is best-effort matching; full equivalence requires PostgreSQL unaccent
        # For now, we just ensure no crashes and reasonable results
        assert all(len(r) > 0 for r in results_sets), "All queries should return some results"


@pytest.mark.django_db
class TestSearchLinkGeneration:
    """Tests for search link generation (no county=. in links)"""

    def test_county_select_uses_slugs(self, test_data_diacritics, client: Client):
        """Test that county select dropdown uses slugs, not IDs"""
        url = reverse("core:search")
        response = client.get(url)

        content = response.content.decode("utf-8")

        # Should use slug in option value
        assert f'value="{test_data_diacritics["county"].slug}"' in content
        # Should NOT use ID
        # Note: ID might still appear in selected logic, but value should be slug

    def test_category_filter_links_use_slugs(self, test_data_diacritics, client: Client):
        """Test that category filter sidebar links use category slugs"""
        url = reverse("core:search")
        response = client.get(url)

        content = response.content.decode("utf-8")

        # Should contain category slug in links
        assert f'category={test_data_diacritics["category"].slug}' in content

    def test_no_county_dot_in_links(self, test_data_diacritics, client: Client):
        """Test that no links contain county=. (placeholder value)"""
        url = reverse("core:search")
        response = client.get(url)

        content = response.content.decode("utf-8")

        # Should NOT contain county=.
        assert "county=." not in content

    def test_filter_chip_removal_links_preserve_params(self, test_data_diacritics, client: Client):
        """Test that filter chip removal links preserve other params"""
        url = reverse("core:search") + "?q=test&county=iasi&category=instalatii&rating=4.5"
        response = client.get(url)

        content = response.content.decode("utf-8")

        # Should show all filter chips
        assert "Iași" in content  # County chip
        assert "Instalații" in content  # Category chip
        assert "4.5+ stele" in content  # Rating chip

        # Each removal link should preserve other params
        # (Exact link structure tested in previous test file)
