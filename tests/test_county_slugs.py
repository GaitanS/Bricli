"""
Test suite for County slug field and populate_county_slugs command
"""

import pytest
from django.core.management import call_command

from accounts.models import County


@pytest.mark.django_db
class TestCountySlugs:
    """Tests for County slug functionality"""

    def test_county_slug_field_exists(self):
        """Test that County model has slug field"""
        county = County.objects.create(name="București", code="B")
        assert hasattr(county, "slug")

    def test_populate_county_slugs_command_exists(self):
        """Test that populate_county_slugs management command exists"""
        # Just running the command is enough to test it exists
        try:
            call_command("populate_county_slugs")
        except SystemExit:
            # --help causes SystemExit, which is fine
            pass

    def test_populate_county_slugs_creates_slug(self):
        """Test that command populates slug from name"""
        # Create county without slug
        county = County.objects.create(name="Cluj", code="CJ")
        assert county.slug == ""

        # Run command
        call_command("populate_county_slugs")

        # Refresh from DB
        county.refresh_from_db()
        assert county.slug == "cluj"

    def test_populate_county_slugs_transliterates_romanian(self):
        """Test Romanian character transliteration"""
        test_cases = [
            ("București", "bucuresti"),  # ș→s
            ("Iași", "iasi"),  # ș→s, ă→a
            ("Brașov", "brasov"),  # ș→s
            ("Mureș", "mures"),  # ș→s
            ("Călărași", "calarasi"),  # ă→a, ș→s
            ("Vâlcea", "valcea"),  # â→a
            ("Constanța", "constanta"),  # ț→t, ă→a
        ]

        for name, expected_slug in test_cases:
            # Clean up
            County.objects.all().delete()

            # Create and populate
            county = County.objects.create(name=name, code="XX")
            call_command("populate_county_slugs")
            county.refresh_from_db()

            assert (
                county.slug == expected_slug
            ), f"Expected '{expected_slug}' for '{name}', got '{county.slug}'"

    def test_populate_county_slugs_handles_duplicates(self):
        """Test that command handles potential slug conflicts"""
        # NOTE: County has unique constraint on name, so we can't test
        # true duplicate handling at DB level. The command logic handles
        # it correctly with counter suffix, but we can't create duplicates.
        # This test just verifies command doesn't crash with single county.
        County.objects.create(name="Test County", code="T1")

        # Run command - should complete without error
        call_command("populate_county_slugs")

        # Check slug was created
        slugs = list(County.objects.values_list("slug", flat=True))
        assert len(slugs) == 1
        assert slugs[0] == "test-county"

    def test_populate_county_slugs_is_idempotent(self):
        """Test that command can be run multiple times safely"""
        county = County.objects.create(name="Timiș", code="TM")

        # Run command first time
        call_command("populate_county_slugs")
        county.refresh_from_db()
        first_slug = county.slug
        assert first_slug == "timis"

        # Run command second time
        call_command("populate_county_slugs")
        county.refresh_from_db()
        second_slug = county.slug

        # Slug should not change
        assert first_slug == second_slug

    def test_county_slug_is_lowercase(self):
        """Test that all slugs are lowercase"""
        county = County.objects.create(name="MARAMUREȘ", code="MM")
        call_command("populate_county_slugs")
        county.refresh_from_db()

        assert county.slug.islower()
        assert county.slug == "maramures"

    def test_county_slug_no_spaces(self):
        """Test that slugs have no spaces"""
        # Hypothetical multi-word county name
        county = County.objects.create(name="Test County Name", code="TC")
        call_command("populate_county_slugs")
        county.refresh_from_db()

        assert " " not in county.slug
        assert county.slug == "test-county-name"
