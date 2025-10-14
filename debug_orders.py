"""
E2E Order Visibility Audit Script
Analyzes order visibility across all views and identifies counter issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bricli.settings')
django.setup()

from services.models import Order, CraftsmanService, Quote
from services.querydefs import q_active, q_completed
from accounts.models import User, CraftsmanProfile
from django.db.models import Q

print("=" * 80)
print("1. ORDER MODEL FIELDS & DB STATUS VALUES")
print("=" * 80)

# Show all orders with full details
orders = Order.objects.all().select_related('client', 'assigned_craftsman__user', 'county', 'city', 'service')

print(f"\nTotal orders in DB: {orders.count()}")
print("\nOrder Details:")
for o in orders:
    print(f"\n  Order #{o.id}:")
    print(f"    Title: {o.title}")
    print(f"    Status: {o.status}")
    print(f"    Client: {o.client.username} (ID: {o.client.id})")
    print(f"    Assigned Craftsman: {o.assigned_craftsman.user.username if o.assigned_craftsman else 'None'} (ID: {o.assigned_craftsman_id or 'None'})")
    print(f"    County: {o.county.name}")
    print(f"    City: {o.city.name}")
    print(f"    Service: {o.service.name}")
    print(f"    Published At: {o.published_at}")
    print(f"    Created At: {o.created_at}")

print("\n" + "=" * 80)
print("2. STATUS GROUPS FROM MODEL")
print("=" * 80)
print(f"COMPLETED_STATUSES: {Order.COMPLETED_STATUSES}")
print(f"CANCELLED_STATUSES: {Order.CANCELLED_STATUSES}")
print(f"ACTIVE_STATUSES: {Order.ACTIVE_STATUSES}")

print("\n" + "=" * 80)
print("3. COUNTER CALCULATION TEST")
print("=" * 80)

# Get the client user (assuming the user who created orders)
client_user = Order.objects.first().client if Order.objects.exists() else None

if client_user:
    print(f"\nClient User: {client_user.username} (ID: {client_user.id})")

    # CURRENT BROKEN COUNTER (from template line 435, 439)
    print("\n--- CURRENT BROKEN COUNTER (order_detail_simple.html:435,439) ---")
    broken_active = client_user.orders.count()
    broken_completed = client_user.orders.count()
    print(f"  Active orders: {broken_active} (WRONG - counts ALL orders)")
    print(f"  Completed orders: {broken_completed} (WRONG - counts ALL orders)")

    # CORRECT COUNTER using querydefs
    print("\n--- CORRECT COUNTER (using querydefs.py) ---")
    active_orders = client_user.orders.filter(q_active())
    completed_orders = client_user.orders.filter(q_completed())
    print(f"  Active orders: {active_orders.count()} (CORRECT - uses q_active())")
    print(f"  Completed orders: {completed_orders.count()} (CORRECT - uses q_completed())")

    print("\n  Active orders detail:")
    for o in active_orders:
        print(f"    - Order #{o.id}: {o.title} (status={o.status})")

    print("\n  Completed orders detail:")
    for o in completed_orders:
        print(f"    - Order #{o.id}: {o.title} (status={o.status})")

print("\n" + "=" * 80)
print("4. AVAILABLEORDERSVIEW FILTER ANALYSIS")
print("=" * 80)

# Get a craftsman user
craftsman_profile = CraftsmanProfile.objects.first()

if craftsman_profile:
    craftsman_user = craftsman_profile.user
    print(f"\nCraftsman: {craftsman_user.username} (ID: {craftsman_user.id})")
    print(f"Craftsman Profile ID: {craftsman_profile.id}")

    # Get craftsman's registered services
    service_ids = CraftsmanService.objects.filter(craftsman=craftsman_profile).values_list('service_id', flat=True)
    print(f"\nCraftsman registered service IDs: {list(service_ids)}")

    print("\n--- FILTER BREAKDOWN FOR EACH ORDER ---")
    for order in orders:
        print(f"\n  Order #{order.id}: {order.title}")

        # Filter 1: status="published"
        filter1 = order.status == "published"
        print(f"    ✓ Filter 1 (status='published'): {filter1} (status={order.status})")

        # Filter 2: service in craftsman's services
        filter2 = order.service_id in service_ids
        print(f"    ✓ Filter 2 (service in craftsman services): {filter2} (order.service_id={order.service_id})")

        # Filter 3: hasn't quoted yet
        has_quoted = Quote.objects.filter(order=order, craftsman=craftsman_profile).exists()
        filter3 = not has_quoted
        print(f"    ✓ Filter 3 (hasn't quoted): {filter3} (has_quoted={has_quoted})")

        # Filter 4: not a direct request
        filter4 = order.assigned_craftsman_id is None
        print(f"    ✓ Filter 4 (not direct request): {filter4} (assigned_craftsman={order.assigned_craftsman_id})")

        # Final decision
        should_appear = filter1 and filter2 and filter3 and filter4
        print(f"    → FINAL: Should appear in AvailableOrdersView? {should_appear}")

print("\n" + "=" * 80)
print("5. VISIBILITY DECISION TABLE")
print("=" * 80)

print("\n| Order | Status     | Direct? | Target Craftsman | Should be on 'AvailableOrders'? | Why/why not |")
print("|-------|------------|---------|------------------|----------------------------------|-------------|")

for order in orders:
    is_direct = order.assigned_craftsman_id is not None
    target = order.assigned_craftsman.user.username if order.assigned_craftsman else "None"

    # Check if craftsman can see it
    if craftsman_profile:
        service_ids = CraftsmanService.objects.filter(craftsman=craftsman_profile).values_list('service_id', flat=True)
        has_quoted = Quote.objects.filter(order=order, craftsman=craftsman_profile).exists()

        should_appear = (
            order.status == "published" and
            order.service_id in service_ids and
            not has_quoted and
            order.assigned_craftsman_id is None
        )

        if not should_appear:
            if is_direct:
                reason = "Direct request (assigned_craftsman set)"
            elif order.status != "published":
                reason = f"Status is '{order.status}' (not published)"
            elif order.service_id not in service_ids:
                reason = "Service not in craftsman's registered services"
            elif has_quoted:
                reason = "Craftsman already quoted"
            else:
                reason = "Unknown"
        else:
            reason = "All filters pass"
    else:
        should_appear = "N/A"
        reason = "No craftsman to test"

    print(f"| #{order.id:3} | {order.status:10} | {'Yes' if is_direct else 'No':7} | {target:16} | {str(should_appear):32} | {reason:11} |")

print("\n" + "=" * 80)
print("6. FIX PLAN")
print("=" * 80)

print("""
PROBLEM 1: Counter Calculation in order_detail_simple.html (lines 435, 439)
---------------------------------------------------------------------------
CURRENT (BROKEN):
  <strong>{{ order.client.orders.count|default:0 }}</strong>

ISSUE:
  - Both "Active" and "Completed" counters use the same code: order.client.orders.count
  - This counts ALL orders regardless of status

FIX:
  Replace lines 435 and 439 in templates/services/order_detail_simple.html:

  Line 435: <strong>{{ order.client.orders.count|default:0 }}</strong>
  →→→ Replace with: <strong>{{ active_orders_count|default:0 }}</strong>

  Line 439: <strong>{{ order.client.orders.count|default:0 }}</strong>
  →→→ Replace with: <strong>{{ completed_orders_count|default:0 }}</strong>

  AND update services/views.py OrderDetailView.get_context_data() to add:

  from services.querydefs import q_active, q_completed

  context['active_orders_count'] = order.client.orders.filter(q_active()).count()
  context['completed_orders_count'] = order.client.orders.filter(q_completed()).count()


PROBLEM 2: AvailableOrdersView Filters (services/views.py:352-355)
-------------------------------------------------------------------
CURRENT (CORRECT):
  - Line 353: .filter(status="published", service_id__in=service_ids)
  - Line 354: .exclude(quotes__craftsman=craftsman)
  - Line 355: .exclude(assigned_craftsman__isnull=False)

STATUS: ✓ Filters are CORRECT
  - Excludes direct requests (assigned_craftsman set)
  - Only shows published orders
  - Filters by craftsman's registered services
  - Hides orders craftsman already quoted on

NO ACTION NEEDED for AvailableOrdersView filters.


PROBLEM 3: Coverage Area / Location Filters
--------------------------------------------
ISSUE: If CoverageArea filtering is enabled, it might hide ALL orders

CHECK: services/views.py lines 785-786 (InviteCraftsmenView)
  # TODO: Implement distance-based filtering

STATUS: Coverage filtering is NOT implemented yet (just a TODO comment)

NO ACTION NEEDED - coverage filtering not active.


SUMMARY:
--------
✓ AvailableOrdersView filters are correct
✓ No coverage area issues (not implemented)
✗ Counter calculation is BROKEN (counts all orders, not filtered by status)

FIX REQUIRED: Update order_detail_simple.html counters + OrderDetailView context
""")
