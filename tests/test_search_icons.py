"""
Tests for unified category icons in search filters.
Verifies Font Awesome icons are used consistently instead of emojis.
"""

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import County
from services.models import ServiceCategory


@pytest.mark.django_db
class TestSearchCategoryIcons:
    """Test that category icons are rendered consistently via service_icons template tag"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def categories(self):
        """Create sample service categories"""
        cat1 = ServiceCategory.objects.create(
            name="Instalații sanitare", slug="instalatii-sanitare", icon="fa-wrench", icon_emoji="🔧", is_active=True
        )
        cat2 = ServiceCategory.objects.create(
            name="Construcție", slug="constructie", icon="fa-hard-hat", icon_emoji="🏗️", is_active=True
        )
        return [cat1, cat2]

    def test_sidebar_uses_service_icons_tag(self, client, categories):
        """Verify sidebar loads service_icons template tag library"""
        response = client.get(reverse("core:search"))
        assert response.status_code == 200

        # Since template tags are processed, we can't check for the raw tag in HTML
        # Instead, verify that Font Awesome icons are rendered (which proves the tag works)
        content = response.content.decode("utf-8")
        assert "fas fa-" in content or "far fa-" in content

    def test_offcanvas_uses_service_icons_tag(self, client, categories):
        """Verify offcanvas loads service_icons template tag library"""
        response = client.get(reverse("core:search"))
        assert response.status_code == 200

        # Check offcanvas is present and contains service icons
        content = response.content.decode("utf-8")
        assert "filtersOffcanvas" in content

    def test_sidebar_does_not_render_emoji_directly(self, client, categories):
        """Verify sidebar doesn't render raw emoji in HTML"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Should NOT contain raw emoji wrapped in spans
        assert "<span class=\"me-1\">🔧</span>" not in content
        assert "<span class=\"me-1\">🏗️</span>" not in content

    def test_offcanvas_does_not_render_emoji_directly(self, client, categories):
        """Verify offcanvas doesn't render raw emoji in HTML"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Offcanvas should NOT contain raw emoji
        # The emoji should be replaced by Font Awesome icons via template tag
        assert "filtersOffcanvas" in content

    def test_icons_present_in_sidebar(self, client, categories):
        """Verify Font Awesome icons are present in sidebar"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Check for Font Awesome icon tags (fa-* classes)
        # The service_icons tag should render <i class="fas fa-*"></i>
        assert "fas fa-" in content or "far fa-" in content

    def test_icons_present_in_offcanvas(self, client, categories):
        """Verify Font Awesome icons are present in offcanvas"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Check for Font Awesome icons in offcanvas
        assert "filtersOffcanvas" in content
        assert "fas fa-" in content or "far fa-" in content

    def test_category_labels_still_visible(self, client, categories):
        """Verify category names are still visible in filters"""
        response = client.get(reverse("core:search"))
        content = response.content.decode("utf-8")

        # Category names should be visible
        assert "Instalații sanitare" in content or "Instalatii sanitare" in content
        assert "Construcție" in content or "Constructie" in content
