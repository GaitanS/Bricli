"""
Unit tests for HomeView stats context.
Tests that the homepage displays accurate platform statistics.
"""

import pytest
from django.urls import reverse

from accounts.models import City, County, CraftsmanProfile, User
from services.models import Order, Review, Service, ServiceCategory


@pytest.mark.django_db
class TestHomeStats:
    """Test platform statistics displayed on homepage"""

    @pytest.fixture
    def setup_data(self, db):
        """Create test data for stats"""
        # Create verified active craftsmen
        for i in range(3):
            user = User.objects.create_user(
                username=f"craftsman{i}",
                email=f"craftsman{i}@test.com",
                password="testpass123",
                user_type="craftsman",
                is_verified=True,
                is_active=True,
            )
            CraftsmanProfile.objects.create(
                user=user, display_name=f"Active Craftsman {i}", slug=f"active-craftsman-{i}"
            )

        # Create inactive craftsman (should not be counted)
        inactive_user = User.objects.create_user(
            username="inactive",
            email="inactive@test.com",
            password="testpass123",
            user_type="craftsman",
            is_verified=True,
            is_active=False,
        )
        CraftsmanProfile.objects.create(user=inactive_user, display_name="Inactive Craftsman", slug="inactive-craftsman")

        # Create unverified craftsman (should not be counted)
        unverified_user = User.objects.create_user(
            username="unverified",
            email="unverified@test.com",
            password="testpass123",
            user_type="craftsman",
            is_verified=False,
            is_active=True,
        )
        CraftsmanProfile.objects.create(user=unverified_user, display_name="Unverified Craftsman", slug="unverified-craftsman")

        # Create completed orders
        client = User.objects.create_user(
            username="client", email="client@test.com", password="testpass123", user_type="client"
        )

        # Create required related objects for orders
        county = County.objects.create(name="Test County")
        city = City.objects.create(name="Test City", county=county)
        category = ServiceCategory.objects.create(name="Test Category", slug="test-category")
        service = Service.objects.create(name="Test Service", slug="test-service", category=category)

        for i in range(5):
            Order.objects.create(
                client=client,
                title=f"Project {i}",
                description="Test project",
                service=service,
                county=county,
                city=city,
                status="completed",
            )

        # Create non-completed orders (should not be counted)
        Order.objects.create(
            client=client, title="Draft", description="Test", service=service, county=county, city=city, status="draft"
        )
        Order.objects.create(
            client=client,
            title="Published",
            description="Test",
            service=service,
            county=county,
            city=city,
            status="published",
        )

        # Create reviews with ratings (one review per order - unique constraint)
        craftsman = CraftsmanProfile.objects.first()
        completed_orders = Order.objects.filter(status="completed")[:5]
        for idx, rating in enumerate([5, 4, 5, 3, 5]):
            Review.objects.create(
                craftsman=craftsman, client=client, rating=rating, comment="Great work", order=completed_orders[idx]
            )

    def test_stats_context_exists(self, client, setup_data):
        """Stats dictionary should be present in context"""
        response = client.get(reverse("core:home"))
        assert response.status_code == 200
        assert "stats" in response.context
        assert isinstance(response.context["stats"], dict)

    def test_active_craftsmen_count(self, client, setup_data):
        """Should count only verified and active craftsmen"""
        response = client.get(reverse("core:home"))
        assert response.context["stats"]["active_craftsmen"] == 3

    def test_avg_rating_calculation(self, client, setup_data):
        """Should calculate average rating from all reviews"""
        response = client.get(reverse("core:home"))
        # Ratings: 5, 4, 5, 3, 5 → avg = 4.4
        assert response.context["stats"]["avg_rating"] == 4.4

    def test_completed_projects_count(self, client, setup_data):
        """Should count only completed orders"""
        response = client.get(reverse("core:home"))
        assert response.context["stats"]["completed_projects"] == 5

    def test_stats_with_no_data(self, client):
        """Stats should handle empty database gracefully"""
        response = client.get(reverse("core:home"))
        assert response.context["stats"]["active_craftsmen"] == 0
        assert response.context["stats"]["avg_rating"] == 0
        assert response.context["stats"]["completed_projects"] == 0

    def test_stats_display_in_template(self, client, setup_data):
        """Stats should be visible in rendered HTML"""
        response = client.get(reverse("core:home"))
        content = response.content.decode()
        assert "Meșteri activi verificați" in content
        assert "Rating mediu meșteri" in content
        assert "Proiecte finalizate" in content
        # Verify stats section exists
        assert "Platform Statistics" in content or "bg-light" in content  # Stats section has bg-light class
