"""
Management command to add missing icons to service categories.
Usage: python manage.py add_missing_icons
"""
from django.core.management.base import BaseCommand
from services.models import ServiceCategory


class Command(BaseCommand):
    help = 'Add missing icons to service categories'

    def handle(self, *args, **options):
        # Mapping of category names to FontAwesome icons
        icon_mapping = {
            'Acoperișuri': 'fas fa-home',
            'Asamblare și Montaj': 'fas fa-screwdriver',
            'Curățenie și Menaj': 'fas fa-broom',
            'Demo Category': 'fas fa-tools',
            'Design Interior': 'fas fa-palette',
            'Geamuri și Ferestre': 'fas fa-window-restore',
            'Grădinărit și Peisagistică': 'fas fa-leaf',
            'IT și Tehnologie': 'fas fa-laptop',
            'Instalații Electrice': 'fas fa-plug',
            'Instalații Sanitare': 'fas fa-faucet',
            'Renovări și Construcții': 'fas fa-hard-hat',
        }

        updated_count = 0
        for category_name, icon in icon_mapping.items():
            try:
                category = ServiceCategory.objects.get(name=category_name)
                if not category.icon:
                    category.icon = icon
                    category.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'[OK] Updated icon for "{category_name}": {icon}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'[SKIP] "{category_name}" already has icon: {category.icon}')
                    )
            except ServiceCategory.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'[ERROR] Category "{category_name}" not found')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n[DONE] Updated {updated_count} categories')
        )
