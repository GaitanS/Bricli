"""
Management command pentru actualizarea profilurilor și badge-urilor
"""

from django.core.management.base import BaseCommand

from accounts.services import BadgeService, ProfileCompletionService


class Command(BaseCommand):
    help = "Actualizează procentajele de completare și badge-urile pentru toate profilurile"

    def add_arguments(self, parser):
        parser.add_argument(
            "--completion-only",
            action="store_true",
            help="Actualizează doar procentajele de completare",
        )
        parser.add_argument(
            "--badges-only",
            action="store_true",
            help="Actualizează doar badge-urile",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="Afișează doar statisticile",
        )

    def handle(self, *args, **options):
        if options["stats"]:
            self.show_statistics()
            return

        if not options["badges_only"]:
            self.stdout.write("Actualizează procentajele de completare...")
            updated_profiles = ProfileCompletionService.update_all_profiles()
            self.stdout.write(self.style.SUCCESS(f"Actualizate {updated_profiles} profiluri"))

        if not options["completion_only"]:
            self.stdout.write("Actualizează badge-urile...")
            updated_badges = BadgeService.update_all_badges()
            self.stdout.write(self.style.SUCCESS(f"Actualizate badge-uri pentru {updated_badges} profiluri"))

        # Afișează statistici finale
        self.show_statistics()
        self.stdout.write("\nActualizarea s-a încheiat!")

    def show_statistics(self):
        """Afișează statisticile badge-urilor"""
        stats = BadgeService.get_badge_statistics()
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("STATISTICI BADGE-URI")
        self.stdout.write("=" * 40)
        self.stdout.write(f'Total profiluri: {stats["total_profiles"]}')
        self.stdout.write(f'Profil complet: {stats["profile_complete"]}')
        self.stdout.write(f'Firmă verificată: {stats["company_verified"]}')
        self.stdout.write(f'Top Rated: {stats["top_rated"]}')
        self.stdout.write(f'Activ: {stats["active"]}')
        self.stdout.write(f'De încredere: {stats["trusted"]}')

        # Calculează procentaje
        total = stats["total_profiles"]
        if total > 0:
            self.stdout.write("\nPROCENTAJE:")
            self.stdout.write(f'Profil complet: {stats["profile_complete"]/total*100:.1f}%')
            self.stdout.write(f'Firmă verificată: {stats["company_verified"]/total*100:.1f}%')
            self.stdout.write(f'Top Rated: {stats["top_rated"]/total*100:.1f}%')
            self.stdout.write(f'Activ: {stats["active"]/total*100:.1f}%')
            self.stdout.write(f'De încredere: {stats["trusted"]/total*100:.1f}%')
