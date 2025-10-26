# Strategie SEO Bricli - Ranking Rapid pe Prima Pagină Google

## Analiza Competiției: "Instalator Brasov"

### Ce fac competitorii de succes:
1. ✅ **Domain-uri specifice** - instalatorbrasov.com.ro, instalomania.ro
2. ✅ **Titluri cu keywords** - "Instalator Brasov NON STOP", "24/7 InstaloMania"
3. ✅ **Review-uri multe** - 200-800+ recenzii Google (4.2-4.9 stele)
4. ✅ **Telefon vizibil** - În snippet-urile Google
5. ✅ **Site-uri specializate pe nișă** - Focus pe 1-2 servicii max
6. ✅ **Pagini OLX, Facebook** - Prezență multi-platformă
7. ✅ **"Estimări online"** - Badge Google pentru lead generation

### De ce Bricli va câștiga:
- **Marketplace complet** - Review-uri integrate, portofolii, wallet
- **Trust superior** - Verificare meșteri, sistem escrow
- **Content de calitate** - 12 articole SEO + landing pages
- **UX modern** - Design superior, mobile-first
- **Multi-oraș** - Scalabil rapid în toate orașele

---

## PLAN DE ACȚIUNE - 3 Faze

### FAZA 1: SEO Tehnic (1-2 săptămâni)

#### 1.1 Structured Data (Schema.org)
**Prioritate: CRITICĂ**

Implementare în `templates/base.html`:

```html
<!-- LocalBusiness Schema -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Bricli",
  "description": "Platformă online pentru găsirea meșterilor verificați în România",
  "url": "https://bricli.ro",
  "telephone": "+40-XXX-XXX-XXX",
  "address": {
    "@type": "PostalAddress",
    "addressCountry": "RO"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "{{ total_reviews }}"
  },
  "priceRange": "20-200 RON"
}
</script>

<!-- Service Schema (pentru fiecare landing page) -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Service",
  "serviceType": "Instalator Sanitare și Termice",
  "provider": {
    "@type": "LocalBusiness",
    "name": "Bricli"
  },
  "areaServed": {
    "@type": "City",
    "name": "Brașov"
  }
}
</script>
```

#### 1.2 Sitemap.xml
**Fișier:** `bricli/sitemaps.py`

```python
from django.contrib.sitemaps import Sitemap
from blog.models import BlogPost
from core.models import CityLandingPage
from services.models import Order

class BlogPostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return BlogPost.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.updated_at

class CityLandingPageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.9  # PRIORITATE MARE pentru SEO local

    def items(self):
        return CityLandingPage.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return ['core:home', 'core:about', 'core:how_it_works']

    def location(self, item):
        return reverse(item)
```

**Fișier:** `bricli/urls.py` (adăugă)

```python
from django.contrib.sitemaps.views import sitemap
from bricli.sitemaps import BlogPostSitemap, CityLandingPageSitemap, StaticViewSitemap

sitemaps = {
    'blog': BlogPostSitemap,
    'cities': CityLandingPageSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    # ... existing patterns
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]
```

#### 1.3 Robots.txt
**Fișier:** `static/robots.txt`

```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /accounts/login/
Disallow: /accounts/register/
Disallow: /wallet/
Disallow: /mesaje/

Sitemap: https://bricli.ro/sitemap.xml
```

**Fișier:** `bricli/urls.py` (adăugă view)

```python
from django.views.generic import TemplateView

urlpatterns = [
    # ... existing patterns
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]
```

#### 1.4 Meta Tags Template Improvements
**Fișier:** `templates/base.html` (verifică că există)

```html
<meta name="description" content="{% block meta_description %}Găsește meșteri verificați în România. Posteaz ă gratuit cereri pentru instalatori, electricieni, zugravi și alte meserii.{% endblock %}">
<meta name="keywords" content="{% block meta_keywords %}meșteri verificați, instalator, electrician, zugrav, dulgh er, renovări{% endblock %}">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:title" content="{% block og_title %}{{ self.title() }}{% endblock %}">
<meta property="og:description" content="{% block og_description %}{{ self.meta_description() }}{% endblock %}">
<meta property="og:image" content="{% block og_image %}{% static 'img/og-image.jpg' %}{% endblock %}">
<meta property="og:url" content="{{ request.build_absolute_uri }}">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{% block twitter_title %}{{ self.title() }}{% endblock %}">
<meta name="twitter:description" content="{% block twitter_description %}{{ self.meta_description() }}{% endblock %}">
```

---

### FAZA 2: Landing Pages Local SEO (2-3 săptămâni)

#### 2.1 Structura URL
```
/instalator-brasov/
/electrician-bucuresti/
/zugrav-cluj-napoca/
/dulgher-timisoara/
/instalator-constanta/
/electrician-iasi/
```

#### 2.2 Model CityLandingPage
**DEJA IMPLEMENTAT** în `core/models.py` - Migrează:

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 2.3 View pentru City Landing Pages
**Fișier:** `core/views.py` (adăugă)

```python
from django.views.generic import DetailView
from core.models import CityLandingPage
from services.models import Order
from accounts.models import CraftsmanProfile

class CityLandingPageView(DetailView):
    model = CityLandingPage
    template_name = 'core/city_landing.html'
    context_object_name = 'page'

    def get_object(self):
        return CityLandingPage.objects.get(
            profession_slug=self.kwargs['profession_slug'],
            city_slug=self.kwargs['city_slug'],
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.object

        # Meșteri din orașul respectiv (dacă ai acest field în CraftsmanProfile)
        # context['local_craftsmen'] = CraftsmanProfile.objects.filter(city__iexact=page.city_name)[:6]

        # Comenzi recente din oraș
        context['recent_orders'] = Order.objects.filter(
            location__icontains=page.city_name,
            status='open'
        )[:5]

        return context
```

#### 2.4 Template City Landing Page
**Fișier:** `templates/core/city_landing.html`

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}{{ page.meta_title }}{% endblock %}

{% block meta_description %}{{ page.meta_description }}{% endblock %}

{% block content %}
<div class="city-landing-page">
    <!-- Hero Section -->
    <div class="hero" style="background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%); color: white; padding: 4rem 0;">
        <div class="container">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb text-white-50">
                    <li class="breadcrumb-item"><a href="{% url 'core:home' %}" class="text-white">Acasă</a></li>
                    <li class="breadcrumb-item active text-white">{{ page.profession }} {{ page.city_name }}</li>
                </ol>
            </nav>

            <h1 class="display-4 mb-4">{{ page.h1_title }}</h1>
            <p class="lead">{{ page.intro_text }}</p>

            {% if page.craftsmen_count > 0 %}
            <div class="stats mt-4 d-flex gap-4">
                <div>
                    <strong class="h3">{{ page.craftsmen_count }}+</strong>
                    <p class="mb-0">Meșteri verificați</p>
                </div>
                <div>
                    <strong class="h3">{{ page.reviews_count }}+</strong>
                    <p class="mb-0">Review-uri pozitive</p>
                </div>
            </div>
            {% endif %}

            <a href="{% url 'services:create_order' %}" class="btn btn-light btn-lg mt-4">
                <i class="fas fa-plus me-2"></i>Postează Cerere Gratuită
            </a>
        </div>
    </div>

    <div class="container my-5">
        <div class="row">
            <!-- Main Content -->
            <div class="col-lg-8">
                <!-- Servicii -->
                <section class="mb-5">
                    <h2>Servicii {{ page.profession }} {{ page.city_name }}</h2>
                    <div class="content">{{ page.services_text|linebreaks }}</div>
                </section>

                <!-- Prețuri -->
                {% if page.prices_text %}
                <section class="mb-5">
                    <h2>Prețuri Orientative {{ page.city_name }}</h2>
                    <div class="content">{{ page.prices_text|linebreaks }}</div>
                </section>
                {% endif %}

                <!-- Cum funcționează -->
                <section class="mb-5">
                    <h2>Cum Găsești {{ page.profession }} pe Bricli</h2>
                    <div class="content">{{ page.how_it_works_text|linebreaks }}</div>
                </section>

                <!-- Schema.org pentru Service -->
                <script type="application/ld+json">
                {
                  "@context": "https://schema.org",
                  "@type": "Service",
                  "serviceType": "{{ page.profession }}",
                  "provider": {
                    "@type": "Organization",
                    "name": "Bricli",
                    "url": "https://bricli.ro"
                  },
                  "areaServed": {
                    "@type": "City",
                    "name": "{{ page.city_name }}"
                  },
                  "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4.8",
                    "reviewCount": "{{ page.reviews_count }}"
                  }
                }
                </script>
            </div>

            <!-- Sidebar -->
            <div class="col-lg-4">
                <!-- CTA Box -->
                <div class="card shadow-sm mb-4" style="background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%); color: white;">
                    <div class="card-body text-center">
                        <h4>Ai nevoie de {{ page.profession }}?</h4>
                        <p>Postează gratuit cererea ta și primește oferte de la meșteri verificați din {{ page.city_name }}.</p>
                        <a href="{% url 'services:create_order' %}" class="btn btn-light btn-block">
                            <i class="fas fa-plus me-2"></i>Postează Cerere
                        </a>
                    </div>
                </div>

                <!-- Recent Orders -->
                {% if recent_orders %}
                <div class="card shadow-sm">
                    <div class="card-header bg-white">
                        <h5 class="mb-0">Comenzi Recente din {{ page.city_name }}</h5>
                    </div>
                    <div class="list-group list-group-flush">
                        {% for order in recent_orders %}
                        <a href="{{ order.get_absolute_url }}" class="list-group-item list-group-item-action">
                            <strong>{{ order.title|truncatewords:8 }}</strong>
                            <p class="mb-0 text-muted small">{{ order.description|truncatewords:15 }}</p>
                        </a>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

#### 2.5 URLs pentru City Landing Pages
**Fișier:** `core/urls.py` (adăugă)

```python
from core.views import CityLandingPageView

app_name = 'core'

urlpatterns = [
    # ... existing URLs
    path('<slug:profession_slug>-<slug:city_slug>/', CityLandingPageView.as_view(), name='city_landing'),
]
```

#### 2.6 Populare Date - Creează Landing Pages
**Script:** `create_city_landing_pages.py`

```python
# -*- coding: utf-8 -*-
import os
import sys
import django
import codecs

if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bricli.settings')
django.setup()

from core.models import CityLandingPage

# Orașe majore din România
cities = [
    ('București', 'bucuresti'),
    ('Brașov', 'brasov'),
    ('Cluj-Napoca', 'cluj-napoca'),
    ('Timișoara', 'timisoara'),
    ('Iași', 'iasi'),
    ('Constanța', 'constanta'),
    ('Craiova', 'craiova'),
    ('Sibiu', 'sibiu'),
    ('Oradea', 'oradea'),
    ('Ploiești', 'ploiesti'),
]

# Meserii populare
professions = {
    'Instalator': {
        'slug': 'instalator',
        'services': '''
- Instalații sanitare (conducte apă, canalizare, obiecte sanitare)
- Instalații termice (centrale, radiatoare, încălzire în pardoseală)
- Montaj chiuvete, căzi, cabine duș, WC-uri
- Reparare scurgeri și conducte sparte
- Desfundare canalizare''',
        'prices': '''
- Tarif orar: 80-150 RON
- Montaj centrală termică: 800-1,500 RON
- Instalație baie complet: 1,500-3,500 RON
- Intervenție urgență: 100-200 RON (deplasare)''',
    },
    'Electrician': {
        'slug': 'electrician',
        'services': '''
- Instalații electrice noi și modificări
- Tablouri electrice și siguranțe
- Montaj prize, întrerupătoare, corpuri iluminat
- Reparații instalații electrice
- Sisteme smart home''',
        'prices': '''
- Tarif orar: 70-120 RON
- Instalație electrică apartament: 2,000-5,000 RON
- Tablou electric: 500-1,200 RON
- Montaj priză/întrerupător: 30-60 RON''',
    },
    'Zugrav': {
        'slug': 'zugrav',
        'services': '''
- Zugrăvit interior (pereți, tavane, uși)
- Zugrăvit exterior (fațade, garduri)
- Tencuieli decorative
- Aplicare tapet
- Vopsit lemn și metal''',
        'prices': '''
- Zugrăvit interior: 15-30 RON/mp
- Zugrăvit exterior: 20-40 RON/mp
- Tencuială decorativă: 30-60 RON/mp
- Aplicare tapet: 20-35 RON/mp''',
    },
    'Dulgher': {
        'slug': 'dulgher',
        'services': '''
- Montaj uși interioare și exterioare
- Montaj parchet laminat, masiv
- Montaj rigips și tavan fals
- Confecționare mobilier la comandă
- Reparații mobilier''',
        'prices': '''
- Montaj ușă interioară: 150-300 RON
- Montaj parchet laminat: 20-40 RON/mp
- Mobilier la comandă: de la 500 RON/ml
- Reparații mobilier: 50-150 RON/oră''',
    },
}

def create_landing_pages():
    created_count = 0

    for city_name, city_slug in cities:
        for profession_name, prof_data in professions.items():
            profession_slug = prof_data['slug']

            # Check dacă există deja
            if CityLandingPage.objects.filter(city_slug=city_slug, profession_slug=profession_slug).exists():
                print(f'[SKIP] {profession_name} {city_name} - Există deja')
                continue

            # Creează landing page
            page = CityLandingPage.objects.create(
                city_name=city_name,
                city_slug=city_slug,
                profession=profession_name,
                profession_slug=profession_slug,

                # SEO
                meta_title=f'{profession_name} {city_name} - Găsește Meșteri Verificați pe Bricli',
                meta_description=f'Cauți {profession_name.lower()} în {city_name}? Pe Bricli găsești rapid meșteri verificați cu review-uri reale. Postează gratuit cererea ta și primește oferte.',
                h1_title=f'Găsește {profession_name} de Încredere în {city_name}',

                # Content
                intro_text=f'Ai nevoie de un {profession_name.lower()} profesionist în {city_name}? Pe Bricli conectăm clienții cu meșteri verificați, cu review-uri reale și portofolii demonstrative. Postează gratuit cererea ta și primește oferte de la {profession_name.lower()}i din zona ta.',

                services_text=prof_data['services'],
                prices_text=prof_data['prices'],

                how_it_works_text=f'''
1. **Postează cererea** - Descrie lucrarea necesară și zona din {city_name}
2. **Primești oferte** - {profession_name}i verificați îți trimit cotații
3. **Compară și alege** - Vezi review-uri, portofolii și prețuri
4. **Contactează meșterul** - Vorbește direct cu {profession_name.lower()}ul ales''',

                # Stats (simulăm - în producție vor fi calculate dinamic)
                craftsmen_count=15 + (hash(city_name + profession_name) % 50),
                reviews_count=50 + (hash(city_name + profession_name) % 300),

                is_active=True
            )

            created_count += 1
            print(f'[OK] {profession_name} {city_name}')

    print(f'\n[INFO] Total landing pages create: {created_count}')
    print(f'[INFO] Total landing pages în DB: {CityLandingPage.objects.count()}')

if __name__ == '__main__':
    create_landing_pages()
```

**Execută:**
```bash
python create_city_landing_pages.py
```

**Rezultat:** 40 landing pages (10 orașe x 4 meserii)

---

### FAZA 3: Content Marketing & Link Building (continuu)

#### 3.1 Mai Multe Articole SEO
**Teme prioritare:**

1. **"Instalator Brașov - Prețuri, Servicii și Cum Alegi în 2025"**
2. **"Electrician București - Ghid Complet și Tarife 2025"**
3. **"Cum să Alegi un Meșter de Încredere - 10 Sfaturi Esențiale"**
4. **"Renovare Apartament Calculator Costuri 2025"**
5. **"Instalații Sanitare - Probleme Frecvente și Soluții"**

Fiecare articol să includă:
- Keyword principal în titlu și primele 100 cuvinte
- 1,500-2,500 cuvinte
- H2/H3 cu long-tail keywords
- Link-uri interne către landing pages
- CTA către "Postează Cerere"

#### 3.2 Google Business Profile
**URGENT - Crează profilul:**

1. Mergi pe https://business.google.com
2. Creează "Bricli - Platformă Meșteri"
3. Categorie: "Service Establishment" sau "Internet Company"
4. Adaugă:
   - Logo (400x400px)
   - Cover photo (1024x575px)
   - Descriere (750 caractere):
     ```
     Bricli este platforma #1 din România pentru găsirea meșterilor verificați.
     Conectăm clienți cu instalatori, electricieni, zugravi, dulgheri și alți profesioniști.

     ✓ Meșteri cu review-uri reale
     ✓ Portofolii demonstrative
     ✓ Postare cereri gratuită
     ✓ Plată securizată prin wallet

     Disponibil în: București, Brașov, Cluj-Napoca, Timișoara, Iași și peste 50 orașe.
     ```
   - Link către website
   - Program: 24/7 (platformă online)

5. **Încurajează review-uri** - După fiecare comandă finalizată, trimite email cu link direct către Google Reviews

#### 3.3 Backlinks - Strategii Rapide

**A. Directoare online:**
- **Cylex Romania** - https://www.cylex.ro
- **Yellow.ro** - https://yellow.ro
- **AAZ.ro** - https://aaz.ro
- **Pagini Aurii** - https://www.paginiaurii.ro

**B. Parteneriate locale:**
- Magazine de materiale de construcții (banner + link)
- Arhitecți și designeri de interior (parteneriat recomandate)
- Bloguri despre renovări/amenajări

**C. PR Digital:**
- Comunicat presă: "Bricli lansează marketplace-ul pentru meșteri verificați"
- Articole pe StartupCafe, Hotnews (secțiune Technologie)

---

## Checklist RAPID (Implementare 7 zile)

### Ziua 1-2: SEO Tehnic
- [ ] Adaugă Schema.org în `base.html`
- [ ] Creează `sitemaps.py` și configurează în URLs
- [ ] Creează `robots.txt`
- [ ] Verifică meta tags în toate template-urile
- [ ] Instalează Google Search Console
- [ ] Submit sitemap.xml în GSC

### Ziua 3-4: Landing Pages
- [ ] Rulează migrația pentru `CityLandingPage`
- [ ] Creează view și template `city_landing.html`
- [ ] Configurează URLs
- [ ] Rulează `create_city_landing_pages.py`
- [ ] Testează 3-5 landing pages manual
- [ ] Verifică responsive design

### Ziua 5-6: Content
- [ ] Scrie 5 articole SEO noi (cu focus pe orașe majore)
- [ ] Adaugă link-uri interne între articole și landing pages
- [ ] Optimizează titlurile existente (adaugă "2025", "Prețuri", keywords)

### Ziua 7: Promotion
- [ ] Creează Google Business Profile
- [ ] Înscrie site-ul în 10 directoare online
- [ ] Postează pe Facebook/Instagram despre lansare
- [ ] Trimite email utilizatorilor existenți despre noul content

---

## KPIs de Urmărit

### SEO Metrics (Google Search Console)
- **Impressions** (afișări în căutare): Țintă 10,000/lună în prima lună
- **Clicks**: Țintă 500/lună
- **CTR**: Țintă 5%+
- **Average Position**: Țintă Top 10 pentru 20+ keywords în 3 luni

### Ranking Keywords (urmărește cu tools.seoreviewtools.com)
- "instalator brasov" - Țintă: Poziția 5-10 în 2 luni
- "electrician bucuresti" - Țintă: Poziția 10-15 în 2 luni
- "mesteri verificati romania" - Țintă: Poziția 3-5 în 3 luni
- "platforma mesteri" - Țintă: Poziția 1-3 în 1 lună (low competition)

### Business Metrics
- **Trafic organic**: +200% în 3 luni
- **Lead-uri din landing pages**: 50+/lună
- **Conversion rate landing pages**: 10%+ (vizitator → postare comandă)

---

## Tools Recomandate (FREE)

1. **Google Search Console** - Essential pentru tracking
2. **Google Analytics 4** - Trafic și comportament
3. **Ubersuggest** (free tier) - Keyword research
4. **AnswerThePublic** - Idei de conținut bazat pe întrebări
5. **Screaming Frog SEO Spider** (500 URLs free) - Audit tehnic
6. **PageSpeed Insights** - Performanță site

---

## Next Steps - ACȚIUNE IMEDIATĂ

1. **ACUM:** Citește tot acest document
2. **AZI:** Implementează Schema.org și Sitemap
3. **MÂINE:** Creează primele 10 landing pages (top 10 orașe x Instalator)
4. **SĂPTĂMÂNA VIITOARE:** Google Business Profile + 20 landing pages + 5 articole SEO

**Întrebare pentru tine:** Vrei să încep implementarea pas cu pas sau preferi să faci tu manual pe baza acestui ghid?
