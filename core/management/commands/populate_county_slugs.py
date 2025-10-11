"""
Management command to populate County slugs from names (idempotent)
Usage: python manage.py populate_county_slugs
"""

import unicodedata

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from accounts.models import County


class Command(BaseCommand):
    help = "Populate County.slug field from names with Romanian transliteration (idempotent)"

    def normalize_slug(self, text):
        """
        Transliterate Romanian characters to ASCII and create slug
        ț/Ț → t, ș/Ș → s, ă/Ă → a, â/Â/î/Î → i → a
        """
        # Romanian-specific replacements
        replacements = {
            "ț": "t",
            "Ț": "t",
            "ș": "s",
            "Ș": "s",
            "ă": "a",
            "Ă": "a",
            "â": "a",
            "Â": "a",
            "î": "i",
            "Î": "i",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Remove other diacritics and create slug
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

        return slugify(text)

    def handle(self, *args, **options):
        counties = County.objects.all()
        updated_count = 0
        skipped_count = 0

        for county in counties:
            # Skip if slug already exists
            if county.slug:
                skipped_count += 1
                self.stdout.write(f"[-] Skipped: {county.name} (slug already exists: {county.slug})")
                continue

            # Generate base slug from name
            base_slug = self.normalize_slug(county.name)
            slug = base_slug
            counter = 1

            # Handle duplicates by appending -1, -2, etc.
            while County.objects.filter(slug=slug).exclude(pk=county.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Update county
            county.slug = slug
            county.save(update_fields=["slug"])
            updated_count += 1
            self.stdout.write(self.style.SUCCESS(f"[+] Updated: {county.name} → {slug}"))

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Updated: {updated_count}, Skipped: {skipped_count}, Total: {County.objects.count()}"
            )
        )
