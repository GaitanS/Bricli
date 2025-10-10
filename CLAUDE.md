# Claude Agent - Bricli Development Guide

## Project Overview
**Bricli** is a production-ready marketplace platform connecting clients with verified craftsmen in Romania (similar to MyBuilder). Built with Django 5.2.6 + Python 3.13.

**Core Value Proposition:**
- Clients post free job orders
- Craftsmen pay 20 RON lead fee to shortlist (get client contact info)
- Real-time notifications, messaging, reviews, wallet system

## Critical Rules

### Security (MANDATORY - NO EXCEPTIONS)
✅ **Allowed:**
- Security analysis and vulnerability detection
- Defensive security tools (rate limiting, input validation)
- Fix security issues (XSS, CSRF, SQL injection)
- Create detection rules and monitoring

❌ **Forbidden:**
- Offensive security tools or exploits
- Credential harvesting (bulk SSH keys, cookies, wallets)
- Malicious code generation
- Bypassing authentication/authorization

⚠️ **Always:**
- Sanitize ALL user inputs (use Django forms, ORM)
- Never commit secrets (.env, API keys)
- Use environment variables for sensitive data
- Apply principle of least privilege

### Code Quality Standards

#### 1. Incremental Development
- Small, focused commits with clear messages
- One feature/fix per commit
- Commit message format: `type(scope): description`
  - Examples: `feat(wallet): add DummyPaymentProvider`, `fix(csrf): add trusted origins`

#### 2. Test-Driven Development (TDD)
- **Write tests BEFORE implementing features** (or immediately after)
- Minimum test coverage: 80% for new code
- All tests must pass before committing: `pytest -v`
- Current baseline: 9 wallet tests (100% coverage for LeadFeeService)

#### 3. Documentation
- Update `PROJECT_STATUS.md` after major decisions
- Add docstrings to all functions/classes
- Comment WHY, not WHAT (code should be self-explanatory)
- Update README.md for user-facing changes

#### 4. Clean Code
- **DRY (Don't Repeat Yourself):** Extract reusable logic to services/utils
- Remove dead code: unused imports, commented blocks, old test files
- Follow PEP 8 style guide
- Use type hints where beneficial

## Verification Workflow (MANDATORY After Each Step)

### 1. Django System Check
```bash
python manage.py check
```
**Expected:** `System check identified 0 issues`

### 2. Security Deployment Check
```bash
python manage.py check --deploy
```
**Expected:** Address all CRITICAL and WARNING issues (INFO can wait)

### 3. Migrations Check
```bash
python manage.py makemigrations --check --dry-run
```
**Expected:** No pending migrations (or apply them immediately)

### 4. Test Suite
```bash
pytest -v                          # Run all tests
pytest services/test_wallet.py -v # Run specific module
pytest --cov=services --cov-report=html # Coverage report
```
**Expected:** All tests pass, coverage ≥80% for new code

### 5. Linting & Formatting (Optional but Recommended)
```bash
ruff check .           # Fast linter
black .                # Code formatter
ruff format .          # Alternative formatter
```
**Expected:** 0 linting errors, code formatted

### 6. Manual Smoke Test
1. Start server: `python manage.py runserver`
2. Navigate to http://localhost:8000
3. Test critical flows:
   - User registration/login
   - Create order (client)
   - Shortlist craftsman (triggers lead fee)
   - Wallet top-up (dummy mode)

## Project Structure

### Apps and Responsibilities

| App            | Purpose                                      | Key Models                          |
|----------------|----------------------------------------------|-------------------------------------|
| **accounts**   | User auth, profiles, portfolios              | User, CraftsmanProfile, Portfolio   |
| **core**       | Home, search, static pages, utilities        | (context processors, views)         |
| **services**   | Orders, quotes, reviews, wallet, payments    | Order, Quote, Review, Wallet        |
| **notifications** | Real-time notifications, push subscriptions | Notification, PushSubscription      |
| **messaging**  | Conversations, messages, attachments         | Conversation, Message               |
| **moderation** | Rate limiting, IP blocking, spam detection   | (rate limit decorators)             |

### Key Services

| Service              | File                           | Purpose                               |
|----------------------|--------------------------------|---------------------------------------|
| LeadFeeService       | services/lead_fee_service.py   | Atomic wallet deduction for shortlist |
| NotificationService  | notifications/services.py      | Send notifications (in-app, push)     |
| PushNotificationService | notifications/services.py   | Web push notifications via pywebpush  |
| DummyPaymentProvider | services/payment_dummy.py (P1) | Local dev without Stripe keys         |

### File Locations

```
bricli/
├── bricli/                # Project settings
│   ├── settings.py        # Main config (⚠️ has hardcoded keys - P1 fix)
│   ├── urls.py            # Root URL config
│   └── wsgi.py            # WSGI entry point
├── apps/                  # Django apps (accounts, core, services, etc.)
├── static/                # Static files (CSS, JS, images)
│   ├── css/               # Custom styles
│   ├── js/                # Custom scripts
│   └── vendor/            # P1: Local Bootstrap, FontAwesome
├── templates/             # Django templates
│   ├── base.html          # Base template (⚠️ uses CDN - P1 fix)
│   ├── accounts/
│   ├── services/
│   └── ...
├── media/                 # User uploads (profile pics, portfolios)
├── locale/                # P1: Translation files
├── tests/                 # Future: centralized test suite
├── PROJECT_STATUS.md      # **SOURCE OF TRUTH** for progress
├── CLAUDE.md              # This file
├── README.md              # P1: User-facing setup guide
├── Makefile               # P1: Dev workflow automation
├── pytest.ini             # Test configuration
├── requirements.txt       # Python dependencies
└── manage.py              # Django CLI
```

## Current Phase: P1 - Production Hardening

**Goal:** Make project production-ready with local-first dev experience.

**Focus Areas:**
1. **Web Security:** CSRF, secure cookies, CSP headers
2. **Local-First:** Self-hosted assets, DummyPaymentProvider
3. **Dev UX:** Makefile, README, comprehensive docs
4. **i18n Skeleton:** Multi-language support foundation
5. **Code Cleanup:** Remove dead files, add health endpoint

**Detailed Checklist:** See `PROJECT_STATUS.md` → P1 section

## Common Workflows

### Adding a New Feature
1. **Plan:** Update PROJECT_STATUS.md with feature description
2. **Design:** Sketch models, views, templates
3. **Test:** Write pytest tests for edge cases
4. **Implement:** Write minimal code to pass tests
5. **Verify:** Run full verification workflow (see above)
6. **Document:** Update README if user-facing, add docstrings
7. **Commit:** `git add . && git commit -m "feat(scope): description"`

### Fixing a Bug
1. **Reproduce:** Write a failing test that captures the bug
2. **Fix:** Make minimal changes to pass the test
3. **Verify:** Ensure no regressions (`pytest -v`)
4. **Document:** Update STATUS.md if critical bug
5. **Commit:** `git commit -m "fix(scope): description"`

### Deploying to Production
1. **Environment:** Set `DEBUG=False`, configure `.env`
2. **Database:** Migrate to PostgreSQL (uncomment psycopg2-binary)
3. **Static Files:** `python manage.py collectstatic --noinput`
4. **Security:** Verify all P1 security tasks complete
5. **Test:** Run deployment check: `python manage.py check --deploy`
6. **Monitor:** Set up Sentry, health endpoint `/api/health`

## Quick Reference

### Run Local Server
```bash
python manage.py runserver 0.0.0.0:8000
# P1: make run
```

### Run Tests
```bash
pytest -v                          # All tests
pytest services/test_wallet.py -v # Wallet tests only
pytest -k "test_lead_fee" -v      # Tests matching pattern
```

### Create Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Translation Workflow (P1)
```bash
python manage.py makemessages -l en      # Extract translatable strings
python manage.py compilemessages         # Compile .po to .mo
```

## Troubleshooting

### "Insufficient Balance" Error
- Check wallet balance: `CreditWallet.objects.get(user=craftsman).balance_lei`
- Top up: `wallet.add_amount(amount_cents=5000, reason='top_up', meta={})`

### Stripe Errors in Local Dev
- **P0 workaround:** Use valid test keys (pk_test_..., sk_test_...)
- **P1 solution:** DummyPaymentProvider auto-activates if STRIPE_SECRET_KEY missing

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATICFILES_DIRS` in settings.py
- Verify Whitenoise middleware order (must be after SecurityMiddleware)

### Tests Failing
1. Check database: `pytest --create-db` (force fresh DB)
2. Verify fixtures: Ensure test data is valid
3. Isolate: Run single test: `pytest path/to/test.py::test_name -v`

## Resources

- **Django Docs:** https://docs.djangoproject.com/en/5.2/
- **DRF Docs:** https://www.django-rest-framework.org/
- **pytest-django:** https://pytest-django.readthedocs.io/
- **Stripe Testing:** https://stripe.com/docs/testing

## Contact & Support

- **Project Owner:** See README.md
- **Issues:** Document in PROJECT_STATUS.md → Riscuri section
- **Questions:** Check this guide first, then ask in chat

---

**Last Updated:** 10 January 2025
**Current Phase:** P1 (Production Hardening)
**Status:** ✅ P0 Complete, 🔄 P1 In Progress
