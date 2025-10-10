"""
Tests for registration choice screen (Pas 6)
"""

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestRegistrationChoice:
    def test_registration_choice_displays_options(self):
        """Registration choice page should display both Meșter and Client options"""
        client = Client()
        response = client.get("/inregistrare/")

        assert response.status_code == 200
        content = response.content.decode()

        # Check both options are displayed
        assert "Sunt Meșter" in content or "Sunt Mester" in content
        assert "Sunt Client" in content

        # Check links to registration forms
        assert 'href="/inregistrare/meserias/"' in content or "auth:craftsman_register" in content
        assert 'href="/inregistrare/client/"' in content or "auth:register" in content

    def test_reverse_url_works(self):
        """URL reverse should work for registration choice"""
        url = reverse("auth:registration_choice")
        assert url == "/inregistrare/"

    def test_meserias_register_link(self):
        """Meșter registration link should work"""
        url = reverse("auth:craftsman_register")
        assert url == "/inregistrare/meserias/"

    def test_client_register_link(self):
        """Client registration link should work"""
        url = reverse("auth:register")
        assert url == "/inregistrare/client/"
