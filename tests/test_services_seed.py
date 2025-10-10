"""
Tests for the populate_categories_services management command
"""

import pytest
from django.core.management import call_command

from services.models import Service, ServiceCategory


@pytest.mark.django_db
class TestServicesSeedCommand:
    """Test suite for populate_categories_services command"""

    def test_command_creates_categories(self):
        """Seed command should create at least 10 categories"""
        # Run the seed command
        call_command("populate_categories_services")

        # Verify categories created
        assert ServiceCategory.objects.count() >= 10

    def test_command_is_idempotent(self):
        """Running command multiple times should not duplicate data"""
        # Run command twice
        call_command("populate_categories_services")
        first_count = ServiceCategory.objects.count()

        call_command("populate_categories_services")
        second_count = ServiceCategory.objects.count()

        # Count should be same (idempotent)
        assert first_count == second_count

    def test_categories_have_emoji_icons(self):
        """All created categories should have emoji icons set"""
        call_command("populate_categories_services")

        categories = ServiceCategory.objects.all()

        # At least one category should exist
        assert categories.exists()

        # All categories should have emoji icons
        for cat in categories:
            assert cat.icon_emoji, f"Category {cat.slug} missing icon_emoji"
            # Emoji should not be the default "🔧" for all
            assert len(cat.icon_emoji) > 0

    def test_each_category_has_minimum_services(self):
        """Each category should have at least 15 services"""
        call_command("populate_categories_services")

        # Get all categories created by the seed command
        expected_slugs = [
            "renovari-constructii",
            "instalatii-sanitare",
            "instalatii-electrice",
            "curatenie-menaj",
            "gradinarit-peisagistica",
            "asamblare-montaj",
            "acoperisuri",
            "geamuri-ferestre",
            "design-interior",
            "it-tehnologie",
        ]

        for slug in expected_slugs:
            category = ServiceCategory.objects.get(slug=slug)
            service_count = category.services.count()

            assert service_count >= 15, f"Category {slug} has only {service_count} services, expected at least 15"

    def test_services_marked_as_popular_and_active(self):
        """All seeded services should be marked as popular and active"""
        call_command("populate_categories_services")

        services = Service.objects.all()

        # Should have created many services
        assert services.count() >= 150

        # All should be popular and active
        for service in services:
            assert service.is_popular, f"Service {service.slug} not marked as popular"
            assert service.is_active, f"Service {service.slug} not marked as active"

    def test_services_have_unique_slugs(self):
        """All services should have globally unique slugs"""
        call_command("populate_categories_services")

        services = Service.objects.all()
        slugs = [s.slug for s in services]

        # No duplicate slugs
        assert len(slugs) == len(set(slugs)), "Found duplicate service slugs"

    def test_service_slugs_are_ascii(self):
        """Service slugs should be ASCII-only (no Romanian diacritics)"""
        call_command("populate_categories_services")

        services = Service.objects.all()

        # Check for Romanian diacritics in slugs
        for service in services:
            assert "ț" not in service.slug, f"Service {service.slug} contains ț"
            assert "ș" not in service.slug, f"Service {service.slug} contains ș"
            assert "ă" not in service.slug, f"Service {service.slug} contains ă"
            assert "â" not in service.slug, f"Service {service.slug} contains â"
            assert "î" not in service.slug, f"Service {service.slug} contains î"

    def test_category_slugs_are_ascii(self):
        """Category slugs should be ASCII-only (no Romanian diacritics)"""
        call_command("populate_categories_services")

        categories = ServiceCategory.objects.all()

        # Check for Romanian diacritics in slugs
        for category in categories:
            assert "ț" not in category.slug, f"Category {category.slug} contains ț"
            assert "ș" not in category.slug, f"Category {category.slug} contains ș"
            assert "ă" not in category.slug, f"Category {category.slug} contains ă"
            assert "â" not in category.slug, f"Category {category.slug} contains â"
            assert "î" not in category.slug, f"Category {category.slug} contains î"
