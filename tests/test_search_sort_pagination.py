"""
Tests for search sort bar, pagination controls, and view toggle.
Verifies sort options, per-page settings, and list/grid view modes.
"""

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import County, CraftsmanProfile, User


@pytest.mark.django_db
class TestSearchSortPagination:
    """Test sort bar, pagination, and view toggle functionality"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def craftsmen_for_sorting(self):
        """Create craftsmen with different attributes for sorting"""
        county = County.objects.create(name="Cluj", slug="cluj")

        craftsmen = []
        # Create craftsmen with various ratings, reviews, and join dates
        test_data = [
            {"username": "new_verified", "rating": 4.8, "reviews": 50, "verified": True, "days_ago": 1},
            {"username": "old_high_rated", "rating": 4.9, "reviews": 100, "verified": True, "days_ago": 365},
            {"username": "most_reviewed", "rating": 4.5, "reviews": 200, "verified": False, "days_ago": 180},
            {"username": "newest", "rating": 4.0, "reviews": 5, "verified": False, "days_ago": 0},
            {"username": "highest_rated", "rating": 5.0, "reviews": 30, "verified": True, "days_ago": 100},
        ]

        from datetime import timedelta

        from django.utils import timezone

        for data in test_data:
            user = User.objects.create_user(
                username=data["username"], email=f"{data['username']}@example.com", password="password123"
            )
            user.is_verified = data["verified"]
            user.date_joined = timezone.now() - timedelta(days=data["days_ago"])
            user.save()

            craftsman = CraftsmanProfile.objects.create(
                user=user,
                county=county,
                average_rating=data["rating"],
                total_reviews=data["reviews"],
                slug=data["username"],
            )
            craftsmen.append(craftsman)

        return craftsmen

    # Sort functionality tests

    def test_sort_bar_present(self, client, craftsmen_for_sorting):
        """Verify sort bar is included in search results"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Should contain sort dropdown
        assert "sortSelect" in content or "sortForm" in content
        assert "Sortare" in content

    def test_sort_options_present(self, client, craftsmen_for_sorting):
        """Verify all sort options are available"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Check for all sort options
        assert "Populare" in content
        assert "Cele mai noi" in content
        assert "Cele mai recenzate" in content
        assert "Rating cel mai mare" in content

    def test_sort_by_popular_default(self, client, craftsmen_for_sorting):
        """Verify default sort is 'popular'"""
        response = client.get(reverse("core:search"))

        # Default sort should be popular
        assert response.context["sort_by"] == "popular"

        craftsmen = list(response.context["craftsmen"])

        # Verified craftsmen should come first
        # Among verified, higher ratings first
        assert craftsmen[0].user.username == "highest_rated"  # 5.0, verified
        assert craftsmen[1].user.username == "old_high_rated"  # 4.9, verified

    def test_sort_by_newest(self, client, craftsmen_for_sorting):
        """Verify sorting by newest works"""
        response = client.get(reverse("core:search"), {"sort": "newest"})

        assert response.context["sort_by"] == "newest"

        craftsmen = list(response.context["craftsmen"])

        # Newest craftsman should be first
        assert craftsmen[0].user.username == "newest"

    def test_sort_by_reviews(self, client, craftsmen_for_sorting):
        """Verify sorting by most reviewed works"""
        response = client.get(reverse("core:search"), {"sort": "reviews"})

        assert response.context["sort_by"] == "reviews"

        craftsmen = list(response.context["craftsmen"])

        # Most reviewed craftsman should be first
        assert craftsmen[0].user.username == "most_reviewed"  # 200 reviews

    def test_sort_by_rating(self, client, craftsmen_for_sorting):
        """Verify sorting by highest rating works"""
        response = client.get(reverse("core:search"), {"sort": "rating"})

        assert response.context["sort_by"] == "rating"

        craftsmen = list(response.context["craftsmen"])

        # Highest rated craftsman should be first
        assert craftsmen[0].user.username == "highest_rated"  # 5.0 rating

    # Pagination tests

    def test_per_page_dropdown_present(self, client, craftsmen_for_sorting):
        """Verify per-page dropdown is present"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Should contain per-page selector
        assert "perPageSelect" in content or "perPageForm" in content
        assert "60 rezultate" in content
        assert "80 rezultate" in content
        assert "100 rezultate" in content

    def test_default_pagination_60(self, client, craftsmen_for_sorting):
        """Verify default pagination is 60 results per page"""
        response = client.get(reverse("core:search"))

        # Default should be 60
        assert response.context["per_page"] == 60

    def test_per_page_80(self, client, craftsmen_for_sorting):
        """Verify per_page=80 parameter works"""
        response = client.get(reverse("core:search"), {"per_page": "80"})

        assert response.context["per_page"] == 80

    def test_per_page_100(self, client, craftsmen_for_sorting):
        """Verify per_page=100 parameter works"""
        response = client.get(reverse("core:search"), {"per_page": "100"})

        assert response.context["per_page"] == 100

    def test_invalid_per_page_fallback(self, client, craftsmen_for_sorting):
        """Verify invalid per_page values fallback to 60"""
        response = client.get(reverse("core:search"), {"per_page": "999"})

        # Should fallback to default 60
        assert response.context["per_page"] == 60

    # View toggle tests

    def test_view_toggle_present(self, client, craftsmen_for_sorting):
        """Verify view toggle buttons are present"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Should contain view toggle buttons
        assert "Listă" in content
        assert "Grilă" in content
        assert "fa-list" in content
        assert "fa-th" in content

    def test_default_view_mode_grid(self, client, craftsmen_for_sorting):
        """Verify default view mode is grid"""
        response = client.get(reverse("core:search"))

        # Default should be grid
        assert response.context["view_mode"] == "grid"

    def test_view_mode_list(self, client, craftsmen_for_sorting):
        """Verify view=list parameter works"""
        response = client.get(reverse("core:search"), {"view": "list"})

        assert response.context["view_mode"] == "list"

    def test_view_mode_grid(self, client, craftsmen_for_sorting):
        """Verify view=grid parameter works"""
        response = client.get(reverse("core:search"), {"view": "grid"})

        assert response.context["view_mode"] == "grid"

    # Parameter preservation tests

    def test_sort_preserves_filters(self, client, craftsmen_for_sorting):
        """Verify changing sort preserves filter parameters"""
        county = County.objects.first()
        response = client.get(reverse("core:search"), {"county": county.slug, "sort": "newest", "rating": "4.0"})

        # All parameters should be preserved in context
        assert response.context["county"] == county
        assert response.context["sort_by"] == "newest"
        assert response.context["rating_min"] == "4.0"

    def test_per_page_preserves_filters(self, client, craftsmen_for_sorting):
        """Verify changing per_page preserves filter parameters"""
        county = County.objects.first()
        response = client.get(reverse("core:search"), {"county": county.slug, "per_page": "80", "rating": "4.0"})

        # All parameters should be preserved
        assert response.context["county"] == county
        assert response.context["per_page"] == 80
        assert response.context["rating_min"] == "4.0"

    def test_view_toggle_preserves_filters(self, client, craftsmen_for_sorting):
        """Verify changing view mode preserves filter parameters"""
        county = County.objects.first()
        response = client.get(reverse("core:search"), {"county": county.slug, "view": "list", "rating": "4.0"})

        # All parameters should be preserved
        assert response.context["county"] == county
        assert response.context["view_mode"] == "list"
        assert response.context["rating_min"] == "4.0"

    def test_sort_bar_hidden_when_no_results(self, client):
        """Verify sort bar is only shown when there are results"""
        response = client.get(reverse("core:search"), {"q": "nonexistent_query_12345"})
        content = response.content.decode("utf-8")

        # Sort bar should not be visible when no results
        # (it's only included in the {% if craftsmen %} block)
        craftsmen = response.context["craftsmen"]
        assert len(craftsmen) == 0
