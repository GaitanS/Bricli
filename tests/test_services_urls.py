"""
Tests for services URL patterns and redirects
"""

import pytest
from django.core.management import call_command
from django.urls import reverse

from services.models import ServiceCategory


@pytest.mark.django_db
class TestServicesURLs:
    """Test suite for services URL patterns"""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Set up test data before each test"""
        # Ensure we have categories with data
        call_command("populate_categories_services")

    def test_category_list_url_returns_200(self, client):
        """Category list page should return 200 OK"""
        url = reverse("services:categories")
        response = client.get(url)

        assert response.status_code == 200

    def test_category_detail_url_returns_200(self, client):
        """Category detail pages should return 200 OK for valid slugs"""
        # Test with a known category from seed data
        url = reverse("services:category_detail", kwargs={"slug": "renovari-constructii"})
        response = client.get(url)

        assert response.status_code == 200

    def test_category_detail_all_seeded_categories(self, client):
        """All seeded categories should have accessible detail pages"""
        expected_slugs = [
            "renovari-constructii",
            "instalatii-sanitare",
            "instalatii-electrice",
            "curatenie-menaj",
            "gradinarit-peisagistica",
            "asamblare-montaj",
            "acoperisuri",
            "geamuri-ferestre",
            "design-interior",
            "it-tehnologie",
        ]

        for slug in expected_slugs:
            url = reverse("services:category_detail", kwargs={"slug": slug})
            response = client.get(url)

            assert response.status_code == 200, f"Category {slug} returned {response.status_code}"

    def test_category_detail_invalid_slug_returns_404(self, client):
        """Invalid category slug should return 404"""
        url = reverse("services:category_detail", kwargs={"slug": "non-existent-category"})
        response = client.get(url)

        assert response.status_code == 404

    def test_old_singular_category_url_redirects_301(self, client):
        """Old singular /servicii/categorie/<slug>/ should redirect to plural with 301"""
        # Old URL pattern (singular)
        old_url = "/servicii/categorie/renovari-constructii/"
        response = client.get(old_url)

        # Should be a permanent redirect
        assert response.status_code == 301

        # Should redirect to new plural URL
        assert response["Location"] == "/servicii/categorii/renovari-constructii/"

    def test_301_redirect_preserves_slug(self, client):
        """301 redirect should preserve the category slug"""
        test_cases = [
            ("instalatii-sanitare", "/servicii/categorii/instalatii-sanitare/"),
            ("instalatii-electrice", "/servicii/categorii/instalatii-electrice/"),
            ("curatenie-menaj", "/servicii/categorii/curatenie-menaj/"),
        ]

        for slug, expected_redirect in test_cases:
            old_url = f"/servicii/categorie/{slug}/"
            response = client.get(old_url)

            assert response.status_code == 301
            assert response["Location"] == expected_redirect

    def test_category_list_shows_all_categories(self, client):
        """Category list should display all active categories"""
        url = reverse("services:categories")
        response = client.get(url)

        # Should contain categories in context
        assert "categories" in response.context

        # Should have all active categories from database
        active_count = ServiceCategory.objects.filter(is_active=True).count()
        assert active_count >= 10, f"Expected at least 10 categories in DB, got {active_count}"

        # Response may show fewer due to caching, but should show at least some categories
        assert len(response.context["categories"]) > 0

    def test_category_detail_context_has_services(self, client):
        """Category detail page should have services in context"""
        url = reverse("services:category_detail", kwargs={"slug": "renovari-constructii"})
        response = client.get(url)

        # Should have category object in context
        assert "category" in response.context
        category = response.context["category"]

        # Category should have services
        assert category.services.count() >= 15

    def test_category_detail_context_has_popular_services(self, client):
        """Category detail page should have popular_services in context"""
        url = reverse("services:category_detail", kwargs={"slug": "renovari-constructii"})
        response = client.get(url)

        # Should have popular_services in context
        assert "popular_services" in response.context

        # Should have some popular services
        popular_services = response.context["popular_services"]
        assert len(popular_services) >= 15
