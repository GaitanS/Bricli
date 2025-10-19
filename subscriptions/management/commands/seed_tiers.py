"""
Management command to seed subscription tiers (Free, Plus, Pro)

Usage: python manage.py seed_tiers [--force]

Creates the 3 subscription tiers with proper feature configurations.
Use --force to recreate existing tiers (updates features, preserves tier IDs).
"""

from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionTier


class Command(BaseCommand):
    help = 'Seed the 3 subscription tiers (Free, Plus, Pro) with feature configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate existing tiers (updates features)',
        )

    def handle(self, *args, **options):
        force = options['force']

        # Define tier configurations
        tiers_config = [
            {
                'name': 'free',
                'display_name': 'Plan Gratuit',
                'price': 0,  # 0 RON/month
                'monthly_lead_limit': 5,
                'max_portfolio_images': 3,
                'profile_badge': '',
                'priority_in_search': 0,
                'show_in_featured': False,
                'can_attach_pdf': False,
                'analytics_access': False,
                'stripe_price_id': '',  # No Stripe price for free tier
            },
            {
                'name': 'plus',
                'display_name': 'Plan Plus',
                'price': 4900,  # 49 RON/month
                'monthly_lead_limit': None,  # Unlimited leads
                'max_portfolio_images': 10,
                'profile_badge': 'Verificat',
                'priority_in_search': 1,
                'show_in_featured': False,
                'can_attach_pdf': True,
                'analytics_access': False,
                'stripe_price_id': '',  # TODO: Add Stripe Price ID after Stripe setup
            },
            {
                'name': 'pro',
                'display_name': 'Plan Pro',
                'price': 14900,  # 149 RON/month
                'monthly_lead_limit': None,  # Unlimited leads
                'max_portfolio_images': 50,
                'profile_badge': 'Top Pro',
                'priority_in_search': 2,
                'show_in_featured': True,
                'can_attach_pdf': True,
                'analytics_access': True,
                'stripe_price_id': '',  # TODO: Add Stripe Price ID after Stripe setup
            },
        ]

        for tier_data in tiers_config:
            tier_name = tier_data['name']
            tier, created = SubscriptionTier.objects.update_or_create(
                name=tier_name,
                defaults=tier_data
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'[+] Created tier: {tier.display_name} ({tier.get_price_ron()} RON/luna)')
                )
            elif force:
                self.stdout.write(
                    self.style.WARNING(f'[~] Updated tier: {tier.display_name} ({tier.get_price_ron()} RON/luna)')
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(f'[-] Skipped existing tier: {tier.display_name} (use --force to update)')
                )

        # Summary
        self.stdout.write(self.style.SUCCESS('\n[+] Tier seeding complete!'))
        self.stdout.write(f'Total tiers: {SubscriptionTier.objects.count()}')
