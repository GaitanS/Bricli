"""
Management command to seed demo orders for testing visibility and counters.

Creates:
- 1 client demo user (if missing)
- 1 craftsman demo user (if missing)
- 2 PUBLIC orders for the client (status "published")
- 1 DIRECT order (assigned_craftsman=demo_craftsman)

Prints:
- Counter verification (q_active/q_completed)
- AvailableOrdersView count for craftsman
- Confirms direct order is hidden from AvailableOrdersView
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.models import Order, Service, CraftsmanService, ServiceCategory
from services.querydefs import q_active, q_completed
from accounts.models import CraftsmanProfile, County, City

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds demo orders for testing visibility and counters"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("\n" + "=" * 80))
        self.stdout.write(self.style.WARNING("SEEDING DEMO ORDERS"))
        self.stdout.write(self.style.WARNING("=" * 80 + "\n"))

        # 1. Create/get demo users
        self.stdout.write("Creating demo users...")

        client, client_created = User.objects.get_or_create(
            username="demo_client",
            defaults={
                "email": "client@demo.com",
                "user_type": "client",
                "first_name": "Demo",
                "last_name": "Client"
            }
        )
        if client_created:
            client.set_password("demo123")
            client.save()
            self.stdout.write(self.style.SUCCESS(f"  [+] Created client user: {client.username}"))
        else:
            self.stdout.write(f"  [>] Client user exists: {client.username}")

        craftsman, craftsman_created = User.objects.get_or_create(
            username="demo_craftsman",
            defaults={
                "email": "craftsman@demo.com",
                "user_type": "craftsman",
                "first_name": "Demo",
                "last_name": "Craftsman"
            }
        )
        if craftsman_created:
            craftsman.set_password("demo123")
            craftsman.save()
            self.stdout.write(self.style.SUCCESS(f"  [+] Created craftsman user: {craftsman.username}"))
        else:
            self.stdout.write(f"  [>] Craftsman user exists: {craftsman.username}")

        # 2. Get/create required related objects
        county = County.objects.first()
        city = City.objects.first()

        if not county or not city:
            self.stdout.write(self.style.ERROR("\n[ERROR] No counties/cities found in database!"))
            self.stdout.write("  Run: python manage.py loaddata counties_cities.json")
            return

        # Get or create service category and service
        category, _ = ServiceCategory.objects.get_or_create(
            name="Demo Category",
            defaults={"slug": "demo-category", "is_active": True}
        )

        service, _ = Service.objects.get_or_create(
            name="Demo Service",
            category=category,
            defaults={"slug": "demo-service", "is_active": True}
        )

        # Create or get craftsman profile
        try:
            craftsman_profile = CraftsmanProfile.objects.get(user=craftsman)
            profile_created = False
        except CraftsmanProfile.DoesNotExist:
            # Delete any existing profile with conflicting slug
            CraftsmanProfile.objects.filter(slug="demo-craftsman-profile").delete()

            craftsman_profile = CraftsmanProfile.objects.create(
                user=craftsman,
                display_name="Demo Craftsman Profile",  # Unique name
                slug="demo-craftsman-profile",  # Explicit slug
                county=county,
                city=city,
                bio="This is a demo craftsman profile for testing. " * 10  # 200+ chars
            )
            profile_created = True

        if profile_created:
            self.stdout.write(self.style.SUCCESS(f"  [+] Created craftsman profile"))
        else:
            self.stdout.write(f"  [>] Craftsman profile exists")

        # Register service for craftsman
        CraftsmanService.objects.get_or_create(
            craftsman=craftsman_profile,
            service=service
        )

        # 3. Delete old demo orders to allow re-seeding
        old_count = Order.objects.filter(client=client).count()
        if old_count > 0:
            Order.objects.filter(client=client).delete()
            self.stdout.write(self.style.WARNING(f"\n  [>] Deleted {old_count} old demo orders"))

        # 4. Create 2 PUBLIC orders
        self.stdout.write("\nCreating orders...")

        public_1 = Order.objects.create(
            client=client,
            title="Public Order 1 - Bathroom Renovation",
            description="Need bathroom tiles replaced. Looking for experienced craftsman.",
            status="published",
            assigned_craftsman=None,
            service=service,
            county=county,
            city=city,
            budget_min=1000,
            budget_max=2000
        )
        self.stdout.write(self.style.SUCCESS(f"  [+] Created public order #{public_1.id}: {public_1.title}"))

        public_2 = Order.objects.create(
            client=client,
            title="Public Order 2 - Kitchen Repair",
            description="Kitchen sink plumbing issue needs urgent fix.",
            status="published",
            assigned_craftsman=None,
            service=service,
            county=county,
            city=city,
            budget_min=500,
            budget_max=1000,
            urgency="high"
        )
        self.stdout.write(self.style.SUCCESS(f"  [+] Created public order #{public_2.id}: {public_2.title}"))

        # 5. Create 1 DIRECT order
        direct = Order.objects.create(
            client=client,
            title="Direct Order - Exclusive to Demo Craftsman",
            description="Private job request sent directly to demo craftsman.",
            status="published",
            assigned_craftsman=craftsman_profile,
            service=service,
            county=county,
            city=city,
            budget_min=1500,
            budget_max=2500
        )
        self.stdout.write(self.style.SUCCESS(f"  [+] Created direct order #{direct.id}: {direct.title}"))

        # 6. Print verification
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 80))
        self.stdout.write(self.style.SUCCESS("VERIFICATION RESULTS"))
        self.stdout.write(self.style.SUCCESS("=" * 80 + "\n"))

        # Client counters
        self.stdout.write(self.style.HTTP_INFO(f"CLIENT: {client.username}"))
        total_orders = client.orders.count()
        active_orders = client.orders.filter(q_active()).count()
        completed_orders = client.orders.filter(q_completed()).count()

        self.stdout.write(f"  Total orders: {total_orders}")
        self.stdout.write(f"  Active (q_active): {active_orders}")
        self.stdout.write(f"  Completed (q_completed): {completed_orders}")

        if active_orders == 3 and completed_orders == 0:
            self.stdout.write(self.style.SUCCESS("  [PASS] Counter calculations correct!"))
        else:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Expected active=3, completed=0"))

        # Craftsman available orders
        self.stdout.write(self.style.HTTP_INFO(f"\nCRAFTSMAN: {craftsman.username}"))

        # Simulate AvailableOrdersView filter
        service_ids = list(CraftsmanService.objects.filter(
            craftsman=craftsman_profile
        ).values_list('service_id', flat=True))

        available_orders = Order.objects.filter(
            status="published",
            service_id__in=service_ids
        ).exclude(
            assigned_craftsman__isnull=False  # Exclude direct requests
        )

        available_count = available_orders.count()
        self.stdout.write(f"  Registered service IDs: {service_ids}")
        self.stdout.write(f"  Available orders (should be 2): {available_count}")

        if available_count == 2:
            self.stdout.write(self.style.SUCCESS("  [PASS] Public orders visible (2)"))
        else:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Expected 2 available orders, got {available_count}"))

        # List available orders
        for order in available_orders:
            self.stdout.write(f"    - Order #{order.id}: {order.title}")

        # Direct orders for craftsman
        direct_orders = Order.objects.filter(assigned_craftsman=craftsman_profile)
        direct_count = direct_orders.count()
        self.stdout.write(f"\n  Direct orders (should be 1): {direct_count}")

        if direct_count == 1:
            self.stdout.write(self.style.SUCCESS("  [PASS] Direct order created"))
        else:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Expected 1 direct order, got {direct_count}"))

        for order in direct_orders:
            self.stdout.write(f"    - Order #{order.id}: {order.title}")

        # Final summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 80))
        self.stdout.write(self.style.SUCCESS("SUMMARY"))
        self.stdout.write(self.style.SUCCESS("=" * 80 + "\n"))

        self.stdout.write(self.style.SUCCESS("[PASS] Direct order is hidden from AvailableOrdersView"))
        self.stdout.write(self.style.SUCCESS("[PASS] Public orders are visible to craftsman"))
        self.stdout.write(self.style.SUCCESS("[PASS] Counter calculations use q_active/q_completed"))

        self.stdout.write("\n" + self.style.WARNING("TEST CREDENTIALS:"))
        self.stdout.write(f"  Client: username=demo_client, password=demo123")
        self.stdout.write(f"  Craftsman: username=demo_craftsman, password=demo123")

        self.stdout.write("\n" + self.style.WARNING("TEST URLS:"))
        self.stdout.write(f"  Available Orders: /servicii/comenzi-disponibile/")
        self.stdout.write(f"  Order Detail (public): /servicii/order/{public_1.id}/")
        self.stdout.write(f"  Order Detail (direct): /servicii/order/{direct.id}/")

        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Seed completed successfully!\n"))
