"""
Tests for contact info display and messaging functionality (Fix-Lot-1)
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from accounts.models import City, County, CraftsmanProfile
from messaging.models import Conversation, Message

User = get_user_model()


@pytest.fixture
def county(db):
    """Create test county"""
    return County.objects.create(name="București", code="B")


@pytest.fixture
def city(db, county):
    """Create test city"""
    return City.objects.create(name="Sector 1", county=county)


@pytest.fixture
def craftsman_user(db):
    """Create craftsman user"""
    return User.objects.create_user(
        username="test_craftsman", email="craftsman@test.com", password="testpass123", user_type="craftsman"
    )


@pytest.fixture
def craftsman(db, craftsman_user, county, city):
    """Create craftsman profile"""
    return CraftsmanProfile.objects.create(
        user=craftsman_user,
        display_name="Ion Popescu",
        slug="ion-popescu",
        county=county,
        city=city,
        coverage_radius_km=25,
        bio="Meșter profesionist cu 10 ani experiență",
        phone="+40722123456",
    )


@pytest.fixture
def client_user(db):
    """Create client user"""
    return User.objects.create_user(
        username="test_client", email="client@test.com", password="testpass123", user_type="client"
    )


@pytest.mark.django_db
class TestContactInfoDisplay:
    """Test contact info display in craftsman detail page"""

    def test_craftsman_email_displays_correctly(self, client, craftsman):
        """Email should show from craftsman.user.email, not craftsman.email"""
        response = client.get(reverse("accounts:craftsman_detail", kwargs={"slug": craftsman.slug}))
        assert response.status_code == 200

        # Check email is in response
        assert craftsman.user.email in response.content.decode()

        # Check mailto: link has email
        assert f"mailto:{craftsman.user.email}" in response.content.decode()

    def test_craftsman_phone_displays_when_set(self, client, craftsman):
        """Phone should display when set"""
        response = client.get(reverse("accounts:craftsman_detail", kwargs={"slug": craftsman.slug}))
        assert response.status_code == 200
        assert craftsman.phone in response.content.decode()
        assert f"tel:{craftsman.phone}" in response.content.decode()

    def test_contact_info_shows_location(self, client, craftsman):
        """Contact card should show city and county"""
        response = client.get(reverse("accounts:craftsman_detail", kwargs={"slug": craftsman.slug}))
        assert response.status_code == 200
        assert craftsman.city.name in response.content.decode()
        assert craftsman.county.name in response.content.decode()


@pytest.mark.django_db
class TestMessagingFlow:
    """Test messaging functionality"""

    def test_send_contact_message_creates_conversation(self, client: Client, client_user, craftsman):
        """Sending message should create conversation and message"""
        client.force_login(client_user)

        response = client.post(
            reverse("messaging:send_contact_message", kwargs={"craftsman_id": craftsman.id}),
            data={
                "subject": "Întrebare despre servicii",
                "message": "Aș dori să știu dacă faceți și renovări complete.",
            },
        )

        # Should redirect back
        assert response.status_code == 302

        # Conversation created
        assert Conversation.objects.count() == 1
        conversation = Conversation.objects.first()
        assert client_user in conversation.participants.all()
        assert craftsman.user in conversation.participants.all()

        # Message created
        assert Message.objects.count() == 1
        message = Message.objects.first()
        assert message.sender == client_user
        assert message.recipient == craftsman.user
        assert "renovări complete" in message.content

    def test_send_reply_in_existing_conversation(self, client: Client, client_user, craftsman):
        """Reply should add message to existing conversation"""
        # Login as craftsman to reply
        client.force_login(craftsman.user)

        # Create conversation first
        conversation = Conversation.objects.create()
        conversation.participants.add(client_user, craftsman.user)

        # Send initial message from client
        Message.objects.create(
            conversation=conversation, sender=client_user, recipient=craftsman.user, content="Mesaj inițial"
        )

        # Craftsman replies
        response = client.post(
            reverse("messaging:send_reply", kwargs={"conversation_id": conversation.id}),
            data={"message": "Răspuns de la meșter"},
        )

        assert response.status_code == 302
        assert Message.objects.count() == 2

        # Check reply message - should be from craftsman to client
        reply = Message.objects.filter(sender=craftsman.user).first()
        assert reply is not None, "Reply message from craftsman not found"
        assert reply.recipient == client_user
        assert "Răspuns de la meșter" in reply.content
