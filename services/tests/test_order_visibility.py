"""
Test suite for order visibility and counter calculations.

Tests verify:
1. AvailableOrdersView correctly excludes direct requests
2. Counter calculations use q_active() and q_completed() properly
3. Craftsmen see public orders but not direct requests to other craftsmen
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

from services.models import Order, Quote, Service, CraftsmanService
from services.querydefs import q_active, q_completed
from accounts.models import CraftsmanProfile, County, City

User = get_user_model()


@pytest.fixture
def county():
    """Create a test county"""
    county, _ = County.objects.get_or_create(name="Brasov", defaults={"slug": "brasov"})
    return county


@pytest.fixture
def city(county):
    """Create a test city"""
    city, _ = City.objects.get_or_create(
        name="Brasov",
        county=county,
        defaults={"slug": "brasov"}
    )
    return city


@pytest.fixture
def service():
    """Create a test service"""
    from services.models import ServiceCategory

    category, _ = ServiceCategory.objects.get_or_create(
        name="Test Category",
        defaults={"slug": "test-category"}
    )

    service, _ = Service.objects.get_or_create(
        name="Test Service",
        category=category,
        defaults={"slug": "test-service"}
    )
    return service


@pytest.fixture
def client_user(db):
    """Create a test client user"""
    user, _ = User.objects.get_or_create(
        username="test_client",
        defaults={
            "email": "client@test.com",
            "user_type": "client",
            "first_name": "Test",
            "last_name": "Client"
        }
    )
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def craftsman_user(db, county, city):
    """Create a test craftsman user with profile"""
    user, _ = User.objects.get_or_create(
        username="test_craftsman",
        defaults={
            "email": "craftsman@test.com",
            "user_type": "craftsman",
            "first_name": "Test",
            "last_name": "Craftsman"
        }
    )
    user.set_password("testpass123")
    user.save()

    profile, _ = CraftsmanProfile.objects.get_or_create(
        user=user,
        defaults={
            "display_name": "Test Craftsman",
            "county": county,
            "city": city,
            "bio": "Test bio " * 50,  # 200+ chars for can_bid_on_jobs
        }
    )

    return user


@pytest.fixture
def other_craftsman_user(db, county, city):
    """Create another craftsman user for testing direct orders"""
    user, _ = User.objects.get_or_create(
        username="other_craftsman",
        defaults={
            "email": "other@test.com",
            "user_type": "craftsman",
            "first_name": "Other",
            "last_name": "Craftsman"
        }
    )
    user.set_password("testpass123")
    user.save()

    profile, _ = CraftsmanProfile.objects.get_or_create(
        user=user,
        defaults={
            "display_name": "Other Craftsman",
            "county": county,
            "city": city,
            "bio": "Test bio " * 50,
        }
    )

    return user


@pytest.mark.django_db
class TestOrderVisibility:
    """Test order visibility across different views"""

    def test_available_orders_excludes_direct_requests(
        self, client_user, craftsman_user, other_craftsman_user, service, county, city
    ):
        """Direct orders (assigned_craftsman set) should not appear in AvailableOrdersView"""
        # Register service for craftsman
        CraftsmanService.objects.get_or_create(
            craftsman=craftsman_user.craftsman_profile,
            service=service
        )

        # Create public order (no assigned_craftsman)
        public_order = Order.objects.create(
            client=client_user,
            title="Public Order - Everyone Can See",
            description="This is a public order available to all craftsmen",
            status="published",
            assigned_craftsman=None,
            service=service,
            county=county,
            city=city
        )

        # Create direct order to OTHER craftsman
        direct_order = Order.objects.create(
            client=client_user,
            title="Direct Order - Only for Other Craftsman",
            description="This order is directly assigned",
            status="published",
            assigned_craftsman=other_craftsman_user.craftsman_profile,
            service=service,
            county=county,
            city=city
        )

        # Login as craftsman
        client = Client()
        client.login(username="test_craftsman", password="testpass123")

        # GET /servicii/comenzi-disponibile/
        response = client.get(reverse("services:available_orders"))

        assert response.status_code == 200
        orders_in_response = response.context["orders"]

        # Assert public_order IS in response
        assert public_order in orders_in_response, "Public order should appear in available orders"

        # Assert direct_order is NOT in response
        assert direct_order not in orders_in_response, "Direct order should NOT appear in available orders"

    def test_counters_client_two_published_orders(self, client_user, service, county, city):
        """Two published orders should appear in active count, not completed"""
        # Create 2 published orders
        order1 = Order.objects.create(
            client=client_user,
            title="Order 1",
            description="First order",
            status="published",
            service=service,
            county=county,
            city=city
        )

        order2 = Order.objects.create(
            client=client_user,
            title="Order 2",
            description="Second order",
            status="published",
            service=service,
            county=county,
            city=city
        )

        # Test using querydefs
        active_count = client_user.orders.filter(q_active()).count()
        completed_count = client_user.orders.filter(q_completed()).count()

        assert active_count == 2, f"Expected 2 active orders, got {active_count}"
        assert completed_count == 0, f"Expected 0 completed orders, got {completed_count}"

    def test_counters_mixed_statuses(self, client_user, service, county, city):
        """Test counters with mixed order statuses"""
        # Create orders with different statuses
        Order.objects.create(
            client=client_user,
            title="Published Order",
            status="published",
            service=service,
            county=county,
            city=city
        )

        Order.objects.create(
            client=client_user,
            title="In Progress Order",
            status="in_progress",
            service=service,
            county=county,
            city=city
        )

        Order.objects.create(
            client=client_user,
            title="Completed Order",
            status="completed",
            service=service,
            county=county,
            city=city
        )

        Order.objects.create(
            client=client_user,
            title="Cancelled Order",
            status="cancelled",
            service=service,
            county=county,
            city=city
        )

        # Test counters
        active_count = client_user.orders.filter(q_active()).count()
        completed_count = client_user.orders.filter(q_completed()).count()
        total_count = client_user.orders.count()

        assert total_count == 4, f"Expected 4 total orders, got {total_count}"
        assert active_count == 2, f"Expected 2 active orders (published + in_progress), got {active_count}"
        assert completed_count == 1, f"Expected 1 completed order, got {completed_count}"

    def test_craftsman_sees_public_orders_not_direct_to_others(
        self, client_user, craftsman_user, other_craftsman_user, service, county, city
    ):
        """Craftsman should see public orders but not direct orders for other craftsmen"""
        # Register service for craftsman
        CraftsmanService.objects.get_or_create(
            craftsman=craftsman_user.craftsman_profile,
            service=service
        )

        # Create public order
        public_order = Order.objects.create(
            client=client_user,
            title="Public Order",
            description="Available to all",
            status="published",
            assigned_craftsman=None,
            service=service,
            county=county,
            city=city
        )

        # Create direct order to OTHER craftsman
        direct_to_other = Order.objects.create(
            client=client_user,
            title="Direct to Other",
            description="Only for other craftsman",
            status="published",
            assigned_craftsman=other_craftsman_user.craftsman_profile,
            service=service,
            county=county,
            city=city
        )

        # Create direct order to THIS craftsman
        direct_to_self = Order.objects.create(
            client=client_user,
            title="Direct to Me",
            description="Assigned to test_craftsman",
            status="published",
            assigned_craftsman=craftsman_user.craftsman_profile,
            service=service,
            county=county,
            city=city
        )

        # Login as craftsman
        client = Client()
        client.login(username="test_craftsman", password="testpass123")

        # GET available orders
        response = client.get(reverse("services:available_orders"))
        assert response.status_code == 200

        available_orders = list(response.context["orders"])

        # Assertions
        assert public_order in available_orders, "Public order should be visible"
        assert direct_to_other not in available_orders, "Direct order to OTHER craftsman should NOT be visible"
        assert direct_to_self not in available_orders, "Direct order to SELF should NOT be in available orders (it's direct)"

    def test_craftsman_cannot_see_order_without_registered_service(
        self, client_user, craftsman_user, service, county, city
    ):
        """Craftsman should not see orders for services they haven't registered"""
        # Create another service
        from services.models import ServiceCategory

        category, _ = ServiceCategory.objects.get_or_create(
            name="Other Category",
            defaults={"slug": "other-category"}
        )

        other_service, _ = Service.objects.get_or_create(
            name="Other Service",
            category=category,
            defaults={"slug": "other-service"}
        )

        # DON'T register this service for craftsman

        # Create order with unregistered service
        order = Order.objects.create(
            client=client_user,
            title="Order with Unregistered Service",
            description="Craftsman hasn't registered for this service",
            status="published",
            service=other_service,
            county=county,
            city=city
        )

        # Login as craftsman
        client = Client()
        client.login(username="test_craftsman", password="testpass123")

        # GET available orders
        response = client.get(reverse("services:available_orders"))
        assert response.status_code == 200

        available_orders = list(response.context["orders"])

        assert order not in available_orders, "Order with unregistered service should NOT be visible"

    def test_craftsman_cannot_see_order_already_quoted_on(
        self, client_user, craftsman_user, service, county, city
    ):
        """Craftsman should not see orders they've already quoted on"""
        # Register service
        CraftsmanService.objects.get_or_create(
            craftsman=craftsman_user.craftsman_profile,
            service=service
        )

        # Create order
        order = Order.objects.create(
            client=client_user,
            title="Order Already Quoted",
            description="Craftsman already sent a quote",
            status="published",
            service=service,
            county=county,
            city=city
        )

        # Create quote from craftsman
        Quote.objects.create(
            order=order,
            craftsman=craftsman_user.craftsman_profile,
            price=1000,
            description="My quote",
            estimated_duration="2 days",
            expires_at="2025-12-31"
        )

        # Login as craftsman
        client = Client()
        client.login(username="test_craftsman", password="testpass123")

        # GET available orders
        response = client.get(reverse("services:available_orders"))
        assert response.status_code == 200

        available_orders = list(response.context["orders"])

        assert order not in available_orders, "Order already quoted on should NOT be visible"


@pytest.mark.django_db
class TestOrderDetailCounters:
    """Test counter display in OrderDetailView"""

    def test_counters_in_order_detail_view(self, client_user, service, county, city):
        """Test that OrderDetailView context contains correct counter values"""
        # Create orders with different statuses
        order1 = Order.objects.create(
            client=client_user,
            title="Published Order",
            status="published",
            service=service,
            county=county,
            city=city
        )

        Order.objects.create(
            client=client_user,
            title="In Progress Order",
            status="in_progress",
            service=service,
            county=county,
            city=city
        )

        Order.objects.create(
            client=client_user,
            title="Completed Order",
            status="completed",
            service=service,
            county=county,
            city=city
        )

        # Login as client
        client = Client()
        client.login(username="test_client", password="testpass123")

        # GET order detail view
        response = client.get(reverse("services:order_detail", kwargs={"pk": order1.pk}))
        assert response.status_code == 200

        # Check context variables
        assert "active_orders_count" in response.context, "active_orders_count missing from context"
        assert "completed_orders_count" in response.context, "completed_orders_count missing from context"

        # Check values
        assert response.context["active_orders_count"] == 2, "Expected 2 active orders"
        assert response.context["completed_orders_count"] == 1, "Expected 1 completed order"
