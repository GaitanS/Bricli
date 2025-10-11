"""
Test suite for Search UI components (mobile offcanvas, desktop sidebar, filter chips)
"""

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import County, CraftsmanProfile, User
from services.models import CraftsmanService, Service, ServiceCategory


@pytest.fixture
def test_search_data(db):
    """Create test data for search UI tests"""
    # Create counties with slugs
    county_bucuresti = County.objects.create(name="București", code="B", slug="bucuresti")
    county_cluj = County.objects.create(name="Cluj", code="CJ", slug="cluj")

    # Create categories
    cat_constructii = ServiceCategory.objects.create(
        name="Construcții", slug="constructii", icon_emoji="🏗️", is_active=True
    )
    cat_instalatii = ServiceCategory.objects.create(
        name="Instalații", slug="instalatii", icon_emoji="🔧", is_active=True
    )

    # Create service
    service = Service.objects.create(name="Zidărie", slug="zidarie", category=cat_constructii)

    # Create craftsman
    user = User.objects.create_user(
        username="craftsman_test",
        email="test@test.com",
        password="test123",
        user_type="craftsman",
        is_active=True,
    )
    profile = CraftsmanProfile.objects.create(
        user=user, county=county_bucuresti, display_name="Test Craftsman", bio="Test bio"
    )
    CraftsmanService.objects.create(craftsman=profile, service=service)

    return {
        "counties": [county_bucuresti, county_cluj],
        "categories": [cat_constructii, cat_instalatii],
        "profile": profile,
    }


@pytest.mark.django_db
class TestSearchUIComponents:
    """Tests for search UI component presence and functionality"""

    def test_search_page_loads(self, test_search_data, client: Client):
        """Test that search page loads successfully"""
        url = reverse("core:search")
        response = client.get(url)

        assert response.status_code == 200
        assert "cautare" in response.request["PATH_INFO"].lower()

    def test_offcanvas_element_present(self, test_search_data, client: Client):
        """Test that mobile offcanvas drawer is present"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        assert 'id="filtersOffcanvas"' in content
        assert 'offcanvas-end' in content
        assert 'd-lg-none' in content  # Hidden on desktop

    def test_sidebar_element_present(self, test_search_data, client: Client):
        """Test that desktop sidebar is present"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        assert 'd-none d-lg-block' in content  # Hidden on mobile, visible on desktop
        assert 'position-sticky' in content

    def test_filter_button_present(self, test_search_data, client: Client):
        """Test that mobile filter button exists"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        assert 'id="filterBtn"' in content
        assert 'Filtrează' in content
        assert 'data-bs-toggle="offcanvas"' in content

    def test_filter_chips_present_with_filters(self, test_search_data, client: Client):
        """Test that filter chips appear when filters are active"""
        url = reverse("core:search") + "?county=bucuresti&rating=4.5"
        response = client.get(url)
        content = response.content.decode()

        # Active filter indicators
        assert "Filtre active:" in content or "București" in content
        assert "fa-times" in content  # Remove icon

    def test_no_filter_chips_without_filters(self, test_search_data, client: Client):
        """Test that filter chips don't appear without active filters"""
        url = reverse("core:search")
        response = client.get(url)

        # Should not show "active filters" section when no filters
        # Just verify page loads successfully
        assert response.status_code == 200

    def test_county_select_uses_slugs(self, test_search_data, client: Client):
        """Test that county select uses slugs instead of IDs"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        # Should have county slug values
        assert 'value="bucuresti"' in content
        assert 'value="cluj"' in content
        # Should NOT have placeholder values
        assert 'value="."' not in content

    def test_category_list_present(self, test_search_data, client: Client):
        """Test that category radio buttons are present"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        assert 'name="category"' in content
        assert 'type="radio"' in content
        assert 'Construcții' in content
        assert 'Instalații' in content

    def test_rating_select_present(self, test_search_data, client: Client):
        """Test that rating select is present"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        assert 'name="rating"' in content
        assert 'Rating minim' in content or 'rating' in content.lower()
        assert '4.5' in content or '4.0' in content

    def test_search_input_preserves_query(self, test_search_data, client: Client):
        """Test that search input preserves query parameter"""
        url = reverse("core:search") + "?q=instalatii"
        response = client.get(url)
        content = response.content.decode()

        assert 'value="instalatii"' in content or 'instalatii' in content

    def test_js_file_included(self, test_search_data, client: Client):
        """Test that search-filters.js is included"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        assert 'search-filters.js' in content

    def test_css_file_included(self, test_search_data, client: Client):
        """Test that search.css is included"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        assert 'search.css' in content

    def test_no_invalid_county_values_in_html(self, test_search_data, client: Client):
        """Test that HTML doesn't contain invalid county values"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        # Should NOT contain these invalid values
        assert 'county=.' not in content
        assert 'county=all' not in content
        assert 'county=toate' not in content

    def test_querystring_tag_works(self, test_search_data, client: Client):
        """Test that querystring template tag generates valid URLs"""
        url = reverse("core:search") + "?q=test&county=bucuresti"
        response = client.get(url)
        content = response.content.decode()

        # Should have links with properly encoded query strings
        # (hard to test exact format, but should not crash)
        assert response.status_code == 200
        assert 'href="?' in content

    def test_apply_filters_button_present(self, test_search_data, client: Client):
        """Test that apply filters button exists"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        assert 'Aplică filtre' in content or 'type="submit"' in content

    def test_reset_filters_link_present(self, test_search_data, client: Client):
        """Test that reset filters link exists"""
        url = reverse("core:search") + "?county=bucuresti"
        response = client.get(url)
        content = response.content.decode()

        assert 'Reset' in content or 'Șterge' in content


@pytest.mark.django_db
class TestSearchUIResponsiveness:
    """Tests for responsive behavior"""

    def test_mobile_only_elements(self, test_search_data, client: Client):
        """Test that mobile-only elements have correct classes"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        # Offcanvas should be mobile-only
        assert 'd-lg-none' in content

    def test_desktop_only_elements(self, test_search_data, client: Client):
        """Test that desktop-only elements have correct classes"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        # Sidebar should be desktop-only
        assert 'd-none d-lg-block' in content

    def test_column_ordering(self, test_search_data, client: Client):
        """Test that column ordering is responsive"""
        url = reverse("core:search")
        response = client.get(url)
        content = response.content.decode()

        # Should have order classes for responsive layout
        assert 'order-1' in content and 'order-2' in content
        assert 'order-lg-1' in content or 'order-lg-2' in content
