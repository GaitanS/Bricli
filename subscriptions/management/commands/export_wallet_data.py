"""
Management command to export all wallet data before removal

Usage: python manage.py export_wallet_data [--output wallets_export.csv]

Exports all CreditWallet and WalletTransaction records to CSV for audit trail.
This data should be archived before the wallet system is removed.
"""

import csv
from django.core.management.base import BaseCommand
from django.utils import timezone

from services.models import CreditWallet, WalletTransaction


class Command(BaseCommand):
    help = 'Export all wallet data to CSV before wallet system removal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='wallet_export_{date}.csv',
            help='Output CSV file path',
        )

    def handle(self, *args, **options):
        # Generate filename with timestamp
        output_file = options['output']
        if '{date}' in output_file:
            date_str = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_file = output_file.replace('{date}', date_str)

        # Export wallet balances
        wallets = CreditWallet.objects.all().select_related('user')
        wallet_count = wallets.count()

        self.stdout.write(f'Found {wallet_count} wallets to export')

        # Export transactions
        transactions = WalletTransaction.objects.all().select_related('wallet__user')
        transaction_count = transactions.count()

        self.stdout.write(f'Found {transaction_count} transactions to export')

        # Write wallets to CSV
        wallet_file = output_file.replace('.csv', '_wallets.csv')
        with open(wallet_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'User Email',
                'User ID',
                'Balance (RON)',
                'Balance (cents)',
                'Created At',
                'Updated At',
            ])

            for wallet in wallets:
                writer.writerow([
                    wallet.user.email,
                    wallet.user.id,
                    wallet.balance_lei,
                    wallet.balance_cents,
                    wallet.created_at,
                    wallet.updated_at,
                ])

        self.stdout.write(self.style.SUCCESS(f'[+] Exported {wallet_count} wallets to {wallet_file}'))

        # Write transactions to CSV
        transaction_file = output_file.replace('.csv', '_transactions.csv')
        with open(transaction_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'User Email',
                'User ID',
                'Transaction Type',
                'Amount (RON)',
                'Amount (cents)',
                'Balance After (RON)',
                'Reason',
                'Metadata',
                'Created At',
            ])

            for tx in transactions:
                writer.writerow([
                    tx.wallet.user.email,
                    tx.wallet.user.id,
                    tx.transaction_type,
                    tx.amount_lei,
                    tx.amount_cents,
                    tx.balance_after_lei,
                    tx.reason,
                    str(tx.meta),
                    tx.created_at,
                ])

        self.stdout.write(self.style.SUCCESS(f'[+] Exported {transaction_count} transactions to {transaction_file}'))

        # Summary
        wallets_with_balance = wallets.filter(balance_cents__gt=0).count()
        total_balance_cents = sum(w.balance_cents for w in wallets)
        total_balance_ron = total_balance_cents / 100

        self.stdout.write(self.style.SUCCESS(f'\n[+] Export complete!'))
        self.stdout.write(f'Total wallets: {wallet_count}')
        self.stdout.write(f'Wallets with balance > 0: {wallets_with_balance}')
        self.stdout.write(f'Total balance to refund: {total_balance_ron:.2f} RON ({total_balance_cents} cents)')

        if wallets_with_balance > 0:
            self.stdout.write(self.style.WARNING(f'\n[!] WARNING: {wallets_with_balance} wallets have non-zero balances!'))
            self.stdout.write(self.style.WARNING('[!] Process refunds before removing wallet system.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n[+] All wallets have zero balance. Safe to proceed with removal.'))
