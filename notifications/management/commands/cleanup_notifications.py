from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.models import Notification, PushSubscription


class Command(BaseCommand):
    help = "Clean up expired notifications and inactive push subscriptions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=30, help="Delete notifications older than this many days (default: 30)"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be deleted without actually deleting"
        )
        parser.add_argument(
            "--expired-only", action="store_true", help="Only delete notifications that have an explicit expiry date"
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        expired_only = options["expired_only"]

        self.stdout.write(self.style.SUCCESS(f"Starting notification cleanup (dry_run={dry_run})"))

        # Clean up expired notifications
        if expired_only:
            expired_notifications = Notification.objects.filter(expires_at__lt=timezone.now())
            count_message = "expired notifications"
        else:
            cutoff_date = timezone.now() - timedelta(days=days)
            expired_notifications = Notification.objects.filter(created_at__lt=cutoff_date)
            count_message = f"notifications older than {days} days"

        expired_count = expired_notifications.count()

        if expired_count > 0:
            self.stdout.write(f"Found {expired_count} {count_message}")

            if not dry_run:
                deleted_count = expired_notifications.delete()[0]
                self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} notifications"))
            else:
                self.stdout.write(self.style.WARNING(f"Would delete {expired_count} notifications"))
        else:
            self.stdout.write(f"No {count_message} found")

        # Clean up inactive push subscriptions
        inactive_cutoff = timezone.now() - timedelta(days=30)
        inactive_subscriptions = PushSubscription.objects.filter(
            models.Q(is_active=False) | models.Q(last_used__lt=inactive_cutoff)
        )

        inactive_count = inactive_subscriptions.count()

        if inactive_count > 0:
            self.stdout.write(f"Found {inactive_count} inactive push subscriptions")

            if not dry_run:
                deleted_subs = inactive_subscriptions.delete()[0]
                self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_subs} push subscriptions"))
            else:
                self.stdout.write(self.style.WARNING(f"Would delete {inactive_count} push subscriptions"))
        else:
            self.stdout.write("No inactive push subscriptions found")

        # Show statistics
        total_notifications = Notification.objects.count()
        total_subscriptions = PushSubscription.objects.count()
        active_subscriptions = PushSubscription.objects.filter(is_active=True).count()

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("STATISTICS:")
        self.stdout.write(f"Total notifications: {total_notifications}")
        self.stdout.write(f"Total push subscriptions: {total_subscriptions}")
        self.stdout.write(f"Active push subscriptions: {active_subscriptions}")
        self.stdout.write("=" * 50)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS("Cleanup completed successfully!"))
        else:
            self.stdout.write(self.style.WARNING("Dry run completed. Use --no-dry-run to actually delete."))
