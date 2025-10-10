"""
Tests for service categories page (Pas 5)
"""

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from services.models import ServiceCategory


@pytest.mark.django_db
class TestCategoriesPage:
    def test_categories_page_displays_content(self):
        """Categories page should display seeded categories"""
        # Populate categories
        call_command("populate_categories")

        # Test page loads
        client = Client()
        response = client.get("/servicii/categorii/")
        assert response.status_code == 200

        # Check some categories are displayed
        content = response.content.decode()
        assert "Construcții" in content or "constructii" in content.lower()
        assert "Instalații" in content or "instalatii" in content.lower()

    def test_categories_command_is_idempotent(self):
        """Running populate_categories twice should not duplicate"""
        call_command("populate_categories")
        count_first = ServiceCategory.objects.count()

        call_command("populate_categories")
        count_second = ServiceCategory.objects.count()

        assert count_first == count_second
        assert count_first >= 8  # We have 8 categories in seed

    def test_reverse_url_works(self):
        """URL reverse should work for categories"""
        url = reverse("services:categories")
        assert url == "/servicii/categorii/"
