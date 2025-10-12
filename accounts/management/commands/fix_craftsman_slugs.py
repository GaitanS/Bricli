"""
Management command to generate missing slugs for craftsmen profiles.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from accounts.models import CraftsmanProfile


class Command(BaseCommand):
    help = "Generates missing slugs for craftsmen profiles"

    def handle(self, *args, **options):
        # Find craftsmen without slugs
        craftsmen_without_slugs = CraftsmanProfile.objects.filter(slug__isnull=True) | CraftsmanProfile.objects.filter(slug='')

        count = craftsmen_without_slugs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("All craftsmen have slugs. Nothing to fix."))
            return

        self.stdout.write(f"Found {count} craftsmen without slugs. Generating...")

        fixed = 0
        for craftsman in craftsmen_without_slugs:
            # Try to generate slug from display_name or user name
            if craftsman.display_name:
                base_slug = slugify(craftsman.display_name)
            elif craftsman.user.first_name and craftsman.user.last_name:
                base_slug = slugify(f"{craftsman.user.first_name}-{craftsman.user.last_name}")
            else:
                base_slug = slugify(craftsman.user.username)

            # Ensure uniqueness
            slug = base_slug
            counter = 1
            while CraftsmanProfile.objects.filter(slug=slug).exclude(id=craftsman.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            craftsman.slug = slug
            craftsman.save(update_fields=['slug'])

            self.stdout.write(f"  [+] {craftsman.user.username}: slug={slug}")
            fixed += 1

        self.stdout.write(self.style.SUCCESS(f"\n[SUCCESS] Fixed {fixed} craftsmen profiles."))
