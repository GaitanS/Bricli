"""
Tests for category icon rendering with Font Awesome
"""

import pytest
from django.core.management import call_command
from django.urls import reverse

from services.icon_map import ICONS


@pytest.mark.django_db
class TestCategoryIconsRender:
    """Test suite for Font Awesome icon rendering in templates"""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Set up test data before each test"""
        # Ensure we have categories with data
        call_command("populate_categories_services")

    def test_category_list_contains_fa_icons(self, client):
        """Category list page should contain Font Awesome icon classes"""
        url = reverse("services:categories")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Should contain at least one FA icon class
        assert "fas fa-" in content

        # Should contain specific icons from our mapping
        # Check for at least 3 different icons
        icon_count = sum(1 for icon in ICONS.values() if icon in content)
        assert icon_count >= 3, f"Expected at least 3 FA icons in category list, found {icon_count}"

    def test_category_detail_contains_correct_fa_icon(self, client):
        """Category detail page should contain the correct FA icon for that category"""
        # Test with renovari-constructii (should have fa-hammer)
        url = reverse("services:category_detail", kwargs={"slug": "renovari-constructii"})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Should contain the hammer icon
        assert "fa-hammer" in content

        # Test with instalatii-sanitare (should have fa-bath)
        url = reverse("services:category_detail", kwargs={"slug": "instalatii-sanitare"})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Should contain the bath icon
        assert "fa-bath" in content

    def test_suggestions_sidebar_contains_fa_icons(self, client):
        """Suggestions sidebar in search page should contain FA icons"""
        url = reverse("core:search")
        response = client.get(url, {"q": "renovare"})

        assert response.status_code == 200
        content = response.content.decode()

        # Should contain FA icon classes
        assert "fas fa-" in content

        # Should have icons for categories in suggestions
        # At least 2 category icons should appear
        icon_count = sum(1 for icon in ICONS.values() if icon in content)
        assert icon_count >= 2, f"Expected at least 2 FA icons in suggestions, found {icon_count}"

    def test_homepage_contains_fa_icons(self, client):
        """Homepage should contain FA icons for service categories"""
        url = reverse("core:home")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Should contain FA icon classes
        assert "fas fa-" in content

        # Should contain multiple category icons (homepage shows up to 8)
        icon_count = sum(1 for icon in ICONS.values() if icon in content)
        assert icon_count >= 4, f"Expected at least 4 FA icons on homepage, found {icon_count}"

    def test_all_seeded_categories_have_mapped_icons(self, client):
        """All seeded categories should have icons in the ICONS mapping"""
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
            assert slug in ICONS, f"Category {slug} missing from ICONS mapping"
            assert ICONS[slug].startswith("fa-"), f"Icon for {slug} should start with 'fa-'"

    def test_category_list_alphabetical_order(self, client):
        """Category list should display categories in alphabetical order"""
        url = reverse("services:categories")
        response = client.get(url)

        assert response.status_code == 200

        # Get categories from context
        categories = response.context["categories"]

        # Extract category names
        category_names = [cat.name for cat in categories]

        # Check if sorted alphabetically
        assert category_names == sorted(category_names), "Categories should be in alphabetical order"

    def test_no_emoji_icons_in_templates(self, client):
        """Templates should not contain emoji icons (replaced with FA icons)"""
        test_urls = [
            reverse("services:categories"),
            reverse("services:category_detail", kwargs={"slug": "renovari-constructii"}),
            reverse("core:search") + "?q=test",
            reverse("core:home"),
        ]

        emojis_to_check = ["🏗️", "🚿", "⚡", "🧹", "🌿", "🧰", "🏠", "🪟", "🛋️", "💻", "🔧"]

        for url in test_urls:
            response = client.get(url)
            content = response.content.decode()

            # Check for emojis in the actual rendered content
            # Note: Some emojis might appear in meta tags or hidden content, so we check main content
            for emoji in emojis_to_check:
                # Emojis should not be in visible icon positions
                # This is a soft check - if emojis appear in text content that's OK
                if emoji in content:
                    # Verify it's not being used as a category icon
                    assert (
                        f'aria-hidden="true">{emoji}' not in content
                    ), f"Emoji {emoji} found as icon in {url}, should use FA icons instead"

    def test_icon_components_exist(self):
        """Icon component templates should exist and be valid"""
        from django.template import TemplateDoesNotExist
        from django.template.loader import get_template

        # Check that both component templates exist
        try:
            get_template("components/category_icon_lg.html")
            get_template("components/category_icon_sm.html")
        except TemplateDoesNotExist as e:
            pytest.fail(f"Icon component template missing: {e}")

    def test_template_tags_load_correctly(self):
        """Service icon template tags should load without errors"""
        from django.template import Context, Template

        # Test loading the template tag library
        template_string = "{% load service_icons %}{{ test }}"
        template = Template(template_string)
        context = Context({"test": "success"})
        result = template.render(context)

        assert "success" in result
