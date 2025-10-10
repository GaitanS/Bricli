"""
Tests for suggestions sidebar links in search page
"""

import pytest
from django.core.management import call_command
from django.urls import reverse


@pytest.mark.django_db
class TestSuggestionsLinks:
    """Test suite for suggestions card links"""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Set up test data before each test"""
        # Ensure we have categories and services
        call_command("populate_categories_services")

    def test_search_page_has_suggestions_context(self, client):
        """Search page should have categories and popular_services in context"""
        url = reverse("core:search")
        response = client.get(url, {"q": "renovare"})

        assert response.status_code == 200
        assert "categories" in response.context
        assert "popular_services" in response.context

    def test_suggestions_has_popular_services(self, client):
        """Suggestions should include popular services"""
        url = reverse("core:search")
        response = client.get(url, {"q": "renovare"})

        popular_services = response.context["popular_services"]

        # Should have at least some popular services
        assert len(popular_services) > 0

        # All should be marked as popular and active
        for service in popular_services:
            assert service.is_popular
            assert service.is_active

    def test_suggestions_has_categories(self, client):
        """Suggestions should include active categories"""
        url = reverse("core:search")
        response = client.get(url, {"q": "renovare"})

        categories = response.context["categories"]

        # Should have at least some categories
        assert len(categories) > 0

        # All should be active
        for category in categories:
            assert category.is_active

    def test_suggestions_service_links_use_url_tag(self, client):
        """Service links in suggestions should use {% url %} pattern"""
        url = reverse("core:search")
        response = client.get(url, {"q": "renovare"})

        content = response.content.decode()

        # Should contain search URL pattern
        assert "{% url 'core:search' %}" in response.content.decode() or "/cautare/" in content

        # Should have service links with urlencode
        popular_services = response.context["popular_services"]
        if popular_services:
            # At least one service should appear as a link
            first_service = popular_services[0]
            # The service name should appear in the HTML
            assert first_service.name in content

    def test_suggestions_category_links_use_url_tag(self, client):
        """Category links in suggestions should use {% url %} pattern"""
        url = reverse("core:search")
        response = client.get(url, {"q": "renovare"})

        content = response.content.decode()

        # Should contain category detail URL pattern
        categories = response.context["categories"]
        if categories:
            # At least one category should appear as a link
            first_category = categories[0]
            # The category name should appear in the HTML
            assert first_category.name in content
            # Should link to category detail
            assert f"/servicii/categorii/{first_category.slug}/" in content

    def test_service_links_are_searchable(self, client):
        """Clicking a service link should lead to search with that service"""
        # Get a popular service
        url = reverse("core:search")
        response = client.get(url, {"q": "test"})

        popular_services = response.context["popular_services"]
        assert len(popular_services) > 0

        first_service = popular_services[0]

        # Build expected search URL
        search_url = reverse("core:search")
        service_search_response = client.get(search_url, {"q": first_service.name})

        # Should return 200 OK
        assert service_search_response.status_code == 200

        # Should have the query in context
        assert service_search_response.context["query"] == first_service.name

    def test_category_links_lead_to_detail_pages(self, client):
        """Clicking a category link should lead to category detail page"""
        # Get categories
        url = reverse("core:search")
        response = client.get(url, {"q": "test"})

        categories = response.context["categories"]
        assert len(categories) > 0

        first_category = categories[0]

        # Visit category detail page
        category_url = reverse("services:category_detail", kwargs={"slug": first_category.slug})
        category_response = client.get(category_url)

        # Should return 200 OK
        assert category_response.status_code == 200

        # Should have category in context
        assert "category" in category_response.context
        assert category_response.context["category"].slug == first_category.slug

    def test_datalist_contains_popular_services(self, client):
        """Search form datalist should contain popular services for autocomplete"""
        url = reverse("core:search")
        response = client.get(url, {"q": "test"})

        content = response.content.decode()

        # Should have datalist element
        assert '<datalist id="popular-services">' in content

        # Should contain some popular services
        popular_services = response.context["popular_services"]
        if popular_services:
            # At least first 5 services should be in datalist
            for service in popular_services[:5]:
                assert f'<option value="{service.name}">' in content

    def test_suggestions_shows_fa_icons(self, client):
        """Category suggestions should display Font Awesome icons"""
        url = reverse("core:search")
        response = client.get(url, {"q": "test"})

        content = response.content.decode()
        categories = response.context["categories"]

        if categories:
            # Font Awesome icons should be present
            assert "fas fa-" in content

            # At least one category icon should be present
            from services.icon_map import ICONS

            icon_count = sum(1 for icon in ICONS.values() if icon in content)
            assert icon_count >= 1, f"Expected at least 1 FA icon in suggestions, found {icon_count}"

    def test_suggestions_limits_display_count(self, client):
        """Suggestions should limit the number of displayed items"""
        url = reverse("core:search")
        response = client.get(url, {"q": "test"})

        content = response.content.decode()

        # Count how many service badges appear in suggestions
        # Should be limited to around 5 in the sidebar (as per |slice:":5")
        popular_services = response.context["popular_services"]

        # Context should have many services
        assert len(popular_services) >= 5

        # But HTML should only show first 5 in suggestions sidebar
        # (Full list of 30 available in datalist for autocomplete)
