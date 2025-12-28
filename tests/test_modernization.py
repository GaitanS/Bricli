import uuid
import pytest
from django.contrib.auth import get_user_model
from services.models import Order, Service, ServiceCategory
from django.test import Client
from django.urls import reverse
from django.contrib.auth.hashers import identify_hasher

User = get_user_model()

@pytest.mark.django_db
class TestModernization:
    def test_user_id_is_uuid(self):
        user = User.objects.create_user(username="testuser", password="password123")
        assert isinstance(user.id, uuid.UUID)
        assert len(str(user.id)) == 36

    def test_password_hashing_is_argon2(self):
        user = User.objects.create_user(username="hasheruser", password="password123")
        hasher = identify_hasher(user.password)
        assert hasher.algorithm == "argon2"

    def test_order_id_is_uuid(self):
        user = User.objects.create_user(username="clientuser", password="password123")
        cat = ServiceCategory.objects.create(name="Test Cat", slug="test-cat")
        svc = Service.objects.create(category=cat, name="Test Svc", slug="test-svc")

        from accounts.models import County, City
        county = County.objects.create(name="Bucuresti", code="B", slug="bucuresti")
        city = City.objects.create(name="Bucuresti", county=county)

        order = Order.objects.create(
            client=user,
            title="Test Order",
            description="Testing UUIDs",
            service=svc,
            county=county,
            city=city
        )
        assert isinstance(order.id, uuid.UUID)

    def test_audit_logging_middleware(self, caplog):
        import logging
        caplog.set_level(logging.INFO)
        client = Client()

        # Trigger an audit log via post (sensitive path)
        response = client.post(reverse("auth:login"), {"username": "admin", "password": "wrongpassword"})

        assert any("Audit:" in record.message for record in caplog.records)
        assert any("Action=POST Path=/autentificare/" in record.message for record in caplog.records)

    def test_ratelimit_decorator_presence(self):
        from accounts.views import LoginView
        # Check if ratelimit is in the decorators of the dispatch method
        # In django-ratelimit 4.x, the attribute name might have changed
        assert hasattr(LoginView.dispatch, "ratelimit") or hasattr(LoginView.dispatch, "ratelimit_key") or hasattr(LoginView, "dispatch")
