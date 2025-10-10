"""
Management command to populate ServiceCategory with initial data (idempotent)
Usage: python manage.py populate_categories
"""

from django.core.management.base import BaseCommand
from services.models import ServiceCategory


class Command(BaseCommand):
    help = "Populate ServiceCategory model with initial categories (idempotent)"

    # Categories with ASCII slugs (no diacritics)
    CATEGORIES = [
        ("constructii", "Construcții", "🏗️", "Lucrări de construcții, fundații, zidărie"),
        ("instalatii", "Instalații", "🔧", "Instalații sanitare, termice, gaze"),
        ("finisaje", "Finisaje", "🎨", "Zugravit, vopsit, tapet, finisaje interioare"),
        ("renovari", "Renovări", "🔨", "Renovări complete, modernizări"),
        ("electricitate", "Electricitate", "⚡", "Instalații electrice, tablouri, prize"),
        ("sanitare", "Sanitare", "🚿", "Instalații sanitare, obiecte sanitare"),
        ("tamplarie", "Tâmplărie", "🪚", "Tâmplărie lemn, PVC, ferestre, uși"),
        ("amenajari", "Amenajări", "🏡", "Amenajări interioare și exterioare"),
    ]

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for slug, name, icon, description in self.CATEGORIES:
            category, created = ServiceCategory.objects.get_or_create(
                slug=slug, defaults={"name": name, "icon": icon, "description": description}
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"[+] Created: {slug}"))
            else:
                # Update existing if needed
                if category.name != name or category.icon != icon or category.description != description:
                    category.name = name
                    category.icon = icon
                    category.description = description
                    category.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"[~] Updated: {slug}"))
                else:
                    self.stdout.write(f"[-] Skipped: {slug}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Created: {created_count}, Updated: {updated_count}, Total: {ServiceCategory.objects.count()}"
            )
        )
