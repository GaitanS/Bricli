# -*- coding: utf-8 -*-
"""
Script to update meta_description for all CityLandingPage records
Adds specific services, CTAs, and "GRATUIT" keyword for improved CTR
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


def update_descriptions():
    """Update all landing page meta descriptions with optimized CTAs"""

    # Description templates by profession (max 155 characters)
    description_templates = {
        'Instalator': '{profession} autorizat {city} NON-STOP. Oferte GRATUIT, meșteri verificați, urgențe 24/7. ⚡ Obține 3 oferte rapid!',
        'Electrician': '{profession} {city} 24/7 - Prețuri GRATUIT, lucrări rapid, meșteri cu experiență. ⚡ Compară 3 oferte și economisește!',
        'Zugrav': '{profession} profesionist {city}. Prețuri de la 50 RON/mp, oferte GRATUIT. ✓ Lucrări de calitate garantată!',
        'Dulgher': 'Tâmplar {city} - Mobilă la comandă, meșteri verificați. Oferte GRATUIT! ⚡ Bucătării, dulapuri, mobilier personalizat.',
    }

    pages = CityLandingPage.objects.all()
    updated_count = 0

    for page in pages:
        # Get appropriate template
        template = description_templates.get(page.profession,
                                            '{profession} {city} - Meșteri verificați, oferte GRATUIT. ⚡ Găsește meșterul potrivit rapid!')

        # Generate new description
        new_description = template.format(
            profession=page.profession,
            city=page.city_name
        )

        # Ensure it's under 155 characters (Google's limit)
        if len(new_description) > 155:
            new_description = new_description[:152] + '...'

        # Update if different
        if page.meta_description != new_description:
            old_description = page.meta_description
            page.meta_description = new_description
            page.save(update_fields=['meta_description', 'updated_at'])

            print(f"✓ Updated: {page.profession} {page.city_name}")
            print(f"  OLD ({len(old_description)} chars): {old_description}")
            print(f"  NEW ({len(new_description)} chars): {new_description}\n")
            updated_count += 1
        else:
            print(f"⊘ Skipped (already optimized): {page.profession} {page.city_name}")

    print(f"\n{'='*60}")
    print(f"SUMMARY: Updated {updated_count} out of {pages.count()} landing pages")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("Starting SEO meta description optimization...\n")
    update_descriptions()
    print("\n✓ Meta description optimization complete!")
