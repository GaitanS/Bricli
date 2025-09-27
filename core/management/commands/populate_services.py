from django.core.management.base import BaseCommand
from django.db import transaction
from services.models import ServiceCategory, Service


class Command(BaseCommand):
    help = 'Populate database with detailed services for each category'

    def handle(self, *args, **options):
        self.stdout.write('Populating database with detailed services...')
        
        with transaction.atomic():
            self.create_detailed_services()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated services!'))

    def create_detailed_services(self):
        """Create detailed services for each category"""
        
        services_data = {
            'Tâmplărie și Dulgherie': [
                'Mobilier la comandă',
                'Reparații mobilier',
                'Montaj uși interioare',
                'Montaj ferestre',
                'Dulgherie structuri',
                'Lambriuri și parchet',
                'Rafturi și biblioteci',
                'Scări din lemn',
                'Pergole și foisoare',
                'Reparații ferestre'
            ],
            'Instalații Sanitare': [
                'Montaj obiecte sanitare',
                'Reparații țevi',
                'Desfundare canalizare',
                'Instalații apă caldă',
                'Montaj boiler',
                'Reparații robinete',
                'Instalații gaz',
                'Montaj căzi și dușuri',
                'Reparații urgente',
                'Modernizare instalații'
            ],
            'Instalații Electrice': [
                'Instalații electrice noi',
                'Reparații electrice',
                'Montaj prize și întrerupătoare',
                'Tablouri electrice',
                'Iluminat decorativ',
                'Sisteme de siguranță',
                'Instalații industriale',
                'Reparații urgente',
                'Modernizare instalații',
                'Verificări tehnice'
            ],
            'Renovări și Construcții': [
                'Renovări complete',
                'Amenajări interioare',
                'Construcții noi',
                'Extensii case',
                'Reparații structurale',
                'Izolații termice',
                'Finisaje interioare',
                'Modernizări',
                'Consolidări',
                'Expertize tehnice'
            ],
            'Acoperișuri': [
                'Montaj acoperișuri noi',
                'Reparații acoperișuri',
                'Montaj jgheaburi',
                'Izolații acoperișuri',
                'Înlocuire țiglă',
                'Reparații urgente',
                'Curățare acoperișuri',
                'Montaj coșuri',
                'Verificări tehnice',
                'Modernizări'
            ],
            'Pictură și Vopsitorie': [
                'Vopsit interior',
                'Vopsit exterior',
                'Zugrăveli decorative',
                'Reparații pereți',
                'Tencuieli decorative',
                'Vopsit mobilier',
                'Finisaje speciale',
                'Restaurări',
                'Protecții anticorrozive',
                'Consultanță culori'
            ],
            'Instalații de Încălzire': [
                'Montaj centrale termice',
                'Instalații radiatori',
                'Reparații încălzire',
                'Modernizări sisteme',
                'Întreținere centrale',
                'Instalații pardoseală',
                'Sisteme solare',
                'Reparații urgente',
                'Optimizări consum',
                'Verificări tehnice'
            ],
            'Parchet și Gresie': [
                'Montaj parchet',
                'Montaj gresie',
                'Montaj faianță',
                'Reparații pardoseli',
                'Șlefuire parchet',
                'Vitrificare parchet',
                'Montaj mocheta',
                'Finisaje decorative',
                'Reparații urgente',
                'Consultanță materiale'
            ],
            'Grădinărit și Peisagistică': [
                'Amenajări grădini',
                'Întreținere spații verzi',
                'Plantări arbori',
                'Sisteme irigații',
                'Tuns gazon',
                'Curățenie grădini',
                'Design peisagistic',
                'Montaj mobilier grădină',
                'Alei și pavaje',
                'Consultanță horticultură'
            ],
            'Curățenie și Menaj': [
                'Curățenie generală',
                'Curățenie după renovări',
                'Curățenie birouri',
                'Spălare geamuri',
                'Curățenie covoare',
                'Dezinfecție spații',
                'Întreținere regulată',
                'Curățenie industrială',
                'Servicii specializate',
                'Consultanță igienă'
            ],
            'Design Interior': [
                'Proiecte design interior',
                'Consultanță amenajări',
                'Planuri 3D',
                'Selecție mobilier',
                'Coordonare lucrări',
                'Design comercial',
                'Renovări stilistice',
                'Optimizare spații',
                'Consultanță culori',
                'Supervizare execuție'
            ],
            'Asamblare și Montaj': [
                'Asamblare mobilier',
                'Montaj echipamente',
                'Instalare aparate',
                'Montaj decorațiuni',
                'Asamblare structuri',
                'Montaj sisteme',
                'Instalări specializate',
                'Reparații montaj',
                'Consultanță tehnică',
                'Servicii urgente'
            ],
            'Demolări și Debarasări': [
                'Demolări controlate',
                'Debarasări locuințe',
                'Demolări interioare',
                'Transport moloz',
                'Curățenie după demolări',
                'Debarasări birouri',
                'Servicii urgente',
                'Demolări specializate',
                'Consultanță tehnică',
                'Evacuare deșeuri'
            ],
            'Zidărie și Beton': [
                'Zidării noi',
                'Reparații ziduri',
                'Turnări beton',
                'Fundații',
                'Șape beton',
                'Reparații structurale',
                'Consolidări',
                'Ziduri decorative',
                'Expertize tehnice',
                'Consultanță structurală'
            ],
            'IT și Tehnologie': [
                'Instalare rețele',
                'Configurare sisteme',
                'Reparații calculatoare',
                'Instalare software',
                'Sisteme securitate',
                'Consultanță IT',
                'Mentenanță sisteme',
                'Recuperare date',
                'Optimizare performanță',
                'Suport tehnic'
            ]
        }

        for category_name, service_names in services_data.items():
            try:
                category = ServiceCategory.objects.get(name=category_name)
                
                # Șterge serviciile existente generice
                Service.objects.filter(category=category).delete()
                
                # Creează serviciile detaliate
                for service_name in service_names:
                    service_slug = service_name.lower().replace(' ', '-').replace('ă', 'a').replace('â', 'a').replace('î', 'i').replace('ș', 's').replace('ț', 't')
                    
                    Service.objects.create(
                        category=category,
                        name=service_name,
                        slug=service_slug,
                        description=f"Servicii profesionale de {service_name.lower()}",
                        is_active=True
                    )
                
                self.stdout.write(f'Created {len(service_names)} services for {category_name}')
                
            except ServiceCategory.DoesNotExist:
                self.stdout.write(f'Category {category_name} not found, skipping...')
                continue
