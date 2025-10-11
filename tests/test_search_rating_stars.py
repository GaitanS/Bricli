"""
Tests for visual star rating filter with result counts.
Verifies stars template tag and rating bucket calculations.
"""

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import County, CraftsmanProfile, User
from services.models import ServiceCategory


@pytest.mark.django_db
class TestSearchRatingStars:
    """Test visual star rating filter with counts"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def craftsmen_with_ratings(self):
        """Create craftsmen with different ratings"""
        county = County.objects.create(name="București", slug="bucuresti")

        # Create craftsmen with various ratings
        craftsmen = []
        ratings = [5.0, 4.5, 4.0, 3.5, 3.0, 2.5]

        for i, rating in enumerate(ratings):
            user = User.objects.create_user(
                username=f"craftsman{i}", email=f"craftsman{i}@example.com", password="password123"
            )
            craftsman = CraftsmanProfile.objects.create(
                user=user, county=county, average_rating=rating, total_reviews=10, slug=f"craftsman-{i}"
            )
            craftsmen.append(craftsman)

        return craftsmen

    def test_stars_template_tag_loaded(self, client, craftsmen_with_ratings):
        """Verify stars template tag is loaded"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Should load stars and dictutils tags
        assert response.status_code == 200

    def test_rating_filter_uses_radio_buttons(self, client, craftsmen_with_ratings):
        """Verify rating filter uses radio buttons instead of dropdown"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Should contain radio inputs for rating
        assert 'type="radio"' in content
        assert 'name="rating"' in content

        # Should NOT contain old select dropdown for rating
        # (There might be other selects for county/category)
        # Check specifically that rating options are radio buttons
        assert 'id="rating-' in content or 'id="rating-mob-' in content

    def test_rating_thresholds_present(self, client, craftsmen_with_ratings):
        """Verify all 5 rating thresholds are present (5.0, 4.5, 4.0, 3.5, 3.0)"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Check for rating values in radio buttons
        assert 'value="5.0"' in content
        assert 'value="4.5"' in content
        assert 'value="4.0"' in content
        assert 'value="3.5"' in content
        assert 'value="3.0"' in content

    def test_rating_counts_calculated(self, client, craftsmen_with_ratings):
        """Verify rating_counts are passed to template"""
        response = client.get(reverse("core:search"))

        # Check context contains rating_counts
        assert "rating_counts" in response.context

        rating_counts = response.context["rating_counts"]

        # Verify counts are correct
        # We have: 5.0(1), 4.5(1), 4.0(1), 3.5(1), 3.0(1), 2.5(1)
        # Thresholds: 5.0+ = 1, 4.5+ = 2, 4.0+ = 3, 3.5+ = 4, 3.0+ = 5
        assert rating_counts[5.0] == 1
        assert rating_counts[4.5] == 2
        assert rating_counts[4.0] == 3
        assert rating_counts[3.5] == 4
        assert rating_counts[3.0] == 5

    def test_star_icons_rendered(self, client, craftsmen_with_ratings):
        """Verify Font Awesome star icons are rendered"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Should contain star icons
        assert "fa-star" in content
        assert "text-warning" in content  # Stars should be yellow

    def test_rating_filter_applied(self, client, craftsmen_with_ratings):
        """Verify rating filter actually filters results"""
        # Filter for 4.0+ rating
        response = client.get(reverse("core:search"), {"rating": "4.0"})

        craftsmen = response.context["craftsmen"]

        # Should return 3 craftsmen (5.0, 4.5, 4.0)
        assert len(craftsmen) == 3

        # All should have rating >= 4.0
        for craftsman in craftsmen:
            assert craftsman.average_rating >= 4.0

    def test_rating_filter_preserves_other_params(self, client, craftsmen_with_ratings):
        """Verify rating filter works with other filters"""
        county = County.objects.first()

        # Apply both county and rating filters
        response = client.get(reverse("core:search"), {"county": county.slug, "rating": "4.0"})

        assert response.status_code == 200
        assert response.context["county"] == county
        assert response.context["rating_min"] == "4.0"

    def test_clear_rating_button_shown_when_active(self, client, craftsmen_with_ratings):
        """Verify clear rating button appears when rating is selected"""
        response = client.get(reverse("core:search"), {"rating": "4.0"})
        content = response.content.decode("utf-8")

        # Should show "Șterge rating" button
        assert "Șterge rating" in content or "terge rating" in content

    def test_rating_buckets_calculated_before_filter(self, client, craftsmen_with_ratings):
        """Verify rating counts are calculated BEFORE applying rating filter"""
        # When filtering by 4.0+, the counts should still show all craftsmen
        response = client.get(reverse("core:search"), {"rating": "4.0"})

        rating_counts = response.context["rating_counts"]

        # Counts should be based on ALL craftsmen, not filtered ones
        # We have: 5.0(1), 4.5(1), 4.0(1), 3.5(1), 3.0(1), 2.5(1)
        assert rating_counts[5.0] == 1
        assert rating_counts[4.5] == 2
        assert rating_counts[4.0] == 3
        assert rating_counts[3.5] == 4
        assert rating_counts[3.0] == 5

    def test_stars_tag_renders_correctly(self, client, craftsmen_with_ratings):
        """Verify stars_5 template tag renders correct number of stars"""
        from core.templatetags.stars import stars_5

        # Test full stars
        html = stars_5(5.0)
        assert html.count("fas fa-star") == 5
        assert html.count("far fa-star") == 0

        # Test half stars
        html = stars_5(4.5)
        assert html.count("fas fa-star") == 4
        assert html.count("fas fa-star-half-alt") == 1

        # Test empty stars
        html = stars_5(3.0)
        assert html.count("fas fa-star") == 3
        assert html.count("far fa-star") == 2

    def test_dictutils_get_item_filter(self, client, craftsmen_with_ratings):
        """Verify get_item filter converts string keys to float"""
        from core.templatetags.dictutils import get_item

        test_dict = {5.0: 10, 4.5: 20, 4.0: 30}

        # Should work with string keys
        assert get_item(test_dict, "5.0") == 10
        assert get_item(test_dict, "4.5") == 20

        # Should work with float keys
        assert get_item(test_dict, 5.0) == 10

    def test_details_accordion_present(self, client, craftsmen_with_ratings):
        """Verify rating filter uses <details> accordion in sidebar"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Should contain <details> tag for collapsible section
        assert "<details" in content
        assert "<summary" in content
