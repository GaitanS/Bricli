"""
Management command to find and optionally remove duplicate services
Usage: python manage.py check_duplicate_services [--remove]
"""

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Count

from services.models import Service


class Command(BaseCommand):
    help = "Find and optionally remove duplicate services within the same category"

    def add_arguments(self, parser):
        parser.add_argument(
            "--remove",
            action="store_true",
            help="Remove duplicate services, keeping the oldest one",
        )

    def handle(self, *args, **options):
        remove = options.get("remove", False)

        # Find services with duplicate names in the same category
        duplicates_found = False

        # Group services by category and name
        services_by_cat_name = defaultdict(list)

        for service in Service.objects.all().order_by("category", "name", "id"):
            key = (service.category_id, service.name.lower().strip())
            services_by_cat_name[key].append(service)

        # Process duplicates
        for (cat_id, name), services in services_by_cat_name.items():
            if len(services) > 1:
                duplicates_found = True
                category_name = services[0].category.name

                self.stdout.write(
                    self.style.WARNING(
                        f'\nDuplicate found: "{services[0].name}" in category "{category_name}" ({len(services)} instances)'
                    )
                )

                for i, service in enumerate(services):
                    marker = "KEEP" if i == 0 else "REMOVE" if remove else "DUPLICATE"
                    self.stdout.write(
                        f"  [{marker}] ID: {service.id}, Slug: {service.slug}, "
                        f"Popular: {service.is_popular}, Active: {service.is_active}"
                    )

                if remove and len(services) > 1:
                    # Keep the first one (oldest), delete the rest
                    keep = services[0]
                    to_delete = services[1:]

                    for service in to_delete:
                        service.delete()
                        self.stdout.write(self.style.SUCCESS(f"    [OK] Deleted duplicate ID: {service.id}"))

        if not duplicates_found:
            self.stdout.write(self.style.SUCCESS("[OK] No duplicate services found!"))
        elif remove:
            self.stdout.write(self.style.SUCCESS("\n[OK] Duplicate services removed successfully!"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\n[INFO] Run with --remove flag to delete duplicates (keeping the oldest entry for each)"
                )
            )
