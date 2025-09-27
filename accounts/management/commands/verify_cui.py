"""
Management command pentru verificarea automată a CUI-urilor
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CraftsmanProfile
from accounts.services import CUIVerificationService


class Command(BaseCommand):
    help = 'Verifică automat CUI-urile meșterilor și actualizează badge-urile'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cui',
            type=str,
            help='Verifică un CUI specific',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Verifică toate CUI-urile din baza de date',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forțează reverificarea CUI-urilor deja verificate',
        )

    def handle(self, *args, **options):
        if options['cui']:
            self.verify_single_cui(options['cui'])
        elif options['all']:
            self.verify_all_cuis(options['force'])
        else:
            self.stdout.write(
                self.style.ERROR('Specifică --cui <CUI> sau --all')
            )

    def verify_single_cui(self, cui):
        """Verifică un singur CUI"""
        self.stdout.write(f'Verifică CUI: {cui}')
        
        result = CUIVerificationService.verify_cui(cui)
        
        if result['is_valid']:
            self.stdout.write(
                self.style.SUCCESS(f'✓ CUI valid: {cui}')
            )
            if result['company_name']:
                self.stdout.write(f'  Companie: {result["company_name"]}')
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ CUI invalid: {cui}')
            )
            if result['error']:
                self.stdout.write(f'  Eroare: {result["error"]}')

    def verify_all_cuis(self, force=False):
        """Verifică toate CUI-urile din baza de date"""
        self.stdout.write('Începe verificarea CUI-urilor...')
        
        # Găsește profilurile cu CUI
        query = CraftsmanProfile.objects.filter(company_cui__isnull=False)
        query = query.exclude(company_cui='')
        
        if not force:
            # Doar CUI-urile neverificate
            query = query.filter(company_verified_at__isnull=True)
        
        profiles = query.all()
        
        if not profiles:
            self.stdout.write(
                self.style.WARNING('Nu există CUI-uri de verificat')
            )
            return
        
        self.stdout.write(f'Găsite {len(profiles)} profiluri cu CUI de verificat')
        
        verified_count = 0
        invalid_count = 0
        error_count = 0
        
        for profile in profiles:
            try:
                self.stdout.write(f'Verifică {profile.user.username}: {profile.company_cui}')
                
                result = CUIVerificationService.update_craftsman_cui_status(
                    profile, profile.company_cui
                )
                
                if result['is_valid']:
                    verified_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Verificat cu succes')
                    )
                    if result['company_name']:
                        self.stdout.write(f'    Companie: {result["company_name"]}')
                else:
                    invalid_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ CUI invalid: {result["error"]}')
                    )
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Eroare: {str(e)}')
                )
        
        # Rezumat
        self.stdout.write('\n' + '='*50)
        self.stdout.write('REZUMAT VERIFICARE CUI')
        self.stdout.write('='*50)
        self.stdout.write(f'Total procesate: {len(profiles)}')
        self.stdout.write(
            self.style.SUCCESS(f'Verificate cu succes: {verified_count}')
        )
        self.stdout.write(
            self.style.ERROR(f'CUI-uri invalide: {invalid_count}')
        )
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'Erori de procesare: {error_count}')
            )
        
        self.stdout.write('\nVerificarea s-a încheiat!')



