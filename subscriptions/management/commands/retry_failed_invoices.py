"""
Management command to retry failed Smart Bill invoice generation

Usage: python manage.py retry_failed_invoices [--max-retries=10]

This command is designed to run every 15 minutes via cron/scheduler.
It retries pending invoices up to a maximum number of attempts (default: 10).
After 10 failed attempts (2.5 hours), an admin alert is sent.
"""

from django.core.management.base import BaseCommand
from django.core.mail import mail_admins
from django.utils import timezone
from subscriptions.models import SubscriptionLog, Invoice
from subscriptions.smartbill_service import InvoiceService, SmartBillAPIError
from decimal import Decimal


class Command(BaseCommand):
    help = 'Retry failed Smart Bill invoice generation for pending invoices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries',
            type=int,
            default=10,
            help='Maximum number of retry attempts before alerting admin (default: 10)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be retried without actually retrying',
        )

    def handle(self, *args, **options):
        max_retries = options['max_retries']
        dry_run = options['dry_run']

        # Find all pending invoices that haven't exceeded max retries
        pending_logs = SubscriptionLog.objects.filter(
            event_type='invoice_pending',
            metadata__retry_count__lt=max_retries
        ).order_by('timestamp')

        total = pending_logs.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('[+] No pending invoices to retry'))
            return

        self.stdout.write(f'[*] Found {total} pending invoice(s) to retry')

        success_count = 0
        failed_count = 0
        max_retry_count = 0

        for log in pending_logs:
            subscription = log.subscription
            metadata = log.metadata
            retry_count = metadata.get('retry_count', 0)
            stripe_invoice_id = metadata.get('stripe_invoice_id')

            # Check if invoice already exists (might have been created manually)
            if Invoice.objects.filter(stripe_invoice_id=stripe_invoice_id).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'[~] Invoice already exists for {stripe_invoice_id}, deleting pending log'
                    )
                )
                if not dry_run:
                    log.delete()
                continue

            self.stdout.write(
                f'[*] Retrying invoice for subscription {subscription.id} '
                f'(attempt {retry_count + 1}/{max_retries})'
            )

            if dry_run:
                self.stdout.write(self.style.NOTICE('    [DRY RUN] Would retry here'))
                continue

            try:
                # Attempt to generate invoice
                invoice_data = InvoiceService.create_invoice(
                    subscription=subscription,
                    stripe_invoice_id=stripe_invoice_id
                )

                # Save invoice record
                total_ron = Decimal(subscription.tier.price) / 100
                base_ron, tva_ron, _ = InvoiceService.calculate_tva(total_ron)

                craftsman = subscription.craftsman
                Invoice.objects.create(
                    subscription=subscription,
                    stripe_invoice_id=stripe_invoice_id,
                    smartbill_series=invoice_data.get('series', ''),
                    smartbill_number=str(invoice_data.get('number', '')),
                    smartbill_url=invoice_data.get('url', ''),
                    total_ron=total_ron,
                    base_ron=base_ron,
                    tva_ron=tva_ron,
                    client_name=craftsman.company_name or craftsman.user.get_full_name(),
                    client_fiscal_code=craftsman.cui or craftsman.cnp,
                    client_address=f"{craftsman.fiscal_address_street}, {craftsman.fiscal_address_city}",
                )

                # Delete pending log (success!)
                log.delete()

                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'    [+] Invoice created: {invoice_data.get("series")}-{invoice_data.get("number")}'
                    )
                )

            except SmartBillAPIError as e:
                # Increment retry count
                metadata['retry_count'] = retry_count + 1
                metadata['last_error'] = str(e)
                metadata['last_retry_at'] = timezone.now().isoformat()
                log.metadata = metadata
                log.save()

                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'    [-] Retry failed: {e}')
                )

                # Check if max retries reached
                if retry_count + 1 >= max_retries:
                    max_retry_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'    [!] Max retries reached, alerting admin'
                        )
                    )

                    # Alert admin for manual intervention
                    mail_admins(
                        subject=f"Invoice Generation Failed After {max_retries} Retries - Subscription {subscription.id}",
                        message=f"Subscription ID: {subscription.id}\n"
                                f"Craftsman: {subscription.craftsman.user.email}\n"
                                f"Tier: {subscription.tier.display_name}\n"
                                f"Stripe Invoice: {stripe_invoice_id}\n\n"
                                f"Error: {e}\n\n"
                                f"First attempt: {log.timestamp}\n"
                                f"Last retry: {metadata.get('last_retry_at')}\n"
                                f"Retry count: {retry_count + 1}\n\n"
                                f"Please generate invoice manually in Smart Bill dashboard.",
                    )

        # Summary
        self.stdout.write(self.style.SUCCESS('\n[+] Retry process complete!'))
        self.stdout.write(f'    Total pending: {total}')
        self.stdout.write(
            self.style.SUCCESS(f'    Successful: {success_count}')
        )
        if failed_count > 0:
            self.stdout.write(
                self.style.WARNING(f'    Failed (will retry): {failed_count}')
            )
        if max_retry_count > 0:
            self.stdout.write(
                self.style.ERROR(f'    Max retries reached (alerted admin): {max_retry_count}')
            )
