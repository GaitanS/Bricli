"""
Management command to backfill missing slugs for craftsmen profiles
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from accounts.models import CraftsmanProfile


class Command(BaseCommand):
    help = "Completează slugurile lipsă pentru meșteri"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Simulează operația fără a salva modificările în baza de date"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        # Import helper here to avoid circular imports
        from accounts.views import ensure_craftsman_slug

        # Find craftsmen without slugs
        craftsmen_without_slugs = CraftsmanProfile.objects.filter(Q(slug__isnull=True) | Q(slug=""))

        total_count = craftsmen_without_slugs.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("✓ Toți meșterii au sluguri valide!"))
            return

        self.stdout.write(f"Găsite {total_count} profile fără slug...")

        if dry_run:
            self.stdout.write(self.style.WARNING("MODE DRY-RUN - nicio modificare nu va fi salvată"))
            for craftsman in craftsmen_without_slugs:
                self.stdout.write(
                    f"  - ID {craftsman.pk}: {craftsman.display_name or craftsman.user.username} "
                    f"(ar primi slug: {craftsman.generate_slug()})"
                )
            return

        # Generate slugs for all craftsmen without them
        updated_count = 0
        for craftsman in craftsmen_without_slugs:
            try:
                old_slug = craftsman.slug
                ensure_craftsman_slug(craftsman)
                updated_count += 1
                self.stdout.write(
                    f"  ✓ ID {craftsman.pk}: "
                    f"{craftsman.display_name or craftsman.user.username} → slug: {craftsman.slug}"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Eroare la ID {craftsman.pk}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Completare finalizată: {updated_count}/{total_count} sluguri generate")
        )
