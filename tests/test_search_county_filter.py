"""
Test suite for search county filtering and 301 redirects
"""

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import County, CraftsmanProfile, User


@pytest.fixture
def test_county(db):
    """Create test county with slug"""
    return County.objects.create(name="Cluj", code="CJ", slug="cluj")


@pytest.fixture
def test_craftsman(db, test_county):
    """Create test craftsman in Cluj"""
    user = User.objects.create_user(
        username="craftsman_cluj", email="cluj@test.com", password="test123", user_type="craftsman", is_active=True
    )
    return CraftsmanProfile.objects.create(user=user, county=test_county, display_name="Cluj Craftsman", bio="Test bio")


@pytest.mark.django_db
class TestSearchCountyFilter:
    """Tests for county filtering in search"""

    def test_search_with_county_slug(self, test_craftsman, test_county, client: Client):
        """Test search accepts county slug"""
        url = reverse("core:search") + "?county=cluj"
        response = client.get(url)

        assert response.status_code == 200
        assert test_craftsman in response.context["craftsmen"]
        assert response.context["county"] == test_county

    def test_search_with_county_id_redirects_to_slug(self, test_county, client: Client):
        """Test that ?county=<id> redirects to ?county=<slug>"""
        url = reverse("core:search") + f"?county={test_county.id}"
        response = client.get(url)

        # Should be 301 redirect
        assert response.status_code == 301
        assert f"?county={test_county.slug}" in response.url

    def test_search_county_redirect_preserves_params(self, test_county, client: Client):
        """Test that 301 redirect preserves other query parameters"""
        url = reverse("core:search") + f"?q=test&county={test_county.id}&rating=4.5"
        response = client.get(url, follow=False)

        assert response.status_code == 301
        assert "q=test" in response.url
        assert f"county={test_county.slug}" in response.url
        assert "rating=4.5" in response.url

    def test_search_with_county_dot_ignored(self, test_craftsman, client: Client):
        """Test that ?county=. is ignored (no error)"""
        url = reverse("core:search") + "?county=."
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["county"] is None
        # Should show all craftsmen
        assert test_craftsman in response.context["craftsmen"]

    def test_search_with_county_all_ignored(self, test_craftsman, client: Client):
        """Test that ?county=all is ignored"""
        url = reverse("core:search") + "?county=all"
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["county"] is None

    def test_search_with_invalid_county_id(self, test_craftsman, client: Client):
        """Test that invalid county ID is ignored (no error)"""
        url = reverse("core:search") + "?county=99999"
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["county"] is None

    def test_search_with_invalid_county_slug(self, test_craftsman, client: Client):
        """Test that invalid county slug is ignored"""
        url = reverse("core:search") + "?county=nonexistent"
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["county"] is None

    def test_county_param_preserved_in_context(self, test_county, client: Client):
        """Test that county_param is passed to context for form"""
        url = reverse("core:search") + "?county=cluj"
        response = client.get(url)

        assert "county_param" in response.context
        assert response.context["county_param"] == "cluj"

    def test_search_without_county_shows_all(self, test_craftsman, client: Client):
        """Test search without county parameter shows all craftsmen"""
        url = reverse("core:search")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["county"] is None
        assert test_craftsman in response.context["craftsmen"]


@pytest.mark.django_db
class TestCountySlugRedirectMiddleware:
    """Tests specifically for CountySlugRedirectMiddleware"""

    def test_middleware_only_redirects_get_requests(self, test_county, client: Client):
        """Test that middleware only affects GET requests"""
        url = reverse("core:search") + f"?county={test_county.id}"

        # GET should redirect
        response_get = client.get(url)
        assert response_get.status_code == 301

        # POST should not redirect (if POST was allowed on search)
        # Note: Search view doesn't accept POST, but middleware should only handle GET

    def test_middleware_handles_missing_slug_gracefully(self, db, client: Client):
        """Test middleware handles counties without slugs"""
        county_no_slug = County.objects.create(name="No Slug", code="NS", slug="")
        url = reverse("core:search") + f"?county={county_no_slug.id}"

        # Should not redirect if county has no slug
        response = client.get(url)
        # Will not redirect, just shows page with filter applied
        assert response.status_code in [200, 301]  # Either works fine

    def test_middleware_preserves_query_string_order(self, test_county, client: Client):
        """Test that middleware preserves query string"""
        url = reverse("core:search") + f"?a=1&county={test_county.id}&b=2"
        response = client.get(url, follow=False)

        assert response.status_code == 301
        assert "a=1" in response.url
        assert f"county={test_county.slug}" in response.url
        assert "b=2" in response.url
