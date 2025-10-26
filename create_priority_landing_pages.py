# -*- coding: utf-8 -*-
"""
Create 5 high-priority landing pages targeting competitor keywords
Based on Google search analysis: instalator apa brasov, reparatii instalatii sanitare brasov, etc.
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


# High-priority landing pages data
PRIORITY_PAGES = [
    {
        'city_name': 'Brașov',
        'profession': 'Instalator Apă',
        'meta_title': 'Instalator Apă Brașov - Instalații Sanitare Apă Rece/Caldă | Bricli',
        'meta_description': 'Instalator apă în Brașov pentru instalații sanitare, țevi apă caldă/rece, reparații scurgeri. Primești oferte de la meșteri verificați în 2 ore. 100% GRATUIT!',
        'h1_title': 'Instalator Apă în Brașov - Instalații Sanitare Profesionale',
        'intro_text': 'Cauti un instalator apă în Brașov pentru instalații sanitare, reparații țevi sau probleme cu apa rece/caldă? Pe Bricli găsești meșteri verificați care intervin rapid. Primești oferte GRATUIT în maxim 2-4 ore și alegi pe cel mai bun.',
        'services_text': '''
## Servicii Instalator Apă Brașov

Instalatorii de apă din Brașov disponibili pe Bricli pot rezolva orice problemă legată de instalațiile sanitare:

### Instalații Apă Nouă
- Instalații apă rece/caldă pentru apartamente și case
- Montaj țevi apă (cupru, PPR, PEX, multicurve)
- Instalații sanitare complete pentru băi și bucătării
- Racorduri apă pentru mașini de spălat

### Reparații Instalații Apă
- Reparații țevi sparte sau fisură
- Înlocuire țevi vechi (cupru, fier, PVC)
- Reparații scurgeri de apă
- Reparații robinete care picură

### Servicii Urgență Apă
- Intervenții NON-STOP pentru țevi sparte
- Închidere apă și reparații de urgență
- Desfundare scurgeri apă
- Inlocuire robinet defect urgent

✓ **Meșteri cu experiență** în instalații sanitare și reparații apă
✓ **Răspuns rapid** în 2-4 ore, disponibili și în weekend
✓ **Garanție 2 ani** pentru toate lucrările executate
''',
        'prices_text': '''
## Prețuri Instalator Apă Brașov

### Instalații Apă Nouă
- **Instalație apă rece (per metru)**: 40-70 RON/ml
- **Instalație apă caldă (per metru)**: 50-80 RON/ml
- **Instalație apă baie completă**: 1500-3000 RON
- **Instalație apă apartament 2 camere**: 2500-4500 RON

### Reparații Apă
- **Reparație țeavă spartă**: 150-400 RON
- **Înlocuire robinet**: 100-250 RON
- **Înlocuire țeavă (per metru)**: 50-100 RON
- **Reparație scurgere apă**: 150-300 RON

### Intervenții Urgență
- **Intervenție urgență (țeavă spartă)**: 200-500 RON
- **Închidere apă + reparație provizorie**: 150-300 RON

**✓ Primești oferte GRATUIT** de la mai mulți instalatori apă și alegi pe cel cu cel mai bun preț.
''',
        'how_it_works_text': '''
## Cum Găsești Instalator Apă în Brașov pe Bricli

**1. Postezi cererea (2 minute)**
Descrie problema cu instalațiile de apă - țevi sparte, scurgeri, instalații noi etc.

**2. Primești oferte (2-4 ore)**
Instalatorii de apă din Brașov îți trimit oferte detaliate cu prețuri și timp de intervenție.

**3. Compari și alegi**
Vezi review-uri, portofolii și prețuri. Alegi instalatorul apă potrivit pentru tine.

**4. Programezi lucrarea**
Contactezi direct meșterul ales și programezi intervenția la apă.

✓ **100% GRATUIT** pentru clienți - postezi cererea și primești oferte fără niciun cost.
''',
        'craftsmen_count': 28,
        'reviews_count': 156,
        'faqs': [
            {
                'question': 'Cât costă instalarea țevilor de apă în Brașov?',
                'answer': 'Prețurile pentru instalații apă variază: 40-70 RON/metru pentru apă rece, 50-80 RON/metru pentru apă caldă. O instalație apă completă pentru baie costă între 1500-3000 RON. Prin Bricli primești oferte de la mai mulți instalatori și alegi cel mai bun preț.',
                'order': 1
            },
            {
                'question': 'Există instalatori de apă disponibili NON-STOP în Brașov?',
                'answer': 'Da! Pe Bricli găsești instalatori disponibili 24/7 pentru urgențe cu apa: țevi sparte, scurgeri mari, robinete defecte. Postează cererea și primești oferte rapid, chiar și în weekend sau noapte.',
                'order': 2
            },
            {
                'question': 'Ce tipuri de țevi de apă pot fi montate?',
                'answer': 'Instalatorii de apă de pe Bricli lucrează cu toate tipurile: țevi cupru (tradiționale, durabile), PPR (polipropilena, economice), PEX (flexibile, moderne), multicurve (aluminiu + plastic). Meșterul te va sfătui care varianta este cea mai bună pentru casa ta.',
                'order': 3
            },
            {
                'question': 'Cât durează o reparație la instalația de apă?',
                'answer': 'Depinde de problemă: o reparație simplă (robinet, țeavă spartă) durează 1-3 ore. Înlocuirea țevilor într-o baie poate dura 1-2 zile. Fiecare instalator îți oferă o estimare clară în oferta sa.',
                'order': 4
            },
            {
                'question': 'Trebuie să plătesc pentru ofertele de la instalatori?',
                'answer': 'Nu! Serviciul Bricli este 100% GRATUIT pentru clienți. Postezi cererea, primești oferte de la instalatori apă și alegi pe cel mai bun. Plătești doar pentru lucrarea efectuată, fără comisioane.',
                'order': 5
            }
        ]
    },
    {
        'city_name': 'Brașov',
        'profession': 'Reparații Instalații Sanitare',
        'meta_title': 'Reparații Instalații Sanitare Brașov - Urgent 24/7 | Bricli',
        'meta_description': 'Reparații instalații sanitare în Brașov: țevi sparte, robinete defecte, scurgeri. Meșteri verificați intervin rapid, chiar și NON-STOP. Primești oferte GRATUIT!',
        'h1_title': 'Reparații Instalații Sanitare Brașov - Intervenții Rapide',
        'intro_text': 'Ai nevoie de reparații la instalațiile sanitare în Brașov? Țevi sparte, robinete care picură, WC blocat sau scurgeri? Pe Bricli găsești instalatori verificați care intervin rapid, disponibili și NON-STOP pentru urgențe. Primești oferte GRATUIT în maxim 2 ore.',
        'services_text': '''
## Servicii Reparații Instalații Sanitare Brașov

### Reparații Urgente 24/7
- Țevi sparte sau fisură - intervenție rapidă
- Scurgeri mari de apă - închidere și reparație
- Robinete defecte care inundă
- WC blocat sau care curge continuu

### Reparații Instalații Apă
- Reparații țevi apă rece/caldă
- Înlocuire robinete și baterii
- Reparații racorduri apă
- Înlocuire țevi vechi (cupru, fier)

### Reparații Instalații Canalizare
- Desfundare WC, chiuvetă, cada
- Reparații țevi canalizare
- Înlocuire sifonuri defecte
- Reparații scurgeri canalizare

### Reparații Echipamente Sanitare
- Reparații rezervor WC
- Înlocuire mecanism WC
- Reparații/înlocuire chiuvete
- Reparații baterii băi

✓ **Disponibili NON-STOP** pentru urgențe sanitare
✓ **Garanție 2 ani** pentru toate reparațiile
''',
        'prices_text': '''
## Prețuri Reparații Instalații Sanitare Brașov

### Reparații Urgente
- **Intervenție urgență NON-STOP**: 200-500 RON
- **Reparație țeavă spartă**: 150-400 RON
- **Închidere apă + reparație provizorie**: 150-300 RON

### Reparații Standard
- **Reparație robinet/baterie**: 100-250 RON
- **Înlocuire robinet**: 150-300 RON
- **Reparație rezervor WC**: 100-200 RON
- **Înlocuire mecanism WC**: 150-300 RON

### Reparații Țevi și Canalizare
- **Desfundare WC/chiuvetă**: 150-300 RON
- **Înlocuire țeavă (per metru)**: 50-100 RON
- **Reparații canalizare**: 200-600 RON

**✓ Primești oferte de la mai mulți meșteri** și alegi cel mai avantajos preț pentru reparația ta.
''',
        'how_it_works_text': '''
## Cum Obții Reparații Rapide la Instalații Sanitare în Brașov

**1. Descrie problema (1 minut)**
Spune ce s-a stricat: țeavă spartă, robinet defect, WC blocat etc.

**2. Instalatorii răspund rapid (30min - 2 ore)**
Pentru urgențe, primești oferte în 30-60 minute. Pentru reparații standard, în 2-4 ore.

**3. Alegi meșterul potrivit**
Vezi review-uri, experiență și prețuri. Alegi instalatorul care se potrivește nevoilor tale.

**4. Reparația se execută**
Instalatorul intervine conform programării. Plătești doar după finalizarea lucrării.

✓ **Gratuit și rapid** - postezi cererea fără costuri și primești oferte de la profesioniști.
''',
        'craftsmen_count': 32,
        'reviews_count': 189,
        'faqs': [
            {
                'question': 'Cât costă o reparație urgentă la instalații sanitare în Brașov?',
                'answer': 'Pentru intervenții urgente NON-STOP (țevi sparte, scurgeri mari), prețurile pornesc de la 200-500 RON. Reparații standard (robinete, WC) costă 100-300 RON. Prin Bricli primești oferte exacte de la meșteri și alegi cel mai bun preț.',
                'order': 1
            },
            {
                'question': 'Cât de repede poate veni un instalator pentru o urgență?',
                'answer': 'Pentru urgențe (țevi sparte, inundații), instalatorii pot interveni în 30-90 minute, în funcție de disponibilitate și locație. Postează cererea și primești oferte rapide, chiar și în weekend sau noapte.',
                'order': 2
            },
            {
                'question': 'Oferă instalatorii garanție pentru reparații?',
                'answer': 'Da! Toți instalatorii verificați de pe Bricli oferă garanție pentru lucrările executate - de obicei 1-2 ani. Garanția acoperă manopera și piesele înlocuite.',
                'order': 3
            },
            {
                'question': 'Ce probleme pot rezolva instalatorii sanitari?',
                'answer': 'Instalatorii de pe Bricli rezolvă orice problemă: țevi sparte/fisură, robinete defecte, WC blocat sau care curge, scurgeri apă/canalizare, înlocuire echipamente sanitare, reparații centrale termice, boilere și multe altele.',
                'order': 4
            }
        ]
    },
    {
        'city_name': 'Brașov',
        'profession': 'Instalator Non-Stop',
        'meta_title': 'Instalator NON-STOP Brașov - Urgențe 24/7 | Bricli',
        'meta_description': 'Instalator NON-STOP în Brașov disponibil 24/7 pentru urgențe: țevi sparte, scurgeri, centrale termice. Intervenție rapidă în 30-90 minute. Postează cerere GRATUIT!',
        'h1_title': 'Instalator NON-STOP Brașov - Disponibil 24/7 pentru Urgențe',
        'intro_text': 'Ai o urgență cu instalațiile la orice oră? Țevi sparte, scurgeri, lipsa apei calde, centrală oprită? Pe Bricli găsești instalatori NON-STOP în Brașov disponibili 24/7, inclusiv weekend și sărbători. Postează cererea GRATUIT și primești oferte în 30-60 minute.',
        'services_text': '''
## Servicii Instalator NON-STOP Brașov

Instalatorii disponibili 24/7 în Brașov pot interveni imediat pentru orice urgență:

### Urgențe Instalații Apă
- **Țevi sparte** - închidere și reparație imediată
- **Scurgeri mari de apă** - intervenție rapidă
- **Robinete blocate/sparte** - înlocuire urgentă
- **Lipsa apei** - verificare și remediere sistem

### Urgențe Centrale Termice
- **Centrală oprită** - diagnoză și reparație
- **Lipsa apei calde** - intervenție imediată
- **Pierderi presiune** - verificare și remediere
- **Eroare centrală** - resetare și reparații

### Urgențe Canalizare
- **WC blocat** - desfundare rapidă
- **Canalizare înfundată** - desfundare profesională
- **Miros neplăcut** - verificare și remediere
- **Scurgere canalizare** - reparație urgentă

### Alte Urgențe Instalații
- **Boiler defect** - reparații NON-STOP
- **Robinetul nu se închide** - intervenție imediată
- **Inundație** - închidere apă și evaluare

✓ **Disponibili 24/7** - Luni-Duminică, inclusiv sărbători
✓ **Intervenție rapidă** - în 30-90 minute în funcție de zona din Brașov
✓ **Meșteri cu experiență** - echipați pentru orice tip de urgență
''',
        'prices_text': '''
## Prețuri Instalator NON-STOP Brașov

### Intervenții Urgență (24/7)
- **Deplasare urgență**: 50-100 RON
- **Diagnosticare problemă**: 50-150 RON
- **Închidere apă + reparație provizorie**: 150-300 RON
- **Reparație țeavă spartă (urgență)**: 200-500 RON

### Reparații Centrale NON-STOP
- **Diagnosticare + resetare centrală**: 150-300 RON
- **Reparație centrală (piese simple)**: 200-500 RON
- **Reparație boiler**: 200-400 RON

### Desfundări Urgență
- **Desfundare WC (urgență)**: 200-400 RON
- **Desfundare canalizare**: 250-600 RON

**✓ Tarife transparente** - instalatorul îți comunică costurile înainte de intervenție
**✓ Fără costuri ascunse** - plătești doar serviciile efectuate

**ℹ️ Notă:** Intervențiile NON-STOP (noapte, weekend, sărbători) pot avea un supliment de 20-30% față de tarifele normale.
''',
        'how_it_works_text': '''
## Cum Soliciți Instalator NON-STOP în Brașov

**1. Postezi cererea de urgență (1 minut)**
Descrie problema: țeavă spartă, centrală oprită, WC blocat etc. Specifică că este urgență.

**2. Instalatorii răspund RAPID (15-60 minute)**
Instalatorii NON-STOP disponibili în zona ta din Brașov îți trimit oferte imediat.

**3. Alegi și contactezi**
Vezi cine poate interveni cel mai repede și la ce preț. Suni direct meșterul.

**4. Intervenția se realizează**
Instalatorul vine în 30-90 minute și rezolvă problema. Plătești după finalizare.

✓ **Disponibil 24/7** - chiar și la 3 dimineața sau în weekend
✓ **Gratuit pentru clienți** - nu plătești pentru postarea cererii
''',
        'craftsmen_count': 18,
        'reviews_count': 94,
        'faqs': [
            {
                'question': 'Cât costă un instalator NON-STOP în Brașov?',
                'answer': 'Intervențiile NON-STOP au un supliment de 20-30% față de orele normale. De exemplu: deplasare urgență 50-100 RON, reparație țeavă spartă 200-500 RON, desfundare WC 200-400 RON. Instalatorul îți comunică tariful exact înainte de intervenție.',
                'order': 1
            },
            {
                'question': 'Cât de repede poate veni instalatorul pentru o urgență?',
                'answer': 'În funcție de disponibilitate și zona din Brașov, instalatorii pot interveni în 30-90 minute. Pentru urgențe majore (țevi sparte, inundații), mulți meșteri pot ajunge în 30-60 minute, chiar și noaptea sau în weekend.',
                'order': 2
            },
            {
                'question': 'Sunt disponibili instalatori NON-STOP și în weekend?',
                'answer': 'Da! Pe Bricli găsești instalatori disponibili 24/7, inclusiv Sâmbătă, Duminică și sărbători legale. Postează cererea oricând ai o urgență și vei primi oferte de la meșteri disponibili.',
                'order': 3
            },
            {
                'question': 'Ce echipamente au instalatorii pentru urgențe?',
                'answer': 'Instalatorii NON-STOP sunt echipați cu: scule de urgență, piese de schimb comune (robinete, sifonuri, ștuțuri), echipamente desfundare, scule pentru centrale termice. Pentru reparații complexe, pot programa o a doua vizită.',
                'order': 4
            },
            {
                'question': 'Trebuie să plătesc pentru postarea cererii de urgență?',
                'answer': 'Nu! Postarea cererii este 100% GRATUITĂ, indiferent de ora sau ziua. Plătești doar instalatorul ales, după ce finalizează intervenția. Nu există costuri ascunse sau comisioane.',
                'order': 5
            }
        ]
    },
    {
        'city_name': 'Brașov',
        'profession': 'Manoperă Instalator',
        'meta_title': 'Prețuri Manoperă Instalator Brașov 2025 - Tarife Actualizate | Bricli',
        'meta_description': 'Află prețurile pentru manoperă instalator în Brașov: instalații sanitare, centrale termice, reparații. Tarife clare 2025. Primești oferte GRATUIT de la meșteri verificați!',
        'h1_title': 'Prețuri Manoperă Instalator Brașov - Tarife 2025',
        'intro_text': 'Cauți informații despre prețurile pentru manoperă instalator în Brașov? Pe această pagină găsești toate tarifele actualizate 2025 pentru instalații sanitare, centrale termice, reparații și alte lucrări. Postează cererea pe Bricli și primești oferte GRATUIT de la instalatori verificați.',
        'services_text': '''
## Tarife Manoperă Instalator Brașov 2025

### Manoperă Instalații Sanitare
- **Instalație apă (per metru liniar)**: 40-80 RON/ml
- **Instalație canalizare (per metru)**: 30-60 RON/ml
- **Montaj chiuvetă/lavoar**: 150-300 RON
- **Montaj WC**: 200-400 RON
- **Montaj cadă**: 300-600 RON
- **Instalație baie completă**: 1500-3000 RON manoperă

### Manoperă Centrale Termice
- **Montaj centrală termică în condensare**: 800-1500 RON
- **Montaj centrală murală**: 500-1000 RON
- **Revizie centrală**: 200-400 RON
- **Igienizare centrală**: 300-500 RON
- **Înlocuire piesă centrală**: 150-400 RON

### Manoperă Încălzire
- **Montaj calorifer (per bucată)**: 150-300 RON
- **Montaj sistem încălzire în pardoseală**: 60-100 RON/mp
- **Racordare calorifer**: 100-200 RON
- **Spălare instalație încălzire**: 400-800 RON

### Manoperă Reparații
- **Reparație țeavă (per intervenție)**: 100-300 RON
- **Înlocuire robinet**: 80-200 RON
- **Desfundare WC/chiuvetă**: 150-300 RON
- **Reparație scurgere**: 150-400 RON

### Manoperă Boilere
- **Montaj boiler electric**: 200-400 RON
- **Montaj boiler pe gaz**: 400-700 RON
- **Decalcifiere boiler**: 200-350 RON

**ℹ️ Important:**
- Prețurile afișate sunt DOAR pentru manoperă (muncă)
- Materialele se achită separat (țevi, robinete, racorduri etc.)
- Tarifele pot varia în funcție de complexitatea lucrării
- Prin Bricli primești oferte detaliate cu manoperă + materiale
''',
        'prices_text': '''
## Cum se Calculează Manopera pentru Instalator?

### Factori care Influențează Tariful
1. **Complexitatea lucrării**: Instalații noi vs reparații simple
2. **Timpul necesar**: Lucrări de 1 oră vs proiecte de mai multe zile
3. **Accesibilitatea**: Spații greu accesibile pot crește tariful
4. **Urgența**: Intervenții NON-STOP au supliment 20-30%
5. **Experiența meșterului**: Instalatori cu experiență >10 ani pot taxa mai mult

### Exemple Concrete Manoperă

**Exemplu 1: Baie Nouă (3mp)**
- Instalație apă rece/caldă: 600-1000 RON
- Instalație canalizare: 400-700 RON
- Montaj WC: 250 RON
- Montaj chiuvetă: 200 RON
- Montaj cadă: 400 RON
- **TOTAL MANOPERĂ: 1850-2550 RON**

**Exemplu 2: Înlocuire Centrală Termică**
- Demontare centrală veche: 200 RON
- Montaj centrală nouă: 800 RON
- Racorduri și reglaje: 300 RON
- **TOTAL MANOPERĂ: 1300 RON**

**Exemplu 3: Reparație Urgență Țeavă Spartă**
- Deplasare urgență: 80 RON
- Diagnosticare: 100 RON
- Reparație țeavă: 250 RON
- **TOTAL MANOPERĂ: 430 RON**

### De ce să Folosești Bricli pentru Manoperă?

✓ **Compari mai multe oferte** - vezi exact cât costă manopera la fiecare meșter
✓ **Prețuri transparente** - fără costuri ascunse
✓ **Meșteri verificați** - experiență dovedită și review-uri reale
✓ **Gratuit pentru tine** - nu plătești pentru primirea ofertelor
''',
        'how_it_works_text': '''
## Cum Primești Oferte pentru Manoperă Instalator în Brașov

**1. Descrie lucrarea (2 minute)**
Specifică ce lucrări ai nevoie: instalații noi, reparații, centrale etc.

**2. Primești oferte detaliate (2-4 ore)**
Fiecare instalator îți trimite ofertă cu:
- Cost manoperă (pe fiecare operațiune)
- Cost materiale necesare
- Timp estimat de execuție
- Garanție oferită

**3. Compari ofertele**
Vezi cine oferă cel mai bun raport calitate-preț pentru manoperă.

**4. Alegi instalatorul**
Contactezi meșterul ales și programezi lucrarea.

**5. Plătești după finalizare**
Plătești instalatorul conform ofertei acceptate, după ce lucrarea este finalizată.

✓ **Zero costuri pentru tine** - serviciul Bricli este 100% gratuit pentru clienți
''',
        'craftsmen_count': 35,
        'reviews_count': 187,
        'faqs': [
            {
                'question': 'Cât costă manopera pentru un instalator în Brașov?',
                'answer': 'Tarifele variază: 40-80 RON/ml pentru instalații apă, 500-1500 RON montaj centrală, 150-300 RON montaj chiuvetă. Prin Bricli primești oferte detaliate de la mai mulți instalatori și compari prețurile.',
                'order': 1
            },
            {
                'question': 'Manopera include și materialele?',
                'answer': 'De obicei NU. Manopera reprezintă doar costul muncii instalatorului. Materialele (țevi, robinete, racorduri) se achită separat. În ofertele de pe Bricli, instalatorii specifică clar: X RON manoperă + Y RON materiale.',
                'order': 2
            },
            {
                'question': 'Pot negocia prețul manoperei cu instalatorul?',
                'answer': 'Da, poți discuta cu meșterul despre tarife, mai ales pentru lucrări mari. Pe Bricli primești oferte de la mai mulți instalatori, deci poți compara și alege cel mai bun preț sau negocia cu cel care îți place.',
                'order': 3
            },
            {
                'question': 'Se dă chitanță/factură pentru manoperă?',
                'answer': 'Da, instalatorii profesioniști emit chitanță sau factură fiscală pentru manoperă. Asigură-te că ceri dovada plății când achiti lucrarea. Instalatorii verificați de pe Bricli sunt profesioniști autorizați.',
                'order': 4
            },
            {
                'question': 'Manopera pentru urgențe costă mai mult?',
                'answer': 'Da, intervențiile NON-STOP (noapte, weekend, sărbători) au un supliment de 20-30% față de tarifele normale. De exemplu, o reparație care costă 200 RON ziua, poate costa 240-260 RON noaptea.',
                'order': 5
            }
        ]
    },
    {
        'city_name': 'Brașov',
        'profession': 'Prețuri Instalator',
        'meta_title': 'Prețuri Instalator Brașov 2025 - Tarife Complete | Bricli',
        'meta_description': 'Ghid complet prețuri instalator Brașov 2025: instalații sanitare, centrale termice, reparații. Află tarifele reale și primește oferte GRATUIT de la meșteri verificați!',
        'h1_title': 'Prețuri Instalator Brașov 2025 - Ghid Complet Tarife',
        'intro_text': 'Vrei să știi cât costă un instalator în Brașov? Pe această pagină găsești un ghid complet cu toate prețurile actualizate 2025: instalații sanitare, centrale termice, boilere, reparații urgente și multe altele. Postează cererea pe Bricli și primești oferte GRATUIT de la instalatori verificați din Brașov.',
        'services_text': '''
## Ghid Complet Prețuri Instalator Brașov 2025

### Prețuri Instalații Sanitare Noi

**Instalații Apă**
- Instalație apă rece (per metru): 40-70 RON/ml
- Instalație apă caldă (per metru): 50-80 RON/ml
- Instalație baie completă: 2000-4000 RON (manoperă + materiale)
- Instalație bucătărie: 800-1500 RON

**Instalații Canalizare**
- Canalizare interioară (per metru): 30-60 RON/ml
- Canalizare baie: 1000-2000 RON
- Montaj sistem scurgere: 500-1200 RON

**Montaj Echipamente Sanitare**
- Montaj WC suspendat: 300-500 RON
- Montaj WC normal: 200-350 RON
- Montaj chiuvetă/lavoar: 150-300 RON
- Montaj cadă: 400-700 RON
- Montaj cabină duș: 350-600 RON

### Prețuri Centrale Termice

**Montaj Centrale**
- Centrală murală pe gaz: 500-1200 RON (doar montaj)
- Centrală în condensare: 800-1500 RON (doar montaj)
- Centrală pe peleți: 1500-3000 RON (montaj complex)
- Centrală electrică: 400-800 RON

**Service Centrale**
- Revizie anuală: 200-400 RON
- Igienizare centrală: 300-600 RON
- Reparații centrale (piese minore): 200-500 RON
- Reparații majore: 500-1500 RON

### Prețuri Încălzire

**Calorifere**
- Montaj calorifer aluminiu: 150-300 RON/buc
- Montaj calorifer fontă: 200-350 RON/buc
- Înlocuire robinete calorifer: 80-150 RON/buc
- Spălare instalație încălzire: 500-1000 RON

**Încălzire în Pardoseală**
- Montaj sistem complet: 80-150 RON/mp
- Colectoare și distribuție: 800-1500 RON
- Hidroizolație + sistem: 100-180 RON/mp

### Prețuri Boilere

- Montaj boiler electric (50-100L): 250-400 RON
- Montaj boiler pe gaz: 500-800 RON
- Decalcifiere boiler: 200-400 RON
- Reparații boiler: 150-400 RON

### Prețuri Reparații Instalații

**Reparații Simple**
- Înlocuire robinet: 100-250 RON
- Reparație țeavă: 150-400 RON
- Desfundare WC/chiuvetă: 150-300 RON
- Înlocuire sifon: 80-150 RON

**Reparații Urgențe NON-STOP**
- Deplasare urgență: 50-120 RON
- Țeavă spartă (reparație urgentă): 250-600 RON
- Scurgere majoră: 200-500 RON
- Centrală oprită (resetare/reparație): 200-500 RON

### Prețuri Alte Servicii

- Montaj filtru apă: 150-350 RON
- Montaj pompă circulație: 200-400 RON
- Verificare presiune instalație: 100-200 RON
- Revizie instalație completă: 300-600 RON

**ℹ️ Note Importante:**
- Prețurile includ manoperă + materiale standard
- Pentru materiale premium (robinete scumpe, țevi cupru), prețul total crește
- Urgențele NON-STOP au supliment 20-30%
- Prețurile pot varia în funcție de zona din Brașov și complexitatea lucrării
''',
        'prices_text': '''
## Factori care Influențează Prețurile la Instalator

### 1. Tipul Lucrării
- **Instalații noi**: Costă mai mult (necesită materiale + timp)
- **Reparații**: Costuri mai mici, intervenții rapide
- **Urgențe**: Supliment 20-30% pentru NON-STOP

### 2. Complexitatea Proiectului
- **Lucrări simple** (schimbat robinet): 100-250 RON
- **Lucrări medii** (montaj centrală): 800-1500 RON
- **Proiecte complexe** (instalație completă casă): 5000-15000 RON

### 3. Materialele Folosite
- **Materiale standard** (PPR, robinete obișnuite): Preț mediu
- **Materiale premium** (cupru, robinete Grohe/Hansgrohe): +30-50% preț
- **Materiale de la client**: Plătești doar manopera

### 4. Experiența Instalatorului
- **Instalatori începători**: Tarife mai mici
- **Instalatori cu experiență 5-10 ani**: Tarife medii
- **Maeștri cu >10 ani experiență**: Tarife premium dar calitate garantată

### 5. Urgența Lucrării
- **Programare normală**: Tarif standard
- **Urgență în 2-4 ore**: +10-20%
- **Urgență NON-STOP** (noapte/weekend): +20-30%

## De ce Prețurile Variază?

Pe Bricli vei primi oferte diferite de la instalatori pentru aceeași lucrare. Acest lucru este normal:

✓ **Experiență diferită** - instalatori cu mai multă experiență taxează mai mult
✓ **Echipamente diferite** - unii au scule profesionale, alții standard
✓ **Garanții diferite** - garanție 2 ani vs 1 an
✓ **Materiale propuse** - unii propun materiale premium, alții standard
✓ **Disponibilitate** - cei mai solicitați au tarife mai mari

**Avantajul Bricli:** Primești 3-5 oferte și alegi pe cel care oferă cel mai bun raport calitate-preț pentru tine!
''',
        'how_it_works_text': '''
## Cum Obții Cele Mai Bune Prețuri la Instalator în Brașov

**1. Postează cererea detaliată (3 minute)**
Cu cât ești mai specific, cu atât ofertele vor fi mai precise:
- Descrie exact ce lucrări ai nevoie
- Precizează dacă ai materialele sau nu
- Menționează termenul dorit
- Atașează poze dacă este posibil

**2. Primești oferte de la 3-5 instalatori (2-4 ore)**
Fiecare instalator îți trimite ofertă cu:
- Preț total (manoperă + materiale)
- Detalii despre materialele propuse
- Timp de execuție
- Garanție oferită

**3. Analizezi ofertele**
- Compară prețurile (nu alege mereu cel mai ieftin!)
- Vezi review-urile fiecărui instalator
- Verifică portofoliul cu lucrări anterioare
- Citește evaluările de la clienți anteriori

**4. Pui întrebări instalatorilor**
- Cere clarificări despre materiale
- Întreabă despre experiența cu lucrări similare
- Verifică dacă prețul include TVA
- Negociază dacă e cazul

**5. Alegi și programezi**
- Alegi instalatorul potrivit
- Stabiliți detaliile finale
- Programați lucrarea
- Plătești după finalizare

## Sfaturi pentru Prețuri Bune

✓ **Postează cererea în afara sezonului de vârf** (evită iarna pentru centrale)
✓ **Compară minimum 3 oferte** înainte de a decide
✓ **Nu alege mereu cel mai ieftin** - verifică și calitatea
✓ **Cere garanție** pentru lucrările executate
✓ **Verifică ce include prețul** (manoperă, materiale, transport)
✓ **Negociază pentru proiecte mari** - instalatorii oferă discount pentru volume mari

**✓ Tot procesul este GRATUIT pentru tine** - nu plătești nimic pentru postarea cererii și primirea ofertelor!
''',
        'craftsmen_count': 42,
        'reviews_count': 234,
        'faqs': [
            {
                'question': 'Care sunt prețurile medii pentru un instalator în Brașov?',
                'answer': 'Prețurile variază: instalații apă 40-80 RON/metru, montaj centrală 500-1500 RON, reparații simple 150-400 RON, montaj baie completă 2000-4000 RON. Pe Bricli primești oferte exacte de la mai mulți instalatori și compari prețurile.',
                'order': 1
            },
            {
                'question': 'Prețurile includ materialele sau doar manopera?',
                'answer': 'Depinde de ofertă. Unii instalatori oferă preț "la cheie" (materiale + manoperă), alții doar manoperă. În ofertele de pe Bricli, fiecare instalator specifică clar ce include prețul. Poți cere orice variantă dorești.',
                'order': 2
            },
            {
                'question': 'De ce există diferențe mari de preț între instalatori?',
                'answer': 'Diferențele de preț apar din: experiența instalatorului (10+ ani vs începător), calitatea materialelor propuse (premium vs standard), garanția oferită (1 an vs 2 ani), și reputația meșterului. Prin Bricli poți compara și alege raportul calitate-preț potrivit.',
                'order': 3
            },
            {
                'question': 'Pot negocia prețurile cu instalatorii?',
                'answer': 'Da! Instalatorii sunt deschiși la negocieri, mai ales pentru: proiecte mari (instalații complete), lucrări multiple (mai multe băi), sau când programul este flexibil. Pe Bricli primești oferte de la mai mulți meșteri, deci ai putere de negociere.',
                'order': 4
            },
            {
                'question': 'Costă ceva să primesc oferte de preț de la instalatori?',
                'answer': 'Nu! Serviciul Bricli este 100% GRATUIT pentru clienți. Postezi cererea, primești oferte detaliate cu prețuri de la 3-5 instalatori verificați și alegi pe cel mai bun. Plătești doar lucrarea efectuată, fără comisioane.',
                'order': 5
            },
            {
                'question': 'Cum știu dacă un preț este corect sau prea mare?',
                'answer': 'Pe Bricli primești 3-5 oferte pentru aceeași lucrare, deci vei vedea imediat care este prețul de piață. Dacă o ofertă este mult mai scumpă decât celelalte, poți întreba instalatorul de ce (poate folosește materiale premium sau oferă garanție extinsă).',
                'order': 6
            }
        ]
    }
]


def create_priority_pages():
    """Create 5 high-priority landing pages targeting competitor keywords"""
    created_count = 0
    skipped_count = 0

    print(f"Creating {len(PRIORITY_PAGES)} high-priority landing pages...\n")

    for page_data in PRIORITY_PAGES:
        faqs_data = page_data.pop('faqs', [])

        # Check if page already exists
        existing = CityLandingPage.objects.filter(
            city_name=page_data['city_name'],
            profession=page_data['profession']
        ).first()

        if existing:
            print(f"⊘ {page_data['profession']} {page_data['city_name']} already exists, skipping")
            skipped_count += 1
            continue

        # Create the landing page
        page = CityLandingPage.objects.create(**page_data)

        # Create FAQs for this page
        for faq_data in faqs_data:
            CityLandingFAQ.objects.create(
                landing_page=page,
                **faq_data,
                is_active=True
            )

        print(f"✓ Created {page.profession} {page.city_name} with {len(faqs_data)} FAQs")
        created_count += 1

    print(f"\n{'='*60}")
    print(f"SUMMARY: Created {created_count} pages, skipped {skipped_count} pages")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("Creating high-priority landing pages for competitor keywords...\n")
    create_priority_pages()
    print("\n✓ Priority pages creation complete!")
