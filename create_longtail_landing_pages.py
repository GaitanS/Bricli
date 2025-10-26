# -*- coding: utf-8 -*-
"""
Script to create 20 longtail landing pages for high-value keywords
Focus: specific services that people actually search for
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


# Longtail landing page data (20 pages)
LONGTAIL_PAGES = [
    # Instalator - specific services (high search volume)
    {
        'profession': 'Instalator Sanitar',
        'profession_slug': 'instalator-sanitar',
        'city_name': 'Brașov',
        'city_slug': 'brasov',
        'meta_title': 'Instalator Sanitar Brașov NON-STOP ⚡ Urgențe 24/7 | Bricli',
        'meta_description': 'Instalator sanitar Brașov disponibil 24/7. Montaj chiuvete, băi, toalete. Oferte GRATUIT! ⚡ Meșteri verificați.',
        'h1_title': 'Găsește Instalator Sanitar în Brașov',
        'intro_text': 'Ai nevoie de un instalator sanitar în Brașov pentru montaj chiuvete, băi sau toalete? Pe Bricli găsești rapid meșteri verificați disponibili NON-STOP.',
        'services_text': '**Servicii Instalații Sanitare:**\n- Montaj chiuvete, lavoare, băi\n- Instalare toalete, bidee\n- Schimbat robinete, baterii\n- Reparații scurgeri, țevi\n- Montaj boilere, încălzire',
        'prices_text': '**Prețuri orientative:**\n- Montaj chiuvetă: 150-250 RON\n- Instalare toaletă: 200-350 RON\n- Schimbat robinet: 100-150 RON\n- Montaj boiler: 300-500 RON',
        'how_it_works_text': '1. Postezi cererea GRATUIT\n2. Primești până la 5 oferte în 24h\n3. Compari prețuri și review-uri\n4. Alegi instalatorul potrivit',
        'craftsmen_count': 45,
        'reviews_count': 230,
    },
    {
        'profession': 'Desfundare WC',
        'profession_slug': 'desfundare-wc',
        'city_name': 'Brașov',
        'city_slug': 'brasov',
        'meta_title': 'Desfundare WC Brașov NON-STOP ⚡ Intervenție Rapidă 24/7 | Bricli',
        'meta_description': 'Desfundare WC/toaletă Brașov NON-STOP. Intervenție rapidă, meșteri verificați. ⚡ Oferte în 30 min!',
        'h1_title': 'Desfundare WC Rapidă în Brașov',
        'intro_text': 'WC-ul înfundat? Instalatori disponibili NON-STOP în Brașov pentru desfundări rapide. Intervenție în 1-2 ore!',
        'services_text': '**Servicii Desfundare:**\n- Desfundare toalete, WC-uri\n- Desfundare scurgeri chiuvete\n- Desfundare conducte principale\n- Inspecție video canalizare\n- Curățare sifoane',
        'prices_text': '**Prețuri orientative:**\n- Desfundare WC simplă: 150-250 RON\n- Desfundare scurgere: 100-200 RON\n- Inspecție video: 300-500 RON\n- Intervenție urgentă noapte: +30%',
        'how_it_works_text': '1. Descrie problema (WC înfundat)\n2. Primești oferte în 30-60 min\n3. Alegi instalatorul disponibil rapid\n4. Problemă rezolvată în 1-2 ore!',
        'craftsmen_count': 32,
        'reviews_count': 180,
    },
    {
        'profession': 'Reparații Centrale Termice',
        'profession_slug': 'reparatii-centrale-termice',
        'city_name': 'Brașov',
        'city_slug': 'brasov',
        'meta_title': 'Reparații Centrale Termice Brașov 24/7 ⚡ Autorizați ISCIR | Bricli',
        'meta_description': 'Reparații centrale termice Brașov NON-STOP. Meșteri autorizați ISCIR, intervenție rapidă. ⚡ Oferte GRATUIT!',
        'h1_title': 'Reparații Centrale Termice în Brașov',
        'intro_text': 'Centrala termică nu funcționează? Instalatori autorizați ISCIR disponibili 24/7 în Brașov pentru reparații și service.',
        'services_text': '**Servicii Centrale Termice:**\n- Reparații centrale Ariston, Vaillant, Bosch\n- Service preventiv, revizie\n- Înlocuire piese (pompe, vase expansiune)\n- Curățare schimbător de căldură\n- Reprogramare centrală',
        'prices_text': '**Prețuri orientative:**\n- Service preventiv: 200-300 RON\n- Reparație simplă: 250-500 RON\n- Înlocuire pompă: 400-800 RON\n- Curățare schimbător: 350-600 RON',
        'how_it_works_text': '1. Descrie defecțiunea centralei\n2. Primești oferte de la meșteri ISCIR\n3. Compari prețuri și disponibilitate\n4. Programează intervenția',
        'craftsmen_count': 28,
        'reviews_count': 150,
    },
    {
        'profession': 'Instalator Urgențe',
        'profession_slug': 'instalator-urgente',
        'city_name': 'București',
        'city_slug': 'bucuresti',
        'meta_title': 'Instalator Urgențe București 24/7 ⚡ Intervenție NON-STOP | Bricli',
        'meta_description': 'Instalator urgențe București disponibil 24/7. Țevi sparte, scurgeri, gaz. ⚡ Intervenție în 1-2 ore!',
        'h1_title': 'Instalator Urgențe 24/7 București',
        'intro_text': 'Urgență instalații în București? Țeavă spartă, scurgere de gaz sau lipsă apă caldă? Instalatori disponibili NON-STOP!',
        'services_text': '**Urgențe Instalații:**\n- Țevi sparte, fisuri, scurgeri\n- Robinete defecte, baterii stricate\n- Scurgeri gaz, miros suspect\n- WC înfundat, scurgeri blocate\n- Centrală oprită, fără căldură',
        'prices_text': '**Prețuri urgențe:**\n- Intervenție urgentă zi: de la 200 RON\n- Intervenție noapte/weekend: de la 250 RON\n- Reparație țeavă spartă: 300-600 RON\n- Desfundare urgentă: 200-350 RON',
        'how_it_works_text': '1. Sună sau postează cererea (urgență!)\n2. Primești oferte în 15-30 min\n3. Alegi instalatorul disponibil rapid\n4. Intervenție în 1-2 ore!',
        'craftsmen_count': 65,
        'reviews_count': 420,
    },

    # Tâmplar - mobilă la comandă (high value)
    {
        'profession': 'Tâmplar',
        'profession_slug': 'tamplar',
        'city_name': 'Brașov',
        'city_slug': 'brasov',
        'meta_title': 'Tâmplar Brașov - Mobilă la Comandă ⚡ Proiecte Custom | Bricli',
        'meta_description': 'Tâmplar Brașov - Mobilă personalizată, bucătării, dulapuri. Oferte GRATUIT! ⚡ Meșteri verificați.',
        'h1_title': 'Găsește Tâmplar Profesionist în Brașov',
        'intro_text': 'Cauți tâmplar în Brașov pentru mobilă la comandă? Pe Bricli găsești meșteri verificați pentru bucătării, dulapuri și mobilier personalizat.',
        'services_text': '**Servicii Tâmplărie:**\n- Bucătării la comandă\n- Dulapuri glisante personalizate\n- Mobilier dormitor (paturi, noptiere)\n- Biblioteci, rafturi, birouri\n- Mobilier pentru baie',
        'prices_text': '**Prețuri orientative:**\n- Bucătărie la comandă: 3000-7000 RON\n- Dulap glisant: 1500-4000 RON\n- Mobilier dormitor: 2000-5000 RON\n- Birou custom: 1000-2500 RON',
        'how_it_works_text': '1. Descrie proiectul tău (măsuri, stil)\n2. Primești oferte personalizate\n3. Compari portofolii și prețuri\n4. Alegi tâmplarul și stabilești detalii',
        'craftsmen_count': 38,
        'reviews_count': 195,
    },
    {
        'profession': 'Mobilă la Comandă',
        'profession_slug': 'mobila-la-comanda',
        'city_name': 'Brașov',
        'city_slug': 'brasov',
        'meta_title': 'Mobilă la Comandă Brașov ⚡ Bucătării, Dulapuri Custom | Bricli',
        'meta_description': 'Mobilă la comandă Brașov - Bucătării, dulapuri, mobilier personalizat. Oferte GRATUIT de la tâmplari! ⚡',
        'h1_title': 'Mobilă la Comandă în Brașov',
        'intro_text': 'Vrei mobilă personalizată perfect adaptată spațiului tău? Tâmplari din Brașov realizează bucătării, dulapuri și mobilier custom.',
        'services_text': '**Mobilă Personalizată:**\n- Bucătării moderne/clasice la comandă\n- Dulapuri glisante pe măsură\n- Mobilier living (biblioteci, TV wall)\n- Mobilier dormitor complet\n- Soluții pentru spații mici',
        'prices_text': '**Prețuri pe metru pătrat:**\n- Mobilă PAL melaminat: 500-800 RON/mp\n- Mobilă MDF vopsit: 800-1200 RON/mp\n- Mobilă lemn masiv: 1500-2500 RON/mp\n- Finisaje premium: de la 1000 RON/mp',
        'how_it_works_text': '1. Trimite dimensiuni și preferințe\n2. Primești schițe/oferte personalizate\n3. Compari designuri și materiale\n4. Confirm comanda și termenul',
        'craftsmen_count': 38,
        'reviews_count': 195,
    },
    {
        'profession': 'Mobilă Bucătărie',
        'profession_slug': 'mobila-bucatarie',
        'city_name': 'Brașov',
        'city_slug': 'brasov',
        'meta_title': 'Mobilă Bucătărie Brașov la Comandă ⚡ Design Modern | Bricli',
        'meta_description': 'Bucătării la comandă Brașov - Design personalizat, materiale premium. Oferte GRATUIT! ⚡ Tâmplari verificați.',
        'h1_title': 'Bucătării la Comandă în Brașov',
        'intro_text': 'Visezi la o bucătărie modernă perfect adaptată spațiului tău? Tâmplari din Brașov realizează bucătării la comandă cu design personalizat.',
        'services_text': '**Bucătării la Comandă:**\n- Design 3D personalizat gratuit\n- Bucătării moderne/clasice/rustice\n- Blat de lucru (compozit, lemn, granit)\n- Electronice integrate (cuptor, plită)\n- Soluții pentru bucătării mici',
        'prices_text': '**Prețuri bucătării:**\n- Bucătărie mică (3-4 mp): 3000-5000 RON\n- Bucătărie medie (5-7 mp): 5000-8000 RON\n- Bucătărie mare (8-12 mp): 8000-15000 RON\n- Materiale premium: +30-50%',
        'how_it_works_text': '1. Trimite planul bucătăriei (măsuri)\n2. Primești designuri 3D gratuite\n3. Alegi materiale și culori\n4. Confirm și așteaptă livrarea (3-6 săptămâni)',
        'craftsmen_count': 25,
        'reviews_count': 140,
    },
    {
        'profession': 'Mobilă Dormitor',
        'profession_slug': 'mobila-dormitor',
        'city_name': 'București',
        'city_slug': 'bucuresti',
        'meta_title': 'Mobilă Dormitor București la Comandă ⚡ Paturi, Dulapuri | Bricli',
        'meta_description': 'Mobilă dormitor București - Paturi, dulapuri, noptiere personalizate. Oferte GRATUIT! ⚡ Design modern.',
        'h1_title': 'Mobilă Dormitor la Comandă București',
        'intro_text': 'Transformă-ți dormitorul! Tâmplari din București realizează mobilier personalizat: paturi, dulapuri, comode, noptiere.',
        'services_text': '**Mobilier Dormitor:**\n- Paturi tapițate personalizate\n- Dulapuri glisante pe măsură\n- Comode și sertare\n- Noptiere și măsuțe\n- Dressing-room complet',
        'prices_text': '**Prețuri mobilier dormitor:**\n- Pat tapițat: 1500-3500 RON\n- Dulap glisant: 2000-5000 RON\n- Comodă cu sertare: 800-2000 RON\n- Set complet dormitor: 5000-12000 RON',
        'how_it_works_text': '1. Descrie stilul dorit (modern, clasic)\n2. Primești variante de design\n3. Alegi materiale și culori\n4. Comandă și instalare în 3-5 săptămâni',
        'craftsmen_count': 52,
        'reviews_count': 310,
    },

    # Electrician - specific services
    {
        'profession': 'Tablou Electric',
        'profession_slug': 'tablou-electric',
        'city_name': 'București',
        'city_slug': 'bucuresti',
        'meta_title': 'Tablou Electric București - Montaj și Modernizare 24/7 | Bricli',
        'meta_description': 'Tablou electric București - Montaj, modernizare, siguranțe automate. Electricieni autorizați ANRE. ⚡ Oferte GRATUIT!',
        'h1_title': 'Montaj și Modernizare Tablou Electric București',
        'intro_text': 'Tablou electric vechi sau supraîncărcat? Electricieni autorizați din București modernizează și montează tablouri electrice noi.',
        'services_text': '**Servicii Tablouri Electrice:**\n- Montaj tablou electric nou\n- Modernizare tablou vechi\n- Siguranțe automate, diferențiale\n- Delimitare și etichetare circuite\n- Verificare și punere în funcțiune',
        'prices_text': '**Prețuri tablouri:**\n- Tablou apartament (6-12 module): 600-1200 RON\n- Tablou casă (18-36 module): 1200-2500 RON\n- Modernizare tablou: 400-800 RON\n- Siguranță automată: 50-150 RON/buc',
        'how_it_works_text': '1. Descrie necesarul (apartament/casă)\n2. Primești oferte de la electricieni ANRE\n3. Alegi soluția optimă\n4. Programează montajul',
        'craftsmen_count': 48,
        'reviews_count': 280,
    },
    {
        'profession': 'Instalații Electrice',
        'profession_slug': 'instalatii-electrice',
        'city_name': 'Cluj-Napoca',
        'city_slug': 'cluj-napoca',
        'meta_title': 'Instalații Electrice Cluj NON-STOP ⚡ Autorizați ANRE | Bricli',
        'meta_description': 'Instalații electrice Cluj-Napoca - Complete sau parțiale, electricieni ANRE. Oferte GRATUIT! ⚡ Rapid și sigur.',
        'h1_title': 'Instalații Electrice Profesionale Cluj-Napoca',
        'intro_text': 'Renovezi sau construiești? Electricieni autorizați din Cluj realizează instalații electrice complete conforme ANRE.',
        'services_text': '**Instalații Electrice:**\n- Instalații electrice complete (case noi)\n- Reface instalații apartamente\n- Montaj prize, întrerupătoare\n- Trasare circuite, tuburi PVC\n- Verificare ANRE, proces verbal',
        'prices_text': '**Prețuri instalații:**\n- Instalație electrică completă: 25-40 RON/mp\n- Montaj priză/întrerupător: 50-100 RON/buc\n- Trasare circuit: 15-25 RON/ml\n- Verificare ANRE: 300-600 RON',
        'how_it_works_text': '1. Trimite planul apartamentului/casei\n2. Primești oferte detaliate\n3. Compari prețuri și termene\n4. Alegi electricianul și programează',
        'craftsmen_count': 42,
        'reviews_count': 245,
    },

    # Zugrav - specific services
    {
        'profession': 'Vopsit Apartament',
        'profession_slug': 'vopsit-apartament',
        'city_name': 'București',
        'city_slug': 'bucuresti',
        'meta_title': 'Vopsit Apartament București ⚡ Zugravi Profesioniști | Bricli',
        'meta_description': 'Vopsit apartament București - Zugravi profesioniști, finisaje impecabile. De la 50 RON/mp. Oferte GRATUIT! ⚡',
        'h1_title': 'Vopsit Apartament Profesional București',
        'intro_text': 'Vrei să îți zugrăvești apartamentul? Zugravi profesioniști din București realizează lucrări impecabile, rapid și la prețuri corecte.',
        'services_text': '**Servicii Vopsitorie:**\n- Vopsit pereți și tavane\n- Șpacluire și grund\n- Vopsit tâmplărie (uși, ferestre)\n- Zugrăvit balcon/terasă\n- Curățenie finală inclusă',
        'prices_text': '**Prețuri vopsit:**\n- Vopsit simplu (1 strat): 50-70 RON/mp\n- Vopsit premium (2 straturi): 70-90 RON/mp\n- Șpacluire + vopsit: 80-120 RON/mp\n- Vopsit tâmplărie: 100-200 RON/bucată',
        'how_it_works_text': '1. Măsoară suprafața (mp pereți)\n2. Primești oferte de la zugravi\n3. Compari prețuri și termene\n4. Programează zugrăveala (2-4 zile)',
        'craftsmen_count': 58,
        'reviews_count': 340,
    },
    {
        'profession': 'Tencuială Decorativă',
        'profession_slug': 'tencuiala-decorativa',
        'city_name': 'Brașov',
        'city_slug': 'brasov',
        'meta_title': 'Tencuială Decorativă Brașov ⚡ Finisaje Premium | Bricli',
        'meta_description': 'Tencuială decorativă Brașov - Efect beton, piatră, venetiană. Zugravi specializați. Oferte GRATUIT! ⚡',
        'h1_title': 'Tencuială Decorativă Profesională Brașov',
        'intro_text': 'Vrei finisaje premium pentru casa ta? Zugravi specializați din Brașov aplică tencuială decorativă cu efect beton, piatră sau venetiană.',
        'services_text': '**Tipuri Tencuială Decorativă:**\n- Tencuială efect beton (loft)\n- Tencuială venetiană (marmură)\n- Tencuială cu efect piatră\n- Stucco decorativ\n- Finisaje texturate personalizate',
        'prices_text': '**Prețuri tencuială decorativă:**\n- Efect beton: 120-180 RON/mp\n- Tencuială venetiană: 150-250 RON/mp\n- Efect piatră: 100-160 RON/mp\n- Stucco: 130-200 RON/mp',
        'how_it_works_text': '1. Alege tipul de finisaj dorit\n2. Primești mostre și oferte\n3. Compari portofolii zugravi\n4. Programează aplicarea (3-5 zile)',
        'craftsmen_count': 22,
        'reviews_count': 115,
    },

    # Additional high-value longtail pages
    {
        'profession': 'Montaj Gresie Faianță',
        'profession_slug': 'montaj-gresie-faianta',
        'city_name': 'București',
        'city_slug': 'bucuresti',
        'meta_title': 'Montaj Gresie și Faianță București ⚡ Meșteri Verificați | Bricli',
        'meta_description': 'Montaj gresie și faianță București - Meșteri profesioniști, finisaje perfecte. De la 70 RON/mp. Oferte GRATUIT! ⚡',
        'h1_title': 'Montaj Gresie și Faianță București',
        'intro_text': 'Amenajezi bucătăria sau baia? Meșteri din București montează gresie și faianță cu finisaje impecabile.',
        'services_text': '**Servicii Montaj:**\n- Montaj gresie pardoseală\n- Montaj faianță pereți\n- Șapă autonivelantă\n- Hidroizolație baie\n- Rosturi și silicon',
        'prices_text': '**Prețuri montaj:**\n- Gresie simplă: 70-100 RON/mp\n- Faianță pereți: 80-120 RON/mp\n- Format mare (120x120): 120-160 RON/mp\n- Șapă autonivelantă: 40-60 RON/mp',
        'how_it_works_text': '1. Măsoară suprafața (mp)\n2. Primești oferte de la meșteri\n3. Compari prețuri și experiență\n4. Programează montajul',
        'craftsmen_count': 45,
        'reviews_count': 265,
    },
    {
        'profession': 'Amenajări Interioare',
        'profession_slug': 'amenajari-interioare',
        'city_name': 'Cluj-Napoca',
        'city_slug': 'cluj-napoca',
        'meta_title': 'Amenajări Interioare Cluj ⚡ Renovări Complete | Bricli',
        'meta_description': 'Amenajări interioare Cluj - Renovări apartamente, design interior, meșteri verificați. Oferte GRATUIT! ⚡',
        'h1_title': 'Amenajări Interioare Profesionale Cluj-Napoca',
        'intro_text': 'Renovezi apartamentul sau casa? Pe Bricli găsești echipe complete pentru amenajări interioare în Cluj-Napoca.',
        'services_text': '**Servicii Amenajări:**\n- Renovări complete apartamente\n- Amenajare bucătărie și baie\n- Vopsit, glet, zugrăvit\n- Montaj parchet, gresie\n- Design interior inclus',
        'prices_text': '**Prețuri renovare:**\n- Renovare simplă: 200-300 RON/mp\n- Renovare standard: 300-500 RON/mp\n- Renovare premium: 500-800+ RON/mp\n- Design interior: 15-30 RON/mp',
        'how_it_works_text': '1. Descrie proiectul de renovare\n2. Primești oferte și planuri\n3. Compari echipe și prețuri\n4. Semnezi contractul și începe lucrul',
        'craftsmen_count': 35,
        'reviews_count': 190,
    },
    {
        'profession': 'Montaj Parchet',
        'profession_slug': 'montaj-parchet',
        'city_name': 'Brașov',
        'city_slug': 'brasov',
        'meta_title': 'Montaj Parchet Brașov ⚡ Lemn, Laminat, Vinil | Bricli',
        'meta_description': 'Montaj parchet Brașov - Lemn masiv, laminat, vinil. Meșteri specializați. De la 25 RON/mp. Oferte GRATUIT! ⚡',
        'h1_title': 'Montaj Parchet Profesional Brașov',
        'intro_text': 'Vrei parchet nou în apartament? Meșteri din Brașov montează parchet din lemn, laminat sau vinil cu finisaje impecabile.',
        'services_text': '**Servicii Montaj Parchet:**\n- Parchet lemn masiv (stejar, frasin)\n- Parchet laminat (clasă trafic 31-33)\n- Parchet vinil (LVT, SPC)\n- Șapă autonivelantă\n- Plintă și profile',
        'prices_text': '**Prețuri montaj:**\n- Laminat: 25-40 RON/mp\n- Parchet triplu stratificat: 35-50 RON/mp\n- Parchet lemn masiv: 50-80 RON/mp\n- Vinil click: 30-45 RON/mp',
        'how_it_works_text': '1. Măsoară suprafața camerei\n2. Alege tipul de parchet\n3. Primești oferte de montaj\n4. Programează instalarea (1-3 zile)',
        'craftsmen_count': 30,
        'reviews_count': 175,
    },
    {
        'profession': 'Rigips și Tavane False',
        'profession_slug': 'rigips-tavane-false',
        'city_name': 'București',
        'city_slug': 'bucuresti',
        'meta_title': 'Rigips și Tavane False București ⚡ Montaj Profesional | Bricli',
        'meta_description': 'Rigips și tavane false București - Montaj pereți, tavane, iluminat LED. Meșteri verificați. Oferte GRATUIT! ⚡',
        'h1_title': 'Montaj Rigips și Tavane False București',
        'intro_text': 'Amenajezi sau renovezi? Meșteri din București montează rigips pentru pereți, tavane false și mobilier din gips-carton.',
        'services_text': '**Servicii Rigips:**\n- Pereți despărțitori rigips\n- Tavane false clasice/LED\n- Mobilier din rigips (rafturi, nișe)\n- Izolație fonică și termică\n- Finisaje și vopsit',
        'prices_text': '**Prețuri rigips:**\n- Perete simplu rigips: 80-120 RON/mp\n- Tavan fals clasic: 100-150 RON/mp\n- Tavan fals LED: 150-250 RON/mp\n- Mobilier rigips: 200-400 RON/mp',
        'how_it_works_text': '1. Descrie proiectul (pereți/tavane)\n2. Primești schițe și oferte\n3. Alegi meșterul și materialele\n4. Montaj în 3-7 zile',
        'craftsmen_count': 40,
        'reviews_count': 230,
    },
    {
        'profession': 'Închidere Balcon',
        'profession_slug': 'inchidere-balcon',
        'city_name': 'Cluj-Napoca',
        'city_slug': 'cluj-napoca',
        'meta_title': 'Închidere Balcon Cluj ⚡ Termopan, Geam Securizat | Bricli',
        'meta_description': 'Închidere balcon Cluj - Termopan, geam securizat, meșteri verificați. Oferte GRATUIT! ⚡ Izolaie termică.',
        'h1_title': 'Închidere Balcon Profesională Cluj-Napoca',
        'intro_text': 'Vrei să îți închizi balconul cu termopan? Meșteri din Cluj montează geam securizat și profile PVC/aluminiu.',
        'services_text': '**Servicii Închidere Balcon:**\n- Geam termopan securizat\n- Profile PVC sau aluminiu\n- Glisare sau rabatare\n- Izolație termică incluse\n- Montaj pervaz interior',
        'prices_text': '**Prețuri închidere:**\n- Geam simplu rabatabil: 600-1000 RON/mp\n- Geam glisant: 700-1200 RON/mp\n- Profile aluminiu premium: 900-1500 RON/mp\n- Geam termopan 3 camere: +20%',
        'how_it_works_text': '1. Măsoară balconul (lățime x înălțime)\n2. Alege tip profile și geam\n3. Primești oferte personalizate\n4. Montaj în 1-2 zile',
        'craftsmen_count': 28,
        'reviews_count': 160,
    },
    {
        'profession': 'Montaj Uși Interior',
        'profession_slug': 'montaj-usi-interior',
        'city_name': 'Brașov',
        'city_slug': 'brasov',
        'meta_title': 'Montaj Uși Interior Brașov ⚡ Meșteri Tâmplari | Bricli',
        'meta_description': 'Montaj uși interior Brașov - Uși lemn, MDF, glisante. Tâmplari verificați. Oferte GRATUIT! ⚡',
        'h1_title': 'Montaj Uși Interior Brașov',
        'intro_text': 'Schimbi ușile interioare? Tâmplari din Brașov montează uși din lemn, MDF, glisante sau pliantă rapid și profesional.',
        'services_text': '**Servicii Montaj Uși:**\n- Uși lemn masiv/furnir\n- Uși MDF/HDF vopsite\n- Uși glisante (sliding)\n- Uși pliantă (pliante)\n- Reglare și toc incluse',
        'prices_text': '**Prețuri montaj:**\n- Montaj ușă clasică: 150-250 RON/buc\n- Ușă glisantă: 300-500 RON\n- Ușă pliantă: 250-400 RON\n- Demontare ușă veche: 50-100 RON',
        'how_it_works_text': '1. Măsoară golul ușii\n2. Alege tipul de ușă\n3. Primești oferte de montaj\n4. Programează instalarea (1-2 ore/ușă)',
        'craftsmen_count': 32,
        'reviews_count': 185,
    },
    {
        'profession': 'Instalator Gaz',
        'profession_slug': 'instalator-gaz',
        'city_name': 'București',
        'city_slug': 'bucuresti',
        'meta_title': 'Instalator Gaz București Autorizat ANRE ⚡ Urgențe 24/7 | Bricli',
        'meta_description': 'Instalator gaz București autorizat ANRE. Branșamente, centrale, urgențe scurgeri gaz 24/7. Oferte GRATUIT! ⚡',
        'h1_title': 'Instalator Gaz Autorizat București',
        'intro_text': 'Ai nevoie de instalator gaz autorizat ANRE în București? Meșteri verificați pentru branșamente, centrale termice și urgențe gaz.',
        'services_text': '**Servicii Instalații Gaz:**\n- Branșament gaz natural\n- Montaj centrale pe gaz\n- Reparații scurgeri gaz\n- Verificare instalație (ANRE)\n- Înlocuire țevi și robinete gaz',
        'prices_text': '**Prețuri instalații gaz:**\n- Branșament gaz: 2000-4000 RON\n- Montaj centrală: 500-1000 RON\n- Verificare scurgeri: 200-400 RON\n- Înlocuire țeavă gaz: 150-300 RON/ml',
        'how_it_works_text': '1. Descrie lucrarea necesară\n2. Primești oferte de la instalatori ANRE\n3. Verifică autorizațiile meșterilor\n4. Programează intervenția',
        'craftsmen_count': 35,
        'reviews_count': 210,
    },
    {
        'profession': 'Montaj Aer Condiționat',
        'profession_slug': 'montaj-aer-conditionat',
        'city_name': 'București',
        'city_slug': 'bucuresti',
        'meta_title': 'Montaj Aer Condiționat București ⚡ Service și Reparații | Bricli',
        'meta_description': 'Montaj aer condiționat București - Instalare, service, reparații AC. Tehnicieni autorizați. Oferte GRATUIT! ⚡',
        'h1_title': 'Montaj Aer Condiționat București',
        'intro_text': 'Vrei să îți montezi aer condiționat? Tehnicieni autorizați din București instalează, service-ază și repară aparate AC.',
        'services_text': '**Servicii Aer Condiționat:**\n- Montaj AC nou (split, multisplit)\n- Demontare AC vechi\n- Service preventiv (curățare, freon)\n- Reparații defecțiuni\n- Relocare unitate',
        'prices_text': '**Prețuri montaj AC:**\n- Montaj AC 9000-12000 BTU: 400-600 RON\n- Montaj AC 18000-24000 BTU: 600-900 RON\n- Service preventiv: 200-350 RON\n- Completare freon: 150-300 RON',
        'how_it_works_text': '1. Specifică tipul AC (BTU, marca)\n2. Primești oferte de montaj\n3. Alegi tehnicianul\n4. Montaj în 2-4 ore',
        'craftsmen_count': 38,
        'reviews_count': 220,
    },
]


def create_longtail_pages():
    """Create 20 longtail landing pages for high-value keywords"""

    created_count = 0
    skipped_count = 0

    for page_data in LONGTAIL_PAGES:
        # Check if page already exists
        exists = CityLandingPage.objects.filter(
            profession_slug=page_data['profession_slug'],
            city_slug=page_data['city_slug']
        ).exists()

        if exists:
            print(f"⊘ {page_data['profession']} {page_data['city_name']} already exists, skipping")
            skipped_count += 1
            continue

        # Create page
        try:
            CityLandingPage.objects.create(**page_data)
            print(f"✓ Created: {page_data['profession']} {page_data['city_name']}")
            created_count += 1
        except Exception as e:
            print(f"✗ Error creating {page_data['profession']} {page_data['city_name']}: {e}")

    print(f"\n{'='*60}")
    print(f"SUMMARY: Created {created_count} new landing pages, skipped {skipped_count}")
    print(f"Total longtail pages: {created_count}")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("Creating 20 longtail landing pages for SEO...\n")
    create_longtail_pages()
    print("\n✓ Longtail page creation complete!")
