# -*- coding: utf-8 -*-
"""
Script to update meta_title for all CityLandingPage records
Adds urgency keywords and symbols for improved CTR
"""

import os
import sys
import django

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bricli.settings')
django.setup()

from core.models import CityLandingPage


def update_titles():
    """Update all landing page titles with urgency keywords"""

    # Title templates by profession
    title_templates = {
        'Instalator': '{profession} {city} NON-STOP ⚡ Urgențe 24/7 | Meșteri Verificați | Bricli',
        'Electrician': '{profession} {city} 24/7 ⚡ Rapid & Ieftin | 100+ Meșteri | Bricli',
        'Zugrav': '{profession} {city} Profesionist ✓ Prețuri de la 50 RON/mp | Bricli',
        'Dulgher': 'Tâmplar {city} NON-STOP ⚡ Mobilă la Comandă | Meșteri | Bricli',
    }

    pages = CityLandingPage.objects.all()
    updated_count = 0

    for page in pages:
        # Get appropriate template
        template = title_templates.get(page.profession,
                                      '{profession} {city} NON-STOP | Meșteri Verificați | Bricli')

        # Generate new title
        new_title = template.format(
            profession=page.profession,
            city=page.city_name
        )

        # Update if different
        if page.meta_title != new_title:
            old_title = page.meta_title
            page.meta_title = new_title
            page.save(update_fields=['meta_title', 'updated_at'])

            print(f"✓ Updated: {page.profession} {page.city_name}")
            print(f"  OLD: {old_title}")
            print(f"  NEW: {new_title}\n")
            updated_count += 1
        else:
            print(f"⊘ Skipped (already optimized): {page.profession} {page.city_name}")

    print(f"\n{'='*60}")
    print(f"SUMMARY: Updated {updated_count} out of {pages.count()} landing pages")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("Starting SEO title optimization...\n")
    update_titles()
    print("\n✓ Title optimization complete!")
