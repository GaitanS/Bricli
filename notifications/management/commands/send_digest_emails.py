from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.services import EmailNotificationService

User = get_user_model()


class Command(BaseCommand):
    help = "Send notification digest emails to users based on their preferences"

    def add_arguments(self, parser):
        parser.add_argument(
            "--period", choices=["daily", "weekly", "monthly"], default="daily", help="Digest period (default: daily)"
        )
        parser.add_argument("--user-id", type=int, help="Send digest to specific user ID only")
        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be sent without actually sending emails"
        )
        parser.add_argument("--force", action="store_true", help="Force send digest even if not the right time")

    def handle(self, *args, **options):
        period = options["period"]
        user_id = options.get("user_id")
        dry_run = options["dry_run"]
        force = options["force"]

        self.stdout.write(self.style.SUCCESS(f"Starting {period} digest email sending (dry_run={dry_run})"))

        # Determine if it's the right time to send digests
        now = timezone.now()

        if not force:
            if period == "daily" and now.hour != 8:  # Send daily digests at 8 AM
                self.stdout.write(self.style.WARNING("Not the right time for daily digests (should be 8 AM)"))
                return

            elif period == "weekly" and (now.weekday() != 0 or now.hour != 8):  # Monday 8 AM
                self.stdout.write(self.style.WARNING("Not the right time for weekly digests (should be Monday 8 AM)"))
                return

            elif period == "monthly" and (now.day != 1 or now.hour != 8):  # 1st of month 8 AM
                self.stdout.write(
                    self.style.WARNING("Not the right time for monthly digests (should be 1st of month 8 AM)")
                )
                return

        # Get users who should receive digests
        if user_id:
            users = User.objects.filter(id=user_id, is_active=True)
        else:
            users = User.objects.filter(is_active=True, notificationpreference__digest_frequency=period).select_related(
                "notificationpreference"
            )

        if not users.exists():
            self.stdout.write("No users found for digest sending")
            return

        self.stdout.write(f"Found {users.count()} users for {period} digest")

        sent_count = 0
        error_count = 0

        for user in users:
            try:
                self.stdout.write(f"Processing user: {user.username} ({user.email})")

                if dry_run:
                    self.stdout.write(self.style.WARNING(f"Would send {period} digest to {user.email}"))
                    sent_count += 1
                else:
                    success = EmailNotificationService.send_digest_email(user, period)

                    if success:
                        self.stdout.write(self.style.SUCCESS(f"Sent {period} digest to {user.email}"))
                        sent_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f"Failed to send digest to {user.email}"))
                        error_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing user {user.username}: {str(e)}"))
                error_count += 1

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("DIGEST SENDING SUMMARY:")
        self.stdout.write(f"Period: {period}")
        self.stdout.write(f"Total users processed: {users.count()}")
        self.stdout.write(f"Successfully sent: {sent_count}")
        self.stdout.write(f"Errors: {error_count}")
        self.stdout.write("=" * 50)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS("Digest sending completed!"))
        else:
            self.stdout.write(self.style.WARNING("Dry run completed. Use --no-dry-run to actually send emails."))
