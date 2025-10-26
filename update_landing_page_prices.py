# -*- coding: utf-8 -*-
"""
Script to add competitive price ranges to all 60 existing landing pages
Based on competitor analysis: InstaloMania, Mesterul Tau Brasov, etc.
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


# Price range content by profession
PRICE_CONTENT = {
    'Instalator': """
## Prețuri Orientative Instalator {city}

Prețurile pentru servicii de instalații sanitare și termice variază în funcție de complexitatea lucrării:

### Intervenții Simple
- **Reparații robinete/țevi**: 150-300 RON
- **Desfundare WC/chiuvetă**: 150-250 RON
- **Înlocuire rezervor WC**: 200-400 RON
- **Montaj chiuvetă/lavoar**: 250-500 RON

### Lucrări Medii
- **Montaj centrală termică**: 500-1500 RON (fără echipament)
- **Montaj boiler electric**: 300-600 RON
- **Înlocuire țevi (per metru)**: 50-100 RON
- **Instalație baie completă**: 2000-4000 RON

### Proiecte Complexe
- **Sistem încălzire în pardoseală**: 80-150 RON/mp
- **Instalație sanitară apartament**: 3000-6000 RON
- **Centrală + calorifere**: 5000-10000 RON

**✓ Obții oferte GRATUIT** de la mai mulți instalatori verificați și alegi pe cel mai avantajos pentru tine.
""",

    'Electrician': """
## Prețuri Orientative Electrician {city}

Tarifele pentru lucrări electrice depind de tipul și complexitatea intervenției:

### Intervenții Simple
- **Schimbat becuri/prize**: 100-200 RON
- **Montaj lustră**: 150-300 RON
- **Reparație întrerupător**: 100-200 RON
- **Verificare siguranțe**: 150-250 RON

### Lucrări Medii
- **Montaj priză auto (EV charger)**: 500-1000 RON
- **Tablou electric nou**: 800-1500 RON
- **Sistem iluminat LED**: 500-1500 RON
- **Montaj videointerfon**: 400-800 RON

### Proiecte Complexe
- **Instalație electrică nouă (per metru)**: 25-40 RON/ml
- **Refacere instalație apartament**: 3000-6000 RON
- **Tablou electric + circuit complet**: 2000-4000 RON

**✓ Electricieni autorizați ANRE** cu garanție și recenzii verificate. Primești oferte GRATUIT în 1-3 ore.
""",

    'Zugrav': """
## Prețuri Orientative Zugrăveli {city}

Costurile pentru zugrăveli și finisaje variază în funcție de suprafață și tipul lucrării:

### Zugrăveli Interioare
- **Vopsit camere (lavabil)**: 50-80 RON/mp
- **Vopsit tavan**: 40-60 RON/mp
- **Șpacluire + vopsit**: 70-100 RON/mp
- **Tencuială decorativă**: 80-150 RON/mp

### Zugrăveli Exterioare
- **Vopsit fațadă**: 60-90 RON/mp
- **Tencuială exterioară**: 80-120 RON/mp
- **Hidroizolație + vopsit**: 100-150 RON/mp

### Finisaje Speciale
- **Efect beton/piatră**: 100-180 RON/mp
- **Vopsit tâmplărie (lemn)**: 30-60 RON/mp
- **Montaj tapet**: 20-40 RON/mp

### Estimări pe Apartament
- **Apartament 2 camere**: 2500-4500 RON
- **Apartament 3 camere**: 3500-6500 RON

**✓ Vezi portofolii cu lucrări anterioare** și alegi zugraveul potrivit. Oferte GRATUIT în 2-4 ore.
""",

    'Dulgher': """
## Prețuri Orientative Mobilă la Comandă {city}

Costurile pentru mobilier personalizat depind de dimensiuni, materiale și complexitate:

### Bucătării la Comandă
- **Bucătărie mică (3-4m)**: 3000-5000 RON
- **Bucătărie medie (5-7m)**: 5000-8000 RON
- **Bucătărie mare (8-10m)**: 8000-12000 RON
- **Cu electrocasnice integrate**: +1000-2000 RON

### Dulapuri și Mobilier Dormitor
- **Dulap glisant 2 usi (2m)**: 1500-2500 RON
- **Dulap glisant 3 usi (3m)**: 2500-4000 RON
- **Pat tapițat cu somieră**: 1500-3000 RON
- **Noptiere (set 2 buc)**: 500-1000 RON

### Mobilier Living și Birou
- **Bibliotecă/rafturi**: 1000-2500 RON
- **Masă living extensibilă**: 1500-3000 RON
- **Birou personalizat**: 1000-2500 RON
- **Comodă TV**: 1000-2000 RON

### Mobilier Baie
- **Dulap baie suspendat**: 800-1500 RON
- **Mobilier baie complet**: 2000-4000 RON

**✓ Tâmplari cu experiență** realizează proiecte personalizate exact după dorințele tale. Primești oferte GRATUIT și alegi cel mai bun raport calitate-preț.
"""
}


def update_prices_for_all_pages():
    """Update prices_text field for all landing pages"""

    pages = CityLandingPage.objects.all().order_by('profession', 'city_name')
    updated_count = 0
    skipped_count = 0

    print(f"Found {pages.count()} landing pages to update\n")

    for page in pages:
        # Get price content template for this profession
        price_template = PRICE_CONTENT.get(page.profession, '')

        if not price_template:
            print(f"⚠ No price template for {page.profession} - {page.city_name}")
            skipped_count += 1
            continue

        # Check if already has substantial price content
        if page.prices_text and len(page.prices_text) > 500:
            print(f"⊘ {page.profession} {page.city_name} already has detailed prices, skipping")
            skipped_count += 1
            continue

        # Format with city name
        new_prices_text = price_template.format(city=page.city_name)

        # Update the page
        page.prices_text = new_prices_text.strip()
        page.save()

        print(f"✓ Updated {page.profession} {page.city_name}")
        updated_count += 1

    print(f"\n{'='*60}")
    print(f"SUMMARY: Updated {updated_count} pages, skipped {skipped_count} pages")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("Adding competitive price ranges to landing pages...\n")
    update_prices_for_all_pages()
    print("\n✓ Price update complete!")
