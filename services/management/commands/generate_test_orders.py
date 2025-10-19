"""
Management command to generate test orders for "Pavaj alei gradina" service.
Useful for testing the notification system and order browsing functionality.

Usage:
    python manage.py generate_test_orders                    # Create 10 draft orders
    python manage.py generate_test_orders --publish           # Create and publish (sends notifications!)
    python manage.py generate_test_orders --cleanup           # Delete all test orders
    python manage.py generate_test_orders --count 5 --publish # Create 5 published orders
"""

import os
import random
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image

from accounts.models import City, County
from services.models import Order, OrderImage, Service, notify_new_order_to_craftsmen

User = get_user_model()


# 10 realistic order templates
ORDER_TEMPLATES = [
    {
        "title": "Pavaj alei acces garaj și parcare",
        "city_name": "Brașov",
        "county_name": "Brașov",
        "description": """Bună ziua,

Caut meșter specializat pentru pavarea unei alei de acces la garaj și a unei zone de parcare.

**Detalii proiect:**
- Suprafață totală: aproximativ 40 mp
- Aleea de acces: 12m lungime × 2.5m lățime
- Zona parcare: 2 mașini (aproximativ 25 mp)
- Teren: relativ plat, pământ compactat
- Fundație: necesită strat de balast 15cm + nisip compactat

**Materiale preferate:**
- Pavele beton dreptunghiulare gri antracit
- Borduri de delimitare
- Material de calitate, rezistent la trafic auto

**Situația actuală:**
Terenul este liber, fără pavaj existent. Am acces bun pentru utilaje (dacă este necesar compactor).

**Termen:** URGENT - Aș dori finalizarea în maximum 5 zile lucrătoare.

Aștept oferte detaliate cu prețul final (materiale + manoperă) și durata execuției. Mulțumesc!""",
        "budget_min": 6000,
        "budget_max": 8000,
        "urgency": "urgent",
        "days_until_start": 5,
        "address": "Str. Zizinului, nr. 45",
        "image_count": 3,
    },
    {
        "title": "Amenajare cărare grădină cu pavele decorative",
        "city_name": "Brașov",
        "county_name": "Brașov",
        "description": """Salut,

Doresc să amenajez o cărare pietonală în grădină care să lege terasa cu zona de relaxare din spatele casei.

**Specificații:**
- Lungime: aproximativ 18 metri
- Lățime: 1.2 metri (circulație pietonală)
- Suprafață totală: ~25 mp
- Traseu: ușor sinuos, urmărește designul grădinii
- Fundație: strat de balast 10cm + nisip 5cm

**Materiale dorite:**
- Pavele decorative tip mozaic sau cu model
- Culori calde (teracotă, bej, crem)
- Eventual combinație de 2-3 culori pentru contrast
- Borduri discrete din piatră naturală

**Context:**
Grădina este deja amenajată cu gazon și plante. Terenul are o ușoară pantă (circa 5%), deci necesită nivelare. Accesul pentru materiale este prin poartă (lățime 1.5m).

**Termen:** În următoarele 2 săptămâni ar fi ideal.

Aștept oferte cu specificații tehnice și exemple de lucrări anterioare. Mulțumesc!""",
        "budget_min": 3500,
        "budget_max": 5000,
        "urgency": "high",
        "days_until_start": 14,
        "address": "Str. Postavarului, nr. 12",
        "image_count": 2,
    },
    {
        "title": "Pavaj curte interioară cu piatră cubică",
        "city_name": "Brașov",
        "county_name": "Brașov",
        "description": """Bună ziua,

Am o curte interioară (spațiu între casă și gard lateral) pe care vreau să o pavez complet pentru a elimina problema noroi și pentru aspect estetic.

**Dimensiuni:**
- Suprafață: aproximativ 80 mp
- Formă: dreptunghiulară, 16m × 5m
- Teren: pământ natural, nivel relativ ok
- Evacuare ape: există canalizare pluvială la capătul curții

**Materiale preferate:**
- Piatră cubică (tip gresie sau granit)
- Model: pus în evantai sau în arc
- Culoare: gri natural sau multicolor
- Borduri din aceeași piatră

**Lucrări necesare:**
- Săpătură 25-30cm
- Balast compactat 15cm
- Nisip stabilizat 8-10cm
- Pante de scurgere către canalizare

**Observații:**
Aș dori un meșter cu experiență în pavaje cu piatră naturală. Am văzut multe lucrări prost executate unde pietruțele s-au ridicat în timp.

**Termen:** Fără grabă urgentă, pot aștepta până în luna următoare (aproximativ 4-5 săptămâni).

Aștept oferte detaliate. Prefer calitate la preț corect față de soluții ieftine. Mulțumesc!""",
        "budget_min": 12000,
        "budget_max": 15000,
        "urgency": "medium",
        "days_until_start": 30,
        "address": "Str. Lungă, nr. 78A",
        "image_count": 4,
    },
    {
        "title": "Refacere alee principală cu dale granit",
        "city_name": "Brașov",
        "county_name": "Brașov",
        "description": """Bună,

Aleea principală de la poartă la intrarea în casă este deteriorată (pavele vechi de beton, crăpate și denivelate). Vreau să o refac complet cu materiale premium.

**Detalii curente:**
- Dimensiuni: 15m lungime × 2.3m lățime (aproximativ 35 mp)
- Situație: pavele vechi de 20 ani, unele sparte
- Se va demola pavajul existent
- Fundația actuală pare stabilă

**Materiale noi dorite:**
- Dale mari de granit (60×40cm sau similar)
- Culoare: gri deschis sau bej
- Finisaj: anti-alunecare (sablat sau flameizat)
- Borduri masive din granit

**Cerințe tehnice:**
- Fundație nouă sau consolidare existentă (la decizia meșterului)
- Pante de scurgere bine gândite (am avut probleme cu bălți)
- Îmbinări perfecte între dale
- Finisaj profesional

**Termen:** Vreau să termin înainte de sărbători - maxim 10 zile lucrătoare.

Caut meșter cu experiență în lucrări cu granit. Aștept portofoliu și referințe. Mulțumesc!""",
        "budget_min": 8000,
        "budget_max": 10000,
        "urgency": "high",
        "days_until_start": 10,
        "address": "Str. Mihai Viteazu, nr. 34",
        "image_count": 3,
    },
    {
        "title": "Pavaj trotuare laterale casă",
        "city_name": "Brașov",
        "county_name": "Brașov",
        "description": """Salutare,

Vreau să pavez trotuarele din ambele laturi ale casei (banda îngustă între casă și gard). Sunt aproximativ 50 mp în total.

**Specificații:**
- Latura stângă: 20m × 1m = 20 mp
- Latura dreaptă: 25m × 1.2m = 30 mp
- Teren: pământ, usor în pantă
- Scurgere: trebuie asigurată pantă către stradă

**Materiale:**
- Pavele clasice de beton, gri
- Dimensiune standard (20×10cm)
- Borduri din beton la limita cu gazonul
- Calitate medie, rezistent la circulație pietonală

**Lucrări necesare:**
- Săpătură 20cm
- Balast 10cm
- Nisip 5cm compactat
- Pavare + bordurare

**Context:**
Spațiu îngust, deci utilajele mari nu au acces. Materialele trebuie aduse manual sau cu roabă. Am acces prin poarta din față.

**Termen:** Fără urgență, pot aștepta 6 săptămâni.

Aștept oferte realiste care să țină cont de dificultatea lucrului în spațiu îngust. Mulțumesc!""",
        "budget_min": 7000,
        "budget_max": 9000,
        "urgency": "low",
        "days_until_start": 42,
        "address": "Str. Republican, nr. 89",
        "image_count": 2,
    },
    {
        "title": "Pavaj intrare principală vilă",
        "city_name": "București",
        "county_name": "București",
        "description": """Bună ziua,

Dețin o vilă în nordul Bucureștiului și doresc să pavez intrarea principală de la poartă până la casa (zona reprezentativă).

**Dimensiuni proiect:**
- Suprafață totală: aproximativ 60 mp
- Alee principală: 20m × 2.5m = 50 mp
- Platformă intrare casă: 3m × 3.5m = 10 mp
- Teren: pământ natural, aproape plat

**Materiale PREMIUM:**
- Granit sau travertin de înaltă calitate
- Dale mari (80×40cm sau 60×60cm)
- Culori: bej crem sau gri perlat
- Finisaj: lustruit și anti-alunecare
- Borduri discrete, îngropate

**Cerințe foarte importante:**
- Execuție impecabilă - este zona cea mai vizibilă
- Fundație solidă (balast + beton armat dacă e cazul)
- Sistem de scurgere profesionist integrat
- Îmbinări milimetrice între dale
- Curățenie totală după finalizare

**Termen: URGENT** - Am vizită importantă peste 3 zile, trebuie terminat obligatoriu!

Caut doar meșteri cu experiență dovedită în lucrări premium. Trimiteți CV, portofoliu și referințe verificabile. Buget generos pentru calitate excepțională. Mulțumesc!""",
        "budget_min": 10000,
        "budget_max": 13000,
        "urgency": "urgent",
        "days_until_start": 3,
        "address": "Șoseaua Pipera, nr. 156",
        "image_count": 4,
    },
    {
        "title": "Alei pietonale grădină cu mozaic",
        "city_name": "București",
        "county_name": "București",
        "description": """Bună,

Vreau să creez mai multe alei pietonale în grădina mare din spatele casei, cu un aspect artistic folosind pavele mozaic.

**Descriere proiect:**
- 3 alei separate care se intersectează
- Suprafață totală: aproximativ 45 mp
- Lățime alei: 1-1.3m (circulație pietonală)
- Design: curbat, organic, se integrează cu peisajul

**Materiale dorite:**
- Pavele tip mozaic multicolor
- Pattern-uri decorative (flori, geometric)
- Combinație culori vii (roșu, galben, albastru, verde)
- Borduri ascunse în iarbă

**Situație teren:**
- Grădină mare (500mp), cu copaci și arbuști
- Teren ușor denivelat
- Gazon existent (va trebui săpat pentru alei)
- Sol argilos, bun pentru fundație

**Cerințe:**
- Meșter cu experiență în mozaic/pattern-uri
- Lucrare atentă la detalii
- Sfaturi pentru design optimal
- Protecție plantelor existente

**Termen:** Aproximativ 3 săptămâni.

Aștept portofoliu cu lucrări similare. Prețul nu este factorul principal, ci calitatea artistică. Mulțumesc!""",
        "budget_min": 8500,
        "budget_max": 11000,
        "urgency": "medium",
        "days_until_start": 21,
        "address": "Bd. Aviatorilor, nr. 72",
        "image_count": 3,
    },
    {
        "title": "Pavaj terasă exterioară și scări",
        "city_name": "Cluj-Napoca",
        "county_name": "Cluj",
        "description": """Salutare,

Am o casă pe un teren în pantă și trebuie să pavez terasa exterioară plus scările de acces.

**Componente proiect:**
- Terasă: 7m × 5m = 35 mp
- Scări: 3 trepte (lățime 2m) = aproximativ 6 mp
- Platformă intermediară: 2m × 2m = 4 mp
- Total: ~55 mp (terasa + scările + platforma)

**Materiale:**
- Gresie de exterior anti-alunecare (R11 minim)
- Culoare: gri închis sau antracit
- Dimensiuni: 60×60cm sau 80×40cm
- Același material pentru scări și terasă
- Trepte cu profil anti-alunecare

**Cerințe tehnice:**
- Fundație beton armat pentru terasă
- Impermeabilizare sub gresie
- Pante de scurgere 1-2%
- Rigolă de scurgere la marginea terasei
- Scări stabile, cu înălțime uniformă

**Context:**
Teren în pantă aproximativ 15%, deci scările sunt obligatorii. Casa este nouă, dar exterior neamenajat. Accesul pentru materiale este ok.

**Termen:** În următoarele 12 zile.

Caut meșter cu experiență în pavaje pe terase și construcție scări exterioare. Mulțumesc!""",
        "budget_min": 9000,
        "budget_max": 12000,
        "urgency": "high",
        "days_until_start": 12,
        "address": "Str. Observatorului, nr. 23",
        "image_count": 3,
    },
    {
        "title": "Renovare alei existente + extindere",
        "city_name": "Timișoara",
        "county_name": "Timiș",
        "description": """Bună ziua,

Am o alee existentă din pavele (aproximativ 40 mp) care trebuie renovată + doresc să o extind cu încă 30 mp.

**Situația existentă:**
- Alee veche din pavele roșii (20 ani vechime)
- Unele pavele sparte sau lipsă
- Denivelări în unele zone
- Fundația pare ok în majoritatea zonelor
- Dimensiuni: aprox 20m × 2m = 40 mp

**Extensie nouă:**
- Prelungire alee cu 15m
- Lățime: 2m
- Suprafață nouă: 30 mp
- Total proiect: 70 mp

**Materiale:**
- Păstrare pavele vechi recuperabile
- Completare cu pavele noi (același model și culoare sau compatibile)
- Borduri noi pe toată lungimea
- Uniformizare aspect

**Lucrări necesare:**
- Ridicare pavele vechi
- Evaluare și consolidare fundație existentă
- Fundație nouă pentru extensie
- Repavare totală cu combinație vechi + noi
- Nivelări și finisare

**Termen:** Aproximativ 1.5 luni - fără urgență.

Aștept oferte de la meșteri cu experiență în renovări. Este important să se integreze bine partea nouă cu cea veche. Mulțumesc!""",
        "budget_min": 11000,
        "budget_max": 14000,
        "urgency": "medium",
        "days_until_start": 45,
        "address": "Calea Lugojului, nr. 234",
        "image_count": 4,
    },
    {
        "title": "Pavaj zonă BBQ și fântână decorativă",
        "city_name": "Sibiu",
        "county_name": "Sibiu",
        "description": """Salut,

Vreau să amenajez o zonă de relaxare în grădina din spate cu BBQ și o fântână decorativă mică.

**Suprafață de pavat:**
- Zona BBQ: cerc cu diametrul 4m = aproximativ 12 mp
- Alee de acces de la terasă: 10m × 1.2m = 12 mp
- Platformă fântână: 2m × 3m = 6 mp
- Total: aproximativ 30 mp

**Design dorit:**
- Zona BBQ: pavaj circular din piatră naturală
- Alee: pavele decorative tip "pas japonez" (dale separate prin iarbă)
- Platformă fântână: dale mari de piatră naturală

**Materiale:**
- Piatră naturală (andezit sau granit) pentru BBQ
- Dale granit 50×50cm pentru fântână
- Pavele decorative pentru alee
- Aspect rustic, natural

**Context:**
Grădină existentă cu gazon. Zona BBQ va avea grătar fix din cărămidă (se face separat). Fântâna decorativă este mică, doar ornament (fără instalații complexe).

**Termen:** Pot aștepta până la 2 luni, nu este urgent.

Caut meșter creativ care să mă ajute cu sugestii de design. Bugetul este orientativ. Mulțumesc!""",
        "budget_min": 4500,
        "budget_max": 6500,
        "urgency": "low",
        "days_until_start": 60,
        "address": "Str. Aurel Vlaicu, nr. 67",
        "image_count": 2,
    },
]


class Command(BaseCommand):
    help = "Generate test orders for 'Pavaj alei gradina' service to test notification system"

    def add_arguments(self, parser):
        parser.add_argument(
            "--publish",
            action="store_true",
            help="Publish orders immediately after creation (triggers notifications)",
        )
        parser.add_argument(
            "--cleanup",
            action="store_true",
            help="Delete all test orders created by this command",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of orders to create (default: 10, max: 10)",
        )
        parser.add_argument(
            "--client-id",
            type=int,
            help="Specific client user ID to use (default: first available client)",
        )

    def handle(self, *args, **options):
        # Handle cleanup
        if options["cleanup"]:
            self.cleanup_test_orders()
            return

        # Get service
        try:
            service = Service.objects.get(slug="gradinarit-peisagistica-pavaj-alei-gradina")
        except Service.DoesNotExist:
            self.stdout.write(self.style.ERROR('Service "Pavaj alei gradina" not found!'))
            self.stdout.write("Run: python manage.py populate_categories_services")
            return

        # Get client
        client_id = options.get("client_id")
        if client_id:
            try:
                client = User.objects.get(id=client_id, user_type="client")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Client with ID {client_id} not found!"))
                return
        else:
            client = User.objects.filter(user_type="client").first()
            if not client:
                self.stdout.write(self.style.ERROR("No client users found in database!"))
                return

        # Determine count
        count = min(options["count"], len(ORDER_TEMPLATES))

        self.stdout.write(f"\nGenerating {count} test orders for 'Pavaj alei gradina'...")
        self.stdout.write(f"Using client: {client.username} (ID: {client.id})")
        self.stdout.write(f"Using service: Pavaj alei gradina (ID: {service.id})\n")

        created_orders = []
        total_notifications = 0

        for i, template in enumerate(ORDER_TEMPLATES[:count], 1):
            try:
                order = self.create_order(client, service, template, i, count)
                created_orders.append(order)

                # Avoid Romanian characters in console output
                safe_title = order.title.encode('ascii', 'replace').decode('ascii')
                safe_city = template['city_name'].encode('ascii', 'replace').decode('ascii')
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[{i}/{count}] Created: \"{safe_title}\" ({safe_city}) - "
                        f"{order.status.upper()}"
                    )
                )
                self.stdout.write(
                    f"        Budget: {order.budget_min}-{order.budget_max} RON | "
                    f"Urgency: {order.urgency} | "
                    f"Deadline: {order.preferred_date}"
                )
                self.stdout.write(f"        Images: {template['image_count']} added\n")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{i}/{count}] Failed to create order: {str(e)}\n"))
                continue

        # Publish if requested
        if options["publish"] and created_orders:
            self.stdout.write("\nPublishing all orders...")
            for i, order in enumerate(created_orders, 1):
                try:
                    order.status = "published"
                    order.published_at = timezone.now()
                    order.save()

                    # Trigger notifications
                    notifications_sent = notify_new_order_to_craftsmen(order)
                    total_notifications += notifications_sent

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[{i}/{len(created_orders)}] Published order #{order.id} - "
                            f"Sent {notifications_sent} notifications"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"[{i}/{len(created_orders)}] Failed to publish order #{order.id}: {str(e)}")
                    )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"[OK] Successfully created {len(created_orders)} test orders"))
        if options["publish"]:
            self.stdout.write(self.style.SUCCESS(f"[OK] Total notifications sent: {total_notifications}"))
        self.stdout.write(f"[OK] View orders: http://127.0.0.1:8000/servicii/comenzile-mele/")
        self.stdout.write("=" * 60 + "\n")

    def create_order(self, client, service, template, index, total):
        """Create a single order with all details and images"""

        # Get county and city
        county = County.objects.filter(name=template["county_name"]).first()
        if not county:
            raise ValueError(f"County '{template['county_name']}' not found")

        city = City.objects.filter(name=template["city_name"], county=county).first()
        if not city:
            raise ValueError(f"City '{template['city_name']}' not found in {county.name}")

        # Calculate preferred date
        preferred_date = timezone.now().date() + timedelta(days=template["days_until_start"])

        # Create order
        order = Order.objects.create(
            client=client,
            title=template["title"],
            description=template["description"],
            service=service,
            county=county,
            city=city,
            address=template["address"],
            budget_min=template["budget_min"],
            budget_max=template["budget_max"],
            urgency=template["urgency"],
            preferred_date=preferred_date,
            status="draft",
        )

        # Add test images
        self.add_test_images(order, template["image_count"])

        return order

    def add_test_images(self, order, count):
        """Add placeholder images to order"""
        colors = [
            (100, 150, 100),  # Green (garden)
            (120, 120, 120),  # Gray (pavement)
            (160, 140, 120),  # Beige (stone)
            (80, 100, 80),  # Dark green
        ]

        for i in range(count):
            # Create simple colored placeholder image
            img = Image.new("RGB", (800, 600), colors[i % len(colors)])

            # Save to BytesIO
            img_io = BytesIO()
            img.save(img_io, format="JPEG", quality=85)
            img_io.seek(0)

            # Create OrderImage
            order_image = OrderImage(order=order)
            filename = f"test_order_{order.id}_img_{i+1}.jpg"
            order_image.image.save(filename, ContentFile(img_io.read()), save=False)
            order_image.save()

    def cleanup_test_orders(self):
        """Delete all test orders (orders with test descriptions)"""
        test_orders = Order.objects.filter(
            description__icontains="Caut meșter"  # Common phrase in test templates
        ) | Order.objects.filter(title__icontains="Pavaj")

        count = test_orders.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("No test orders found to delete."))
            return

        self.stdout.write(f"\nFound {count} test orders. Deleting...")

        # Delete (images will be deleted via cascade)
        test_orders.delete()

        self.stdout.write(self.style.SUCCESS(f"[OK] Deleted {count} test orders and their images.\n"))
