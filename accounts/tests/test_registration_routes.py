"""
Regression tests for registration routes and aliases
Ensures backward compatibility and canonical route names work correctly
"""

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestRegistrationRoutes:
    """Test registration route naming and aliases"""

    def test_canonical_craftsman_register_reverse(self):
        """Canonical name auth:craftsman_register should resolve correctly"""
        url = reverse("auth:craftsman_register")
        assert url == "/inregistrare/meserias/"

    def test_alias_simple_craftsman_register_reverse(self):
        """Backward compat alias auth:simple_craftsman_register should work"""
        url = reverse("auth:simple_craftsman_register")
        assert url == "/inregistrare/meserias/"

    def test_canonical_register_reverse(self):
        """Canonical name auth:register should resolve correctly"""
        url = reverse("auth:register")
        assert url == "/inregistrare/client/"

    def test_alias_simple_register_reverse(self):
        """Backward compat alias auth:simple_register should work"""
        url = reverse("auth:simple_register")
        assert url == "/inregistrare/client/"

    def test_registration_choice_contains_canonical_links(self):
        """Registration choice page should link to canonical routes"""
        client = Client()
        response = client.get("/inregistrare/")
        assert response.status_code == 200

        content = response.content.decode()
        # Should contain links to craftsman and client registration
        assert "/inregistrare/meserias/" in content or "auth:craftsman_register" in content
        assert "/inregistrare/client/" in content or "auth:register" in content

    def test_craftsman_register_page_loads(self):
        """Craftsman registration page should load successfully"""
        client = Client()
        response = client.get("/inregistrare/meserias/")
        assert response.status_code == 200
        # Should contain form
        content = response.content.decode()
        assert "form" in content.lower() or "înregistrare" in content.lower()

    def test_client_register_page_loads(self):
        """Client registration page should load successfully"""
        client = Client()
        response = client.get("/inregistrare/client/")
        assert response.status_code == 200
        # Should contain form
        content = response.content.decode()
        assert "form" in content.lower() or "înregistrare" in content.lower()

    def test_both_aliases_point_to_same_view(self):
        """Canonical and alias names should point to the same URL"""
        canonical_craftsman = reverse("auth:craftsman_register")
        alias_craftsman = reverse("auth:simple_craftsman_register")
        assert canonical_craftsman == alias_craftsman

        canonical_client = reverse("auth:register")
        alias_client = reverse("auth:simple_register")
        assert canonical_client == alias_client

    def test_registration_choice_page(self):
        """Registration choice page should display both options"""
        client = Client()
        response = client.get(reverse("auth:registration_choice"))
        assert response.status_code == 200

        content = response.content.decode()
        # Should show both meșter and client options
        assert "Meșter" in content or "Mester" in content
        assert "Client" in content
