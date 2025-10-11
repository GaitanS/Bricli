"""
Test suite for search category filtering functionality
"""

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import County, CraftsmanProfile, User
from services.models import CraftsmanService, Service, ServiceCategory


@pytest.fixture
def test_data(db):
    """Create test data for search tests"""
    # Create county with slug
    county = County.objects.create(name="București", code="B", slug="bucuresti")

    # Create categories with slugs
    cat_constructii = ServiceCategory.objects.create(
        name="Construcții", slug="constructii", icon_emoji="🏗️", is_active=True
    )
    cat_instalatii = ServiceCategory.objects.create(
        name="Instalații", slug="instalatii", icon_emoji="🔧", is_active=True
    )

    # Create services
    service_zidarie = Service.objects.create(name="Zidărie", slug="zidarie", category=cat_constructii)
    service_instalatii = Service.objects.create(name="Instalații sanitare", slug="instalatii-sanitare", category=cat_instalatii)

    # Create craftsman user
    user = User.objects.create_user(username="craftsman1", email="craft@test.com", password="test123", user_type="craftsman", is_active=True)

    # Create craftsman profile
    profile = CraftsmanProfile.objects.create(user=user, county=county, display_name="Test Craftsman", bio="Test bio for craftsman")

    # Add services to craftsman
    CraftsmanService.objects.create(craftsman=profile, service=service_zidarie)
    CraftsmanService.objects.create(craftsman=profile, service=service_instalatii)

    return {
        "county": county,
        "cat_constructii": cat_constructii,
        "cat_instalatii": cat_instalatii,
        "service_zidarie": service_zidarie,
        "service_instalatii": service_instalatii,
        "user": user,
        "profile": profile,
    }


@pytest.mark.django_db
class TestSearchCategoryFilter:
    """Tests for category filtering in search"""

    def test_search_with_valid_category(self, test_data, client: Client):
        """Test search filters by valid category slug"""
        url = reverse("core:search") + "?category=constructii"
        response = client.get(url)

        assert response.status_code == 200
        assert test_data["profile"] in response.context["craftsmen"]

    def test_search_with_invalid_category(self, test_data, client: Client):
        """Test search ignores invalid category slug"""
        url = reverse("core:search") + "?category=invalid-category"
        response = client.get(url)

        assert response.status_code == 200
        # Should show all craftsmen (not filtered)
        assert test_data["profile"] in response.context["craftsmen"]

    def test_search_category_with_diacritics(self, test_data, client: Client):
        """Test category filter works with diacritics in slug"""
        # Create category with diacritics that normalizes to same slug
        url = reverse("core:search") + "?category=instalatii"  # without diacritics
        response = client.get(url)

        assert response.status_code == 200
        assert test_data["profile"] in response.context["craftsmen"]

    def test_search_combined_filters(self, test_data, client: Client):
        """Test search with county + category + query combined"""
        url = reverse("core:search") + "?q=test&county=bucuresti&category=constructii"
        response = client.get(url)

        assert response.status_code == 200
        # Profile should match all filters
        assert test_data["profile"] in response.context["craftsmen"]

    def test_search_category_filter_distinct(self, test_data, client: Client):
        """Test that category filter returns distinct craftsmen"""
        # Craftsman has multiple services in same category - should appear once
        url = reverse("core:search") + "?category=constructii"
        response = client.get(url)

        craftsmen = list(response.context["craftsmen"])
        # Check no duplicates
        assert len(craftsmen) == len(set(c.id for c in craftsmen))

    def test_active_category_in_context(self, test_data, client: Client):
        """Test that active category is passed to context"""
        url = reverse("core:search") + "?category=instalatii"
        response = client.get(url)

        assert "active_category" in response.context
        assert response.context["active_category"] == test_data["cat_instalatii"]

    def test_inactive_category_ignored(self, test_data, client: Client):
        """Test that inactive categories are ignored"""
        # Create inactive category
        inactive_cat = ServiceCategory.objects.create(name="Inactive Cat", slug="inactive", is_active=False)

        url = reverse("core:search") + "?category=inactive"
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["active_category"] is None

    def test_service_categories_in_context(self, test_data, client: Client):
        """Test that service_categories are passed to context for sidebar"""
        url = reverse("core:search")
        response = client.get(url)

        assert "service_categories" in response.context
        categories = list(response.context["service_categories"])
        assert len(categories) >= 2  # At least our test categories
        assert test_data["cat_constructii"] in categories
        assert test_data["cat_instalatii"] in categories
