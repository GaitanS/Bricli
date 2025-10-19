"""
Management command to migrate existing craftsmen to Free tier

Usage: python manage.py migrate_existing_craftsmen [--dry-run]

Assigns all existing CraftsmanProfile records to the Free tier.
Creates CraftsmanSubscription records with active status.

IMPORTANT: Run this AFTER seed_tiers command.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from accounts.models import CraftsmanProfile
from subscriptions.models import SubscriptionTier, CraftsmanSubscription, SubscriptionLog


class Command(BaseCommand):
    help = 'Migrate all existing craftsmen to Free tier subscriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Verify Free tier exists
        try:
            free_tier = SubscriptionTier.objects.get(name='free')
        except SubscriptionTier.DoesNotExist:
            raise CommandError(
                '[!] Free tier not found! Run "python manage.py seed_tiers" first.'
            )

        # Get all craftsmen without subscriptions
        craftsmen_without_subs = CraftsmanProfile.objects.filter(
            subscription__isnull=True
        )
        total_craftsmen = craftsmen_without_subs.count()

        if total_craftsmen == 0:
            self.stdout.write(self.style.SUCCESS('[+] All craftsmen already have subscriptions!'))
            return

        self.stdout.write(f'Found {total_craftsmen} craftsmen without subscriptions')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[i] DRY RUN MODE - No changes will be applied\n'))
            for craftsman in craftsmen_without_subs[:10]:  # Show first 10
                self.stdout.write(f'  - {craftsman.user.get_full_name()} ({craftsman.user.email})')
            if total_craftsmen > 10:
                self.stdout.write(f'  ... and {total_craftsmen - 10} more')
            return

        # Migrate craftsmen to Free tier
        migrated_count = 0
        now = timezone.now()

        with transaction.atomic():
            for craftsman in craftsmen_without_subs:
                # Create subscription record
                subscription = CraftsmanSubscription.objects.create(
                    craftsman=craftsman,
                    tier=free_tier,
                    status='active',
                    current_period_start=now,
                    current_period_end=now + timedelta(days=30),  # 30-day billing cycle
                    leads_used_this_month=0,
                    grace_period_end=None,
                    withdrawal_right_waived=True,  # Existing users don't get withdrawal rights
                    withdrawal_deadline=None,
                    stripe_subscription_id='',
                    stripe_customer_id='',
                )

                # Create audit log entry
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    event_type='migration_to_free',
                    old_tier=None,
                    new_tier=free_tier,
                    metadata={
                        'migration_date': now.isoformat(),
                        'migration_type': 'legacy_craftsman',
                        'reason': 'Platform migration from pay-per-lead to subscriptions',
                    }
                )

                migrated_count += 1

                if migrated_count % 10 == 0:
                    self.stdout.write(f'Migrated {migrated_count}/{total_craftsmen} craftsmen...')

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n[+] Successfully migrated {migrated_count} craftsmen to Free tier!'))
        self.stdout.write(f'Total active subscriptions: {CraftsmanSubscription.objects.filter(status="active").count()}')
