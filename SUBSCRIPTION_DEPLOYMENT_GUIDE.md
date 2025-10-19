# Subscription System - Production Deployment Guide

**Date:** 19 Octombrie 2025
**Status:** Ready for Production Deployment

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Stripe Configuration](#stripe-configuration)
3. [Smart Bill Configuration](#smartbill-configuration)
4. [Environment Variables](#environment-variables)
5. [Database Migration](#database-migration)
6. [Testing Checklist](#testing-checklist)
7. [Go-Live Procedure](#go-live-procedure)
8. [Monitoring](#monitoring)
9. [Rollback Plan](#rollback-plan)

---

## Prerequisites

### Required Accounts
- ✅ Stripe account (https://stripe.com)
- ✅ Smart Bill account (https://smartbill.ro)
- ✅ Production email server (SMTP)
- ✅ Production database backup

### Required Packages
All required packages are already in `requirements.txt`:
```bash
Django==5.2.6
stripe==11.3.0
requests==2.32.3
django-ratelimit==4.1.0
pywebpush==2.0.0
```

---

## Stripe Configuration

### Step 1: Create Products in Stripe Dashboard

1. **Log in to Stripe Dashboard**: https://dashboard.stripe.com

2. **Navigate to Products**:
   - Click "Products" → "Add product"

3. **Create "Bricli Plus" Product**:
   ```
   Name: Bricli Plus
   Description: Abonament Plus - Lead-uri nelimitate
   Pricing Model: Recurring
   Price: 49.00 RON
   Billing Period: Monthly
   ```
   - Click "Save product"
   - **Copy the Price ID** (format: `price_xxxxxxxxxxxxx`)
   - Save as `PLUS_PRICE_ID`

4. **Create "Bricli Pro" Product**:
   ```
   Name: Bricli Pro
   Description: Abonament Pro - Lead-uri nelimitate + Features Premium
   Pricing Model: Recurring
   Price: 149.00 RON
   Billing Period: Monthly
   ```
   - Click "Save product"
   - **Copy the Price ID** (format: `price_xxxxxxxxxxxxx`)
   - Save as `PRO_PRICE_ID`

5. **Enable Proration**:
   - Go to Settings → Billing → Subscriptions
   - Enable "Proration" for subscription changes
   - Save settings

### Step 2: Configure Webhook

1. **Navigate to Webhooks**:
   - Go to Developers → Webhooks
   - Click "Add endpoint"

2. **Configure Endpoint**:
   ```
   Endpoint URL: https://bricli.ro/abonamente/webhook/stripe/
   Description: Bricli Subscription Webhooks

   Events to send:
   ✅ invoice.payment_succeeded
   ✅ invoice.payment_failed
   ✅ customer.subscription.deleted
   ✅ customer.subscription.updated
   ✅ charge.dispute.created
   ```

3. **Save and Copy Signing Secret**:
   - Click "Add endpoint"
   - **Copy the Signing Secret** (format: `whsec_xxxxxxxxxxxxx`)
   - Save as `STRIPE_WEBHOOK_SECRET`

### Step 3: Update Subscription Tiers in Database

Run Django shell:
```bash
python manage.py shell
```

```python
from subscriptions.models import SubscriptionTier

# Update Plus tier
plus_tier = SubscriptionTier.objects.get(name='plus')
plus_tier.stripe_price_id = 'price_PLUS_ID_HERE'  # Replace with actual Price ID
plus_tier.save()

# Update Pro tier
pro_tier = SubscriptionTier.objects.get(name='pro')
pro_tier.stripe_price_id = 'price_PRO_ID_HERE'  # Replace with actual Price ID
pro_tier.save()

print("✅ Stripe Price IDs updated successfully!")
```

---

## Smart Bill Configuration

### Step 1: Get API Credentials

1. **Log in to Smart Bill**: https://smartbill.ro
2. **Navigate to Settings → Integrari → API**
3. **Generate API Token**:
   - Click "Generează token nou"
   - **Copy the API Token**
   - Save as `SMARTBILL_API_TOKEN`

### Step 2: Get Company Details

1. **Get Company VAT Code (CUI)**:
   - Navigate to Settings → Date firmă
   - Copy your CUI (format: `RO12345678` or just `12345678`)
   - Save as `SMARTBILL_COMPANY_VAT_CODE`

2. **Create Invoice Series**:
   - Navigate to Facturi → Configurare serii
   - Create new series: `SUBS` (for subscriptions)
   - Save as `SMARTBILL_INVOICE_SERIES`

### Step 3: Get Username

Your Smart Bill username is the email you used to register:
- Save as `SMARTBILL_USERNAME`

---

## Environment Variables

### Production .env File

Create/update `.env` file in project root:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=bricli.ro,www.bricli.ro
SITE_URL=https://bricli.ro

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@localhost:5432/bricli_production

# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Smart Bill Configuration
SMARTBILL_USERNAME=your-email@example.com
SMARTBILL_API_TOKEN=your-api-token-here
SMARTBILL_COMPANY_VAT_CODE=RO12345678
SMARTBILL_INVOICE_SERIES=SUBS

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@bricli.ro
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=Bricli <noreply@bricli.ro>

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Update Django Settings

In `bricli/settings.py`, ensure you have:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Stripe
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Smart Bill
SMARTBILL_USERNAME = os.getenv('SMARTBILL_USERNAME')
SMARTBILL_API_TOKEN = os.getenv('SMARTBILL_API_TOKEN')
SMARTBILL_COMPANY_VAT_CODE = os.getenv('SMARTBILL_COMPANY_VAT_CODE')
SMARTBILL_INVOICE_SERIES = os.getenv('SMARTBILL_INVOICE_SERIES', 'SUBS')

# Site
SITE_URL = os.getenv('SITE_URL', 'https://bricli.ro')
```

---

## Database Migration

### Step 1: Backup Current Database

```bash
# PostgreSQL
pg_dump bricli_production > backup_pre_subscription_$(date +%Y%m%d).sql

# Or Django dumpdata
python manage.py dumpdata > backup_full_$(date +%Y%m%d).json
```

### Step 2: Apply Migrations

```bash
# Check for pending migrations
python manage.py makemigrations --check

# Apply all migrations
python manage.py migrate

# Verify
python manage.py check --deploy
```

### Step 3: Seed Subscription Tiers

```bash
# Create the 3 subscription tiers
python manage.py seed_tiers

# Verify
python manage.py shell
>>> from subscriptions.models import SubscriptionTier
>>> SubscriptionTier.objects.all()
<QuerySet [<SubscriptionTier: free>, <SubscriptionTier: plus>, <SubscriptionTier: pro>]>
```

### Step 4: Migrate Existing Craftsmen to Free Tier

```bash
# Assign Free tier to all existing craftsmen
python manage.py migrate_existing_craftsmen

# Output should show:
# ✅ Created 50 subscriptions
# ✅ All craftsmen migrated to Free tier
```

---

## Testing Checklist

### Test in Stripe Test Mode First

1. **Enable Stripe Test Mode**:
   ```bash
   # Use test keys
   STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
   STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
   ```

2. **Test Payment Flow**:
   - [ ] Visit `/abonamente/preturi/`
   - [ ] Click "Upgrade la Plus"
   - [ ] Fill fiscal data
   - [ ] Use test card: `4242 4242 4242 4242`
   - [ ] Verify subscription created
   - [ ] Check email received

3. **Test Webhook Events**:
   - [ ] Use Stripe CLI: `stripe listen --forward-to localhost:8000/abonamente/webhook/stripe/`
   - [ ] Trigger `invoice.payment_succeeded`
   - [ ] Verify invoice generated in Smart Bill (test mode)
   - [ ] Check email sent

4. **Test Cancellation**:
   - [ ] Go to `/abonamente/manage/`
   - [ ] Click "Anulează Abonament"
   - [ ] Verify status changes
   - [ ] Check email received

5. **Test Refund**:
   - [ ] Upgrade within 14 days
   - [ ] Request refund
   - [ ] Verify Stripe refund
   - [ ] Check email received

### Smart Bill Test Mode

Smart Bill doesn't have a test mode. **Do NOT generate real invoices during testing.**

Options:
1. Use a separate Smart Bill account for testing
2. Delete test invoices manually after testing
3. Skip Smart Bill during initial tests (will create pending invoices)

---

## Go-Live Procedure

### Day Before Launch

1. **Final Database Backup**:
   ```bash
   pg_dump bricli_production > backup_pre_subscription_launch.sql
   ```

2. **Update Environment to Production**:
   - Switch to live Stripe keys
   - Verify all env variables

3. **Send Pre-Launch Email**:
   - Notify all craftsmen about new subscription system
   - 14-day notice period

### Launch Day

1. **Deploy Code** (2:00 AM - Low traffic):
   ```bash
   git pull origin main
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   sudo systemctl restart gunicorn
   ```

2. **Seed Tiers**:
   ```bash
   python manage.py seed_tiers
   ```

3. **Migrate Craftsmen**:
   ```bash
   python manage.py migrate_existing_craftsmen
   ```

4. **Verify Webhook Endpoint**:
   - Test webhook from Stripe Dashboard
   - Check logs: `tail -f /var/log/bricli/application.log`

5. **Monitor First Hour**:
   - Watch for errors in Sentry
   - Check webhook success rate
   - Monitor email delivery

---

## Monitoring

### Key Metrics to Watch

1. **Subscription Metrics**:
   - Active subscriptions (Free/Plus/Pro)
   - Conversion rate (Free → Paid)
   - Churn rate

2. **Payment Metrics**:
   - Payment success rate (should be >90%)
   - Failed payments
   - Grace period expirations

3. **Technical Metrics**:
   - Webhook success rate (should be >95%)
   - Smart Bill API success rate (should be >90%)
   - Email delivery rate

### Setup Monitoring Alerts

1. **Stripe Dashboard Alerts**:
   - Failed payments >5%
   - Dispute created

2. **Sentry Alerts**:
   - Webhook failures
   - Smart Bill API errors
   - Email send failures

3. **Cron Jobs**:
   ```cron
   # Retry failed invoices every 15 minutes
   */15 * * * * cd /path/to/bricli && python manage.py retry_failed_invoices

   # Check expired grace periods daily at 3 AM
   0 3 * * * cd /path/to/bricli && python manage.py check_expired_grace_periods
   ```

---

## Rollback Plan

### If Critical Issues Occur

1. **Disable Subscription Enforcement**:
   ```python
   # In settings.py
   SUBSCRIPTION_ENFORCEMENT_ENABLED = False
   ```
   This allows all craftsmen unlimited access temporarily.

2. **Stop Webhooks**:
   - Comment out webhook handler
   - Return 503 Service Unavailable

3. **Restore Database**:
   ```bash
   psql bricli_production < backup_pre_subscription_launch.sql
   python manage.py migrate subscriptions zero
   ```

4. **Refund All Payments**:
   ```python
   # Django shell
   from subscriptions.models import CraftsmanSubscription
   from subscriptions.services import SubscriptionService

   for sub in CraftsmanSubscription.objects.filter(tier__name__in=['plus', 'pro']):
       try:
           SubscriptionService.request_refund(sub.craftsman)
       except Exception as e:
           print(f"Failed refund for {sub.id}: {e}")
   ```

5. **User Communication**:
   - Send apology email
   - Offer compensation (e.g., 100 RON wallet credit)

---

## Support Contacts

- **Stripe Support**: https://support.stripe.com
- **Smart Bill Support**: support@smartbill.ro / +40 21 300 8484
- **Django Admin**: Check `/admin/` for subscription management

---

## Success Criteria

Launch is successful if after 24 hours:
- ✅ Payment success rate >90%
- ✅ Webhook success rate >95%
- ✅ Smart Bill API success rate >90%
- ✅ No critical errors in Sentry
- ✅ All craftsmen have subscriptions assigned
- ✅ At least 1 successful upgrade to paid tier

---

**Last Updated:** 19 Octombrie 2025
**Version:** 1.0
**Owner:** Bricli Development Team
