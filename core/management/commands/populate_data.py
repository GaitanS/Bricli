from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import County, City, User, CraftsmanProfile
from services.models import ServiceCategory, Service
from core.models import SiteSettings, FAQ, Testimonial


class Command(BaseCommand):
    help = 'Populate database with initial data for Romania'

    def handle(self, *args, **options):
        self.stdout.write('Populating database with initial data...')
        
        with transaction.atomic():
            # Create counties
            self.create_counties()
            
            # Create service categories
            self.create_service_categories()
            
            # Create site settings
            self.create_site_settings()
            
            # Create FAQs
            self.create_faqs()
            
            # Create testimonials
            self.create_testimonials()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))

    def create_counties(self):
        counties_data = [
            ('Alba', 'AB'), ('Arad', 'AR'), ('Argeș', 'AG'), ('Bacău', 'BC'),
            ('Bihor', 'BH'), ('Bistrița-Năsăud', 'BN'), ('Botoșani', 'BT'),
            ('Brașov', 'BV'), ('Brăila', 'BR'), ('București', 'B'),
            ('Buzău', 'BZ'), ('Caraș-Severin', 'CS'), ('Călărași', 'CL'),
            ('Cluj', 'CJ'), ('Constanța', 'CT'), ('Covasna', 'CV'),
            ('Dâmbovița', 'DB'), ('Dolj', 'DJ'), ('Galați', 'GL'),
            ('Giurgiu', 'GR'), ('Gorj', 'GJ'), ('Harghita', 'HR'),
            ('Hunedoara', 'HD'), ('Ialomița', 'IL'), ('Iași', 'IS'),
            ('Ilfov', 'IF'), ('Maramureș', 'MM'), ('Mehedinți', 'MH'),
            ('Mureș', 'MS'), ('Neamț', 'NT'), ('Olt', 'OT'),
            ('Prahova', 'PH'), ('Satu Mare', 'SM'), ('Sălaj', 'SJ'),
            ('Sibiu', 'SB'), ('Suceava', 'SV'), ('Teleorman', 'TR'),
            ('Timiș', 'TM'), ('Tulcea', 'TL'), ('Vaslui', 'VS'),
            ('Vâlcea', 'VL'), ('Vrancea', 'VN')
        ]
        
        for name, code in counties_data:
            county, created = County.objects.get_or_create(name=name, code=code)
            if created:
                self.stdout.write(f'Created county: {name}')

        # Create some major cities
        cities_data = [
            ('București', 'București'), ('Cluj-Napoca', 'Cluj'), ('Timișoara', 'Timiș'),
            ('Iași', 'Iași'), ('Constanța', 'Constanța'), ('Craiova', 'Dolj'),
            ('Brașov', 'Brașov'), ('Galați', 'Galați'), ('Ploiești', 'Prahova'),
            ('Oradea', 'Bihor'), ('Brăila', 'Brăila'), ('Arad', 'Arad'),
            ('Pitești', 'Argeș'), ('Sibiu', 'Sibiu'), ('Bacău', 'Bacău'),
            ('Târgu Mureș', 'Mureș'), ('Baia Mare', 'Maramureș'), ('Buzău', 'Buzău'),
            ('Botoșani', 'Botoșani'), ('Satu Mare', 'Satu Mare')
        ]
        
        for city_name, county_name in cities_data:
            try:
                county = County.objects.get(name=county_name)
                city, created = City.objects.get_or_create(name=city_name, county=county)
                if created:
                    self.stdout.write(f'Created city: {city_name}')
            except County.DoesNotExist:
                self.stdout.write(f'County {county_name} not found for city {city_name}')

    def create_service_categories(self):
        categories_data = [
            # Construction & Building
            ('Tâmplărie și Dulgherie', 'tamplarie-dulgherie', 'fas fa-hammer', 'Mobilier, uși, ferestre, structuri din lemn'),
            ('Instalații Sanitare', 'instalatii-sanitare', 'fas fa-wrench', 'Instalații sanitare, reparații țevi, montaj obiecte sanitare'),
            ('Instalații Electrice', 'instalatii-electrice', 'fas fa-bolt', 'Instalații electrice, reparații, montaj prize și întrerupătoare'),
            ('Renovări și Construcții', 'renovari-constructii', 'fas fa-hard-hat', 'Renovări complete, construcții noi, amenajări interioare'),
            ('Acoperișuri', 'acoperisuri', 'fas fa-home', 'Montaj și reparații acoperișuri, jgheaburi'),
            ('Zidărie și Beton', 'zidarie-beton', 'fas fa-cube', 'Lucrări de zidărie, turnare beton, fundații'),

            # Specialized Services
            ('Parchet și Gresie', 'parchet-gresie', 'fas fa-th-large', 'Montaj parchet, gresie, faianță, finisaje'),
            ('Pictură și Vopsitorie', 'pictura-vopsitorie', 'fas fa-paint-roller', 'Vopsit pereți, zugrăveli, finisaje decorative'),
            ('Instalații de Încălzire', 'instalatii-incalzire', 'fas fa-fire', 'Centrale termice, calorifere, încălzire în pardoseală'),
            ('Geamuri și Ferestre', 'geamuri-ferestre', 'fas fa-window-maximize', 'Montaj ferestre, uși, markize'),
            ('Curățenie și Menaj', 'curatenie-menaj', 'fas fa-broom', 'Servicii de curățenie profesională, menaj'),

            # Outdoor & Garden
            ('Grădinărit și Peisagistică', 'gradinarit-peisagistica', 'fas fa-seedling', 'Amenajări grădini, întreținere spații verzi'),
            ('Pavaje și Alei', 'pavaje-alei', 'fas fa-road', 'Pavaje, alei, terase exterioare'),
            ('Demolări și Debarasări', 'demolari-debarasari', 'fas fa-trash', 'Demolări, debarasări, evacuări'),
            ('Piscine', 'piscine', 'fas fa-swimming-pool', 'Construcție și întreținere piscine'),

            # Transport & Assembly
            ('Mutări și Transport', 'mutari-transport', 'fas fa-truck', 'Servicii de mutare, transport marfă'),
            ('Asamblare și Montaj', 'asamblare-montaj', 'fas fa-tools', 'Asamblare mobilier, montaj diverse'),

            # Interior & Design
            ('Design Interior', 'design-interior', 'fas fa-couch', 'Proiectare și amenajare spații interioare'),
            ('Tapițerie și Decorațiuni', 'tapiterie-decoratiuni', 'fas fa-chair', 'Tapițerie, decorațiuni textile'),

            # Specialized Trades
            ('Lucrări Metalice', 'lucrari-metalice', 'fas fa-industry', 'Construcții metalice, sudură, fier forjat'),
            ('Sticlărie', 'sticlarie', 'fas fa-glass-martini', 'Montaj geamuri, oglinzi, lucrări din sticlă'),
            ('IT și Tehnologie', 'it-tehnologie', 'fas fa-laptop', 'Reparații calculatoare, instalări software, rețele'),
            ('Reparații Auto', 'reparatii-auto', 'fas fa-car', 'Reparații auto, service, întreținere vehicule'),
            ('Șeminee și Coșuri', 'seminee-cosuri', 'fas fa-fire-alt', 'Construcție șeminee, curățare coșuri'),
        ]
        
        for name, slug, icon, description in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slug,
                    'icon': icon,
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created service category: {name}')

    def create_site_settings(self):
        settings, created = SiteSettings.objects.get_or_create(
            id=1,
            defaults={
                'site_name': 'Bricli',
                'site_description': 'Platforma care conectează clienții cu meșteri verificați din România',
                'contact_email': 'contact@bricli.ro',
                'contact_phone': '+40 21 123 4567',
                'total_craftsmen': 1250,
                'total_completed_jobs': 5680,
                'total_reviews': 3420
            }
        )
        if created:
            self.stdout.write('Created site settings')

    def create_faqs(self):
        faqs_data = [
            ('Cum funcționează Bricli?', 'Bricli este o platformă care conectează clienții cu meșteri verificați. Postezi o cerere, primești oferte și alegi meșterul potrivit.', 'General'),
            ('Este gratuit să postez o cerere?', 'Da, postarea cererilor este complet gratuită pentru clienți. Plătești doar pentru serviciul prestat de meșter.', 'General'),
            ('Cum sunt verificați meșterii?', 'Toți meșterii sunt verificați prin documente de identitate, certificări profesionale și referințe anterioare.', 'Meșteri'),
            ('Pot anula o comandă?', 'Da, poți anula o comandă înainte ca aceasta să fie acceptată de un meșter. După acceptare, discută cu meșterul pentru modificări.', 'Comenzi'),
            ('Cum las o recenzie?', 'După finalizarea lucrării, vei primi o notificare pentru a lăsa o recenzie despre experiența ta cu meșterul.', 'Recenzii'),
        ]
        
        for question, answer, category in faqs_data:
            faq, created = FAQ.objects.get_or_create(
                question=question,
                defaults={
                    'answer': answer,
                    'category': category,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created FAQ: {question[:50]}...')

    def create_testimonials(self):
        testimonials_data = [
            ('Maria Popescu', 'București', 'Am găsit un electrician excelent prin Bricli. Lucrarea a fost făcută profesional și la timp!', 5, True),
            ('Ion Georgescu', 'Cluj-Napoca', 'Platforma foarte ușor de folosit. Am primit 3 oferte în prima zi și am ales cel mai bun preț.', 5, True),
            ('Ana Dumitrescu', 'Timișoara', 'Meșterul găsit prin Bricli a renovat complet baia. Rezultatul a depășit așteptările!', 5, True),
        ]
        
        for name, location, content, rating, is_featured in testimonials_data:
            testimonial, created = Testimonial.objects.get_or_create(
                name=name,
                defaults={
                    'location': location,
                    'content': content,
                    'rating': rating,
                    'is_featured': is_featured
                }
            )
            if created:
                self.stdout.write(f'Created testimonial from: {name}')
