"""
Management command to populate ServiceCategory and Service with comprehensive data
Usage: python manage.py populate_categories_services
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from services.models import Service, ServiceCategory


def make_slug(text: str) -> str:
    """Create ASCII-only slug (remove diacritics for SEO)"""
    return (
        slugify(text, allow_unicode=True)
        .replace("ț", "t")
        .replace("Ț", "T")
        .replace("ș", "s")
        .replace("Ș", "S")
        .replace("ă", "a")
        .replace("â", "a")
        .replace("î", "i")
    )


# Categories with emoji icons
CATEGORIES = [
    ("renovari-constructii", "Renovări și Construcții", "🏗️", "Lucrări de construcții, renovări complete, extinderi"),
    ("instalatii-sanitare", "Instalații Sanitare", "🚿", "Instalații sanitare, țevi, obiecte sanitare"),
    ("instalatii-electrice", "Instalații Electrice", "⚡", "Instalații electrice, tablouri, prize, iluminat"),
    ("curatenie-menaj", "Curățenie și Menaj", "🧹", "Curățenie profesională, menaj, igienizare"),
    ("gradinarit-peisagistica", "Grădinărit și Peisagistică", "🌿", "Grădinărit, peisagistică, întreținere spații verzi"),
    ("asamblare-montaj", "Asamblare și Montaj", "🧰", "Asamblare mobilier, montaj corpuri, instalare echipamente"),
    ("acoperisuri", "Acoperișuri", "🏠", "Reparații acoperișuri, înlocuire țigle, hidroizolație"),
    ("geamuri-ferestre", "Geamuri și Ferestre", "🪟", "Montaj ferestre, termopan, jaluzele, reparații"),
    ("design-interior", "Design Interior", "🛋️", "Proiectare 3D, consultanță design, amenajări interioare"),
    ("it-tehnologie", "IT și Tehnologie", "💻", "Instalare software, configurare rețele, asistență IT"),
]

# Services per category (≥15 each)
SERVICES = {
    "renovari-constructii": [
        "Renovare baie",
        "Renovare bucătărie",
        "Zugrăvit / vopsit",
        "Gletuit și finisaje",
        "Montaj parchet laminat",
        "Montaj gresie și faianță",
        "Compartimentări din rigips",
        "Tencuieli mecanizate",
        "Șapă și nivelare",
        "Izolație termică / fonică",
        "Montaj uși interioare",
        "Montaj ferestre termopan",
        "Reparații acoperiș",
        "Extinderi și anexe",
        "Consolidări structurale",
        "Placări decorative",
        "Montaj plintă",
    ],
    "instalatii-sanitare": [
        "Montaj chiuvetă",
        "Montaj vas WC",
        "Montaj cabină duș",
        "Montaj cadă",
        "Înlocuire țevi (PPR/PEX)",
        "Reparație scurgeri",
        "Montaj baterie",
        "Desfundare canalizare",
        "Montaj boiler",
        "Instalare pompă submersibilă",
        "Montaj apometru",
        "Întreținere țevi",
        "Înlocuire sifon",
        "Verificare etanșeitate",
        "Mutare puncte apă",
        "Montaj mașină de spălat",
    ],
    "instalatii-electrice": [
        "Tragere circuite noi",
        "Înlocuire tablou electric",
        "Montaj prize și întrerupătoare",
        "Montaj corpuri de iluminat",
        "Montaj siguranțe automate",
        "Priză pentru cuptor / plită",
        "Priză exterior IP65",
        "Împământare / paratrăsnet",
        "Diode / redresor pentru LED",
        "Detectare și remediere scurtcircuit",
        "Rețea cat6 în apartament",
        "TV / coaxial cablare",
        "Smart home (relee / becuri)",
        "Certificat PRAM",
        "Audit energetic locuință",
    ],
    "curatenie-menaj": [
        "Curățenie generală",
        "Curățenie după constructor",
        "Curățenie apartament",
        "Curățenie casă",
        "Spălat geamuri",
        "Curățenie canapele / tapițerie",
        "Curățenie birouri",
        "Igienizare băi",
        "Curățare gresie/faianță",
        "Curățenie frigidere / cuptoare",
        "Aspirat covoare",
        "Curățenie scară bloc",
        "Dezinfectare",
        "Curățenie periodică",
        "Colectare și evacuare moloz",
    ],
    "gradinarit-peisagistica": [
        "Tuns gazon",
        "Montaj rulouri gazon",
        "Sisteme irigații",
        "Toaletare arbori",
        "Plantare arbori / arbuști",
        "Însămânțare gazon",
        "Modelare teren",
        "Pavaj alei grădină",
        "Gard viu - plantare și tăiere",
        "Întreținere grădină",
        "Fertilizare",
        "Stropiri fitosanitare",
        "Îndepărtare resturi vegetale",
        "Fântână arteziană mică",
        "Iluminat grădină",
    ],
    "asamblare-montaj": [
        "Asamblare mobilier IKEA",
        "Montaj dulap",
        "Montaj pat",
        "Montaj masă / scaune",
        "Montaj bibliotecă",
        "Montaj dressing",
        "Montaj corpuri suspendate",
        "Fixare TV pe perete",
        "Montaj perdele / galerii",
        "Montaj jaluzele",
        "Montaj ușă interior",
        "Montaj ușă metalică",
        "Montaj glafuri",
        "Montaj polițe",
        "Montaj parchet / plintă",
    ],
    "acoperisuri": [
        "Reparații acoperiș țiglă",
        "Reparații acoperiș tablă",
        "Înlocuire țiglă spartă",
        "Montaj jgheaburi / burlane",
        "Hidroizolație terasă",
        "Mansardare",
        "Montaj luminator",
        "Stopare infiltrații",
        "Curățare acoperiș",
        "Montaj parazăpezi",
        "Vopsire tablă",
        "Izolație pod",
        "Ferestre de mansardă",
        "Revizie acoperiș",
        "Streasină și pazie",
    ],
    "geamuri-ferestre": [
        "Montaj termopan",
        "Reglaj ferestre",
        "Schimbare balamale",
        "Schimbare garnituri",
        "Înlocuire sticlă",
        "Plase insecte",
        "Glafuri interior/exterior",
        "Geamuri culisante",
        "Uși PVC",
        "Uși glisante",
        "Reparații rulouri",
        "Etanșare ferestre",
        "Jaluzele verticale",
        "Jaluzele orizontale",
        "Măsurători & consultanță",
    ],
    "design-interior": [
        "Proiectare 3D",
        "Consultanță design",
        "Alegere paletă culori",
        "Amenajare living",
        "Amenajare dormitor",
        "Amenajare bucătărie",
        "Amenajare baie",
        "Iluminat ambiental",
        "Selectare materiale",
        "Stilizare mobilier",
        "Decor ferestre",
        "Tablouri & accente",
        "Plan mobilier la comandă",
        "Planificare spațiu",
        "Studiu de concept",
    ],
    "it-tehnologie": [
        "Instalare Windows",
        "Instalare și configurare software",
        "Curățare virus/malware",
        "Recuperare date (basic)",
        "Upgrade SSD/RAM",
        "Rețea Wi-Fi optimizare",
        "Partajare imprimantă",
        "Back-up automat",
        "Monitorizare PC familie",
        "Configurare NAS",
        "Server media (Plex)",
        "Montaj router mesh",
        "Instalare cameră IP",
        "Configurare smart home",
        "Depanare la distanță",
    ],
}


class Command(BaseCommand):
    help = "Populate categories and popular services (idempotent)"

    def handle(self, *args, **opts):
        created_cats = 0
        updated_cats = 0
        created_svcs = 0

        self.stdout.write("Seeding categories and services...")

        for slug, name, emoji, description in CATEGORIES:
            # Create or update category
            cat, created = ServiceCategory.objects.get_or_create(slug=slug, defaults={"name": name})

            if created:
                created_cats += 1
                self.stdout.write(self.style.SUCCESS(f"[+] Created category: {slug}"))
            else:
                self.stdout.write(f"[-] Category exists: {slug}")

            # Update fields
            changed = False
            if cat.icon_emoji != emoji:
                cat.icon_emoji = emoji
                changed = True
            if cat.name != name:
                cat.name = name
                changed = True
            if cat.description != description:
                cat.description = description
                changed = True

            if changed:
                cat.save()
                updated_cats += 1
                self.stdout.write(self.style.WARNING(f"[~] Updated: {slug}"))

            # Create services for this category
            items = SERVICES.get(slug, [])
            for service_name in items:
                s_slug = f"{slug}-{make_slug(service_name)}"
                svc, svc_created = Service.objects.get_or_create(
                    slug=s_slug,
                    defaults={"category": cat, "name": service_name, "is_popular": True, "is_active": True},
                )
                if svc_created:
                    created_svcs += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Categories: {created_cats} created, {updated_cats} updated. Services: {created_svcs} created."
            )
        )
        self.stdout.write(
            f"Total in DB: {ServiceCategory.objects.count()} categories, {Service.objects.count()} services"
        )
