# -*- coding: utf-8 -*-
"""
Script to add FAQs to the top 5 landing pages
Focuses on pricing, availability, trust, and process questions
"""

import os
import sys
import django

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bricli.settings')
django.setup()

from core.models import CityLandingPage, CityLandingFAQ


# FAQ templates by profession
FAQ_DATA = {
    'Instalator': [
        {
            'question': 'Cât costă serviciile unui instalator în {city}?',
            'answer': 'Prețurile variază în funcție de complexitatea lucrării. În medie, o intervenție simplă pornește de la 150 RON, în timp ce montarea centralelor termice poate costa între 500-1500 RON. Prin Bricli poți obține oferte GRATUIT de la mai mulți meșteri și alegi pe cel mai avantajos.',
            'order': 1
        },
        {
            'question': 'Sunt disponibili instalatori NON-STOP în {city}?',
            'answer': 'Da! Pe Bricli găsești instalatori disponibili 24/7 pentru urgențe precum țevi sparte, robinetele defecte sau scurgeri de gaz. Postează cererea ta și primești oferte rapid, chiar și în weekend sau noapte.',
            'order': 2
        },
        {
            'question': 'Cum știu că instalatorii de pe Bricli sunt de încredere?',
            'answer': 'Toți instalatorii de pe platformă sunt verificați și au autorizații valide. Poți vedea review-urile reale ale clienților anteriori, portofoliul cu lucrări finalizate și evaluările de la 1 la 5 stele. Fiecare meșter este evaluat după fiecare lucrare.',
            'order': 3
        },
        {
            'question': 'Cât durează până primesc oferte de la instalatori?',
            'answer': 'În medie, primești primele oferte în maxim 2-4 ore de la postarea cererii. Pentru urgențe, meșterii răspund adesea în 30-60 de minute. Vei fi notificat prin email și SMS când primești o ofertă nouă.',
            'order': 4
        },
        {
            'question': 'Trebuie să plătesc pentru a posta o cerere pe Bricli?',
            'answer': 'Nu! Postarea cererii și primirea ofertelor este 100% GRATUITĂ pentru clienți. Plătești doar meșterul ales după finalizarea lucrării, conform ofertei acceptate. Nu există costuri ascunse.',
            'order': 5
        },
        {
            'question': 'Ce tipuri de lucrări poate face un instalator?',
            'answer': 'Instalatorii de pe Bricli pot realiza: montaj/reparații centrale termice, instalații sanitare (chiuvete, băi, toalete), sisteme de încălzire în pardoseală, înlocuirea țevilor, desfundarea scurgerilor, montaj boilere și multe altele. Descrie problema ta și primești soluții.',
            'order': 6
        },
    ],
    'Electrician': [
        {
            'question': 'Cât costă un electrician în {city}?',
            'answer': 'Tarifele electricienilor încep de la 100 RON pentru intervenții simple (schimbat becuri, prize). Lucrări complexe precum refacerea instalației electrice costă între 25-40 RON/metru liniar. Prin Bricli primești oferte de la mai mulți electricieni și compari prețurile.',
            'order': 1
        },
        {
            'question': 'Există electricieni disponibili 24/7 în {city} pentru urgențe?',
            'answer': 'Da! Pe Bricli găsești electricieni disponibili NON-STOP pentru urgențe precum scurtcircuite, siguranțe arse, panouri electrice defecte sau lipsa curentului. Postează cererea și primești oferte rapid, chiar și în weekend.',
            'order': 2
        },
        {
            'question': 'Sunt electricienii de pe Bricli autorizați?',
            'answer': 'Absolut! Toți electricienii sunt verificați și dețin autorizații ANRE valide pentru lucrări electrice. Vezi review-urile reale, portofoliul cu proiecte anterioare și evaluările clienților înainte de a alege.',
            'order': 3
        },
        {
            'question': 'Cât de repede primesc oferte de la electricieni?',
            'answer': 'De obicei în 1-3 ore de la postarea cererii. Pentru urgențe, meșterii răspund adesea în 30-60 de minute. Ești notificat instant prin email și SMS când primești oferte noi.',
            'order': 4
        },
        {
            'question': 'Costa ceva să postez o cerere pe Bricli?',
            'answer': 'Nu! Serviciul este GRATUIT pentru clienți. Postezi cererea, primești oferte și alegi electricianul. Plătești doar pentru lucrarea efectuată, fără comisioane sau costuri ascunse.',
            'order': 5
        },
        {
            'question': 'Ce lucrări poate face un electrician autorizat?',
            'answer': 'Electricienii de pe Bricli pot realiza: instalații electrice complete, montaj tablouri electrice, prize și întrerupătoare, sisteme de iluminat, detectoare fum, videointerfoane, prize auto (EV chargers), verificări ANRE și multe altele.',
            'order': 6
        },
    ],
    'Zugrav': [
        {
            'question': 'Cât costă zugrăveala în {city}?',
            'answer': 'Prețurile pornesc de la 50 RON/mp pentru vopsitorie simplă și pot ajunge la 80-120 RON/mp pentru finisaje speciale sau tencuieli decorative. Prin Bricli primești oferte GRATUIT de la mai mulți zugravi și compari prețurile.',
            'order': 1
        },
        {
            'question': 'Cum aleg un zugrav de încredere în {city}?',
            'answer': 'Pe Bricli vezi review-uri reale de la clienți, poze din portofoliu cu lucrări anterioare și evaluări de la 1 la 5 stele. Toți zugravi sunt verificați și au experiență dovedită în domeniu.',
            'order': 2
        },
        {
            'question': 'Cât durează zugrăveala unui apartament?',
            'answer': 'Un apartament cu 2 camere se zugrăvește în 2-4 zile, în funcție de starea pereților și finisajul dorit. Zugravi profesioniști oferă estimări clare ale duratei la fiecare ofertă primită.',
            'order': 3
        },
        {
            'question': 'Trebuie să plătesc pentru ofertele de zugrăvit?',
            'answer': 'Nu! Postarea cererii și primirea ofertelor este 100% GRATUITĂ. Plătești doar zugraveul ales după finalizarea lucrării, conform prețului convenit.',
            'order': 4
        },
        {
            'question': 'Pot vedea lucrările anterioare ale zugravilor?',
            'answer': 'Da! Fiecare zugrav are un portofoliu cu poze din proiecte finalizate. Vezi calitatea lucrărilor, finisajele realizate și detaliile înainte de a decide.',
            'order': 5
        },
        {
            'question': 'Ce servicii oferă zugravi pe Bricli?',
            'answer': 'Zugravi pot realiza: zugrăvit interior/exterior, tencuieli decorative, vopsit tâmplărie, montaj tapet, șpacluire pereți, finisaje speciale (efect beton, piatră, etc), și consultanță în alegerea culorilor.',
            'order': 6
        },
    ],
    'Dulgher': [
        {
            'question': 'Cât costă mobilă la comandă în {city}?',
            'answer': 'Prețurile variază în funcție de dimensiuni și materiale. O bucătărie la comandă pornește de la 3000-5000 RON, dulapuri de la 1500 RON, iar mobilier personalizat de la 500 RON/mp. Primești oferte GRATUIT de la mai mulți tâmplari pe Bricli.',
            'order': 1
        },
        {
            'question': 'Sunt tâmplari disponibili pentru proiecte custom în {city}?',
            'answer': 'Da! Pe Bricli găsești tâmplari specializați în mobilă la comandă: bucătării, dulapuri, birouri, rafturi, mobilier pentru dormitor sau living. Descrie proiectul tău și primești oferte personalizate.',
            'order': 2
        },
        {
            'question': 'Cum știu că tâmplarii sunt profesioniști?',
            'answer': 'Vezi portofoliul cu proiecte finalizate, review-uri reale de la clienți anteriori și evaluări de la 1 la 5 stele. Poți compara mai mulți meșteri și alegi pe cel care se potrivește nevoilor tale.',
            'order': 3
        },
        {
            'question': 'Cât durează realizarea mobilei la comandă?',
            'answer': 'De obicei 2-4 săptămâni, în funcție de complexitate. Bucătăriile complexe pot dura 4-6 săptămâni. Fiecare tâmplar oferă o estimare clară a termenului de livrare în oferta sa.',
            'order': 4
        },
        {
            'question': 'Costa ceva să primesc oferte pentru mobilă?',
            'answer': 'Nu! Serviciul Bricli este GRATUIT pentru clienți. Postezi cererea, primești oferte personalizate și alegi tâmplarul. Plătești doar pentru mobilierul realizat, fără comisioane sau costuri ascunse.',
            'order': 5
        },
        {
            'question': 'Ce tipuri de mobilier pot comanda?',
            'answer': 'Tâmplarii de pe Bricli realizează: bucătării la comandă, dulapuri glisante, mobilier dormitor, birouri personalizate, rafturi și biblioteci, mobilier pentru baie, mese și scaune, pergole și foisoare, și orice alte proiecte custom.',
            'order': 6
        },
    ],
}


def add_faqs_for_landing_pages():
    """Add FAQs to the top 5 most important landing pages"""

    # Top 5 landing pages by SEO priority
    # Instalator Brașov, București, Cluj
    # Electrician Brașov, București
    top_pages = [
        ('Instalator', 'Brașov'),
        ('Instalator', 'București'),
        ('Instalator', 'Cluj-Napoca'),
        ('Electrician', 'Brașov'),
        ('Electrician', 'București'),
    ]

    added_count = 0

    for profession, city_name in top_pages:
        try:
            page = CityLandingPage.objects.get(
                profession=profession,
                city_name=city_name
            )

            # Get FAQ templates for this profession
            faq_templates = FAQ_DATA.get(profession, [])

            if not faq_templates:
                print(f"⚠ No FAQ templates for {profession}")
                continue

            # Check if FAQs already exist
            existing_faqs = page.faqs.count()
            if existing_faqs > 0:
                print(f"⊘ {profession} {city_name} already has {existing_faqs} FAQs, skipping")
                continue

            # Add FAQs
            for faq_data in faq_templates:
                CityLandingFAQ.objects.create(
                    landing_page=page,
                    question=faq_data['question'].format(city=city_name),
                    answer=faq_data['answer'],
                    order=faq_data['order'],
                    is_active=True
                )

            print(f"✓ Added {len(faq_templates)} FAQs to {profession} {city_name}")
            added_count += 1

        except CityLandingPage.DoesNotExist:
            print(f"✗ Landing page not found: {profession} {city_name}")
        except Exception as e:
            print(f"✗ Error adding FAQs to {profession} {city_name}: {e}")

    print(f"\n{'='*60}")
    print(f"SUMMARY: Added FAQs to {added_count} landing pages")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("Adding FAQs to top 5 landing pages for SEO...\n")
    add_faqs_for_landing_pages()
    print("\n✓ FAQ addition complete!")
