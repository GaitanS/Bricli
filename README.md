# Bricli - Platformă de Conectare Clienți-Meșteri

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2.6](https://img.shields.io/badge/django-5.2.6-green.svg)](https://www.djangoproject.com/)
[![Tests Passing](https://img.shields.io/badge/tests-9/9_passing-success.svg)](services/test_wallet.py)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()

## 📋 Despre Proiect

**Bricli** este o platformă modernă tip marketplace care conectează clienții cu meșteri verificați din România, similară cu MyBuilder. Platforma permite clienților să posteze comenzi gratuit, iar meșteri să acceseze aceste comenzi plătind o taxă de lead de 20 RON.

### Caracteristici Principale

✅ **Pentru Clienți:**
- Postare comenzi gratuite
- Invitare meșteri specifici
- Shortlisting meșteri (selectare meșteri preferați)
- Sistem de review-uri și rating
- Mesagerie în timp real
- Notificări push și in-app

✅ **Pentru Meșteri:**
- Sistem wallet cu credit
- Taxă lead: 20 RON per shortlist
- Portfolio cu imagini
- Verificare CUI
- Istoric tranzacții
- Management oferte

🔐 **Securitate:**
- CSRF protection cu trusted origins
- Session cookies securizate (HTTPS only în producție)
- Content Security Policy (CSP) headers
- Rate limiting și IP blocking
- Two-factor authentication (2FA)

💳 **Plăți:**
- Integrare Stripe pentru plăți reale
- **DummyPaymentProvider** pentru dezvoltare locală (fără chei Stripe)
- Tranzacții atomice pentru integritate financiară
- Istoric complet al tranzacțiilor

---

## 🚀 Quick Start

### 1. Cerințe de Sistem

- **Python 3.13+** (sau 3.11+)
- **Git**
- **Make** (opțional, pentru comenzi rapide)
- **Windows/Linux/macOS**

### 2. Instalare

```bash
# Clonează repository-ul
git clone <repository-url>
cd Bricli

# Creează și activează virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# Instalează dependințele
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurare

Creează fișierul `.env` (copiază din `.env.example`):

```bash
# Copiază template-ul
cp .env.example .env

# Editează .env cu setările tale
# (vezi secțiunea Configurare Detaliată mai jos)
```

**Configurare minimă pentru dezvoltare locală** (`.env`):

```env
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-here

# Stripe (opțional pentru dev local - va folosi DummyPaymentProvider)
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_or_leave_placeholder
STRIPE_SECRET_KEY=sk_test_your_key_or_leave_placeholder
```

### 4. Inițializare Bază de Date

```bash
# Rulează migrațiile
python manage.py migrate

# Creează un superuser (admin)
python manage.py createsuperuser
```

### 5. Pornește Serverul

```bash
# Start server de dezvoltare
python manage.py runserver 0.0.0.0:8000

# Sau folosind Makefile
make run
```

Accesează:
- **Homepage:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin

---

## 🛠️ Folosind Makefile

Makefile-ul oferă comenzi convenabile pentru dezvoltare:

```bash
# Afișează toate comenzile disponibile
make help

# Setup inițial (venv + deps + migrate)
make init

# Rulează serverul de dezvoltare
make run

# Rulează teste
make test              # Toate testele
make test-verbose      # Cu output detaliat
make test-coverage     # Cu coverage report

# Verificări
make check             # Django system check
make deploy-check      # Security check

# Code quality
make lint              # Rulează linter
make fmt               # Formatează cod

# Utilități
make migrate           # Rulează migrații
make superuser         # Creează admin
make collectstatic     # Colectează static files
make clean             # Curăță cache și artifacts
```

---

## 🧪 Testare

### Rulare Teste

```bash
# Toate testele
pytest -v

# Doar wallet tests (9 tests)
pytest services/test_wallet.py -v

# Cu coverage report
pytest --cov=services --cov-report=html

# Vezi coverage în browser
# Deschide htmlcov/index.html
```

### Test Coverage

**Current Coverage:** 9/9 wallet tests passing (100% pentru LeadFeeService)

```
services/test_wallet.py::TestWalletOperations
  ✓ test_wallet_creation
  ✓ test_wallet_top_up
  ✓ test_wallet_deduct_success
  ✓ test_wallet_deduct_insufficient_balance
  ✓ test_has_sufficient_balance

services/test_wallet.py::TestLeadFeeService
  ✓ test_charge_shortlist_fee_sufficient_balance
  ✓ test_charge_shortlist_fee_insufficient_balance
  ✓ test_charge_shortlist_fee_no_existing_wallet_fails
  ✓ test_can_afford_shortlist
```

---

## 💰 Dummy Payment Mode (Dezvoltare Locală)

Bricli include **DummyPaymentProvider** pentru dezvoltare locală fără chei Stripe reale.

### Activare Automată

Dummy mode se activează automat când:
- `STRIPE_SECRET_KEY` lipsește din `.env`
- `STRIPE_SECRET_KEY` conține placeholder-uri (ex: `your-stripe-key`, `sk_test_51234...`)

### Funcționare

1. **Acces la wallet top-up:** http://localhost:8000/services/wallet/topup/
2. **Banner de avertizare:** Vei vedea un mesaj galben: *"Mod Dezvoltare Activ - Plățile sunt simulate local"*
3. **Selectează suma:** Alege orice sumă (ex: 50 RON, 100 RON)
4. **Plată instantanee:** Click pe buton → wallet-ul este creditat imediat
5. **Verificare:** Vizualizează soldul actualizat

### Log Output

În console vei vedea:

```
INFO: 🔧 Stripe disabled - using DummyPaymentProvider for local development
INFO: 💳 Dummy Payment Intent Created: dummy_pi_abc123xyz... | Amount: 50.00 RON
```

### Revenire la Stripe Real

Pentru a folosi Stripe real:

1. Obține chei de test de la https://dashboard.stripe.com/test/apikeys
2. Actualizează `.env`:

```env
STRIPE_PUBLISHABLE_KEY=pk_test_your_real_key_here
STRIPE_SECRET_KEY=sk_test_your_real_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

3. Restart server → dummy mode se dezactivează automat

---

## 🌐 Scenariu End-to-End (E2E)

### Fluxul Complet: Client → Comandă → Meșter → Lead Fee

#### Pas 1: Înregistrare Utilizatori

**Client:**
```
1. Navighează la /accounts/register/
2. Selectează tip: "Client"
3. Completează formular (nume, email, parolă)
4. Login la /accounts/login/
```

**Meșter:**
```
1. Navighează la /accounts/craftsman/register/
2. Completează formular extins (nume, CUI, servicii, județ)
3. Login
4. Alimentează wallet: /services/wallet/topup/
   → În dummy mode: selectează 100 RON → creditat instant
```

#### Pas 2: Client Creează Comandă

```
1. Login ca client
2. Navighează la /services/orders/create/
3. Completează:
   - Titlu: "Renovare baie completă"
   - Descriere: Detalii lucrare
   - Categorie: Instalații sanitare
   - Județ/Oraș: București
   - Status: Published
4. Submit → Comanda este vizibilă în /services/orders/available/
```

#### Pas 3: Meșter Vizualizează Comenzi

```
1. Login ca meșter
2. Navighează la /services/orders/available/
3. Vezi comanda "Renovare baie completă"
4. Click pe comandă → Vezi detalii
```

#### Pas 4: Client Shortlistează Meșterul

```
1. Login ca client
2. Navighează la /services/orders/<order_id>/invite/
3. Vezi lista meșteri disponibili
4. Click "Shortlist" pe meșterul dorit
   → Backend: LeadFeeService.charge_shortlist_fee()
   → Deduce 20 RON din wallet-ul meșterului
   → Creează Shortlist entry
   → Trimite notificare meșterului
5. Verificare: Wallet-ul meșterului scade cu 20 RON
```

#### Pas 5: Meșter Trimite Ofertă

```
1. Login ca meșter
2. Navighează la /notifications/ → Vezi notificare: "Ai fost shortlistat!"
3. Click pe notificare → Acces la comandă
4. Trimite ofertă cu preț și detalii
```

#### Pas 6: Client Acceptă Oferta

```
1. Login ca client
2. Navighează la /services/orders/<order_id>/
3. Vezi ofertă de la meșter
4. Click "Acceptă ofertă"
   → Dezvăluie datele de contact reciproce
   → Pornește conversație în /messages/
```

#### Pas 7: Comunicare și Finalizare

```
1. Ambii utilizatori pot accesa /messages/
2. Exchange mesaje, detalii, date întâlnire
3. După finalizare lucrare:
   - Client marchează comandă ca "Completed"
   - Client lasă review la /services/reviews/create/
   - Meșter primește rating
```

### Verificări După E2E

```bash
# Check wallet transactions
python manage.py shell
>>> from services.models import CreditWallet, WalletTransaction
>>> wallet = CreditWallet.objects.get(user__username='meșter1')
>>> wallet.balance_lei
80.0  # 100 - 20 lead fee
>>> WalletTransaction.objects.filter(wallet=wallet, reason='lead_fee')
<QuerySet [<WalletTransaction: -20 RON lead_fee>]>
```

---

## 📖 Structura Proiectului

```
Bricli/
├── accounts/           # User management, profiles, portfolios
│   ├── models.py       # User, CraftsmanProfile, County, City
│   ├── views.py        # Registration, login, profile edit
│   └── forms.py        # User registration forms
├── core/               # Homepage, search, static pages
│   ├── views.py        # Home, search, about, FAQ
│   └── context_processors.py  # Global template variables
├── services/           # Orders, quotes, wallet, payments
│   ├── models.py       # Order, Quote, Review, Wallet, Transaction
│   ├── views.py        # Order CRUD, wallet views
│   ├── payment_views.py         # Stripe integration
│   ├── payment_dummy.py         # Dummy payment provider (P1)
│   ├── lead_fee_service.py      # Lead fee charging logic
│   └── test_wallet.py           # 9 wallet tests
├── messaging/          # Real-time conversations
│   ├── models.py       # Conversation, Message
│   └── views.py        # Conversation list, detail
├── notifications/      # In-app and push notifications
│   ├── models.py       # Notification, NotificationPreference
│   ├── services.py     # NotificationService, PushNotificationService
│   └── serializers.py  # DRF serializers for API
├── moderation/         # Rate limiting, IP blocking
│   ├── decorators.py   # @rate_limit decorator
│   └── middleware.py   # IP blocking middleware
├── templates/          # Django templates
│   ├── base.html       # Base layout (Bootstrap + CSP-safe)
│   ├── accounts/       # User templates
│   ├── services/       # Order/wallet templates
│   └── ...
├── static/             # Static assets (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── vendor/         # P1: Local Bootstrap, FontAwesome (future)
├── media/              # User uploads (profiles, portfolios)
├── locale/             # i18n translation files (P1)
├── bricli/             # Project settings
│   ├── settings.py     # Main settings (CSP, CSRF, security)
│   ├── urls.py         # Root URL config
│   └── wsgi.py         # WSGI entry point
├── manage.py           # Django CLI
├── Makefile            # Dev workflow automation
├── pytest.ini          # Test configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git exclusions
├── PROJECT_STATUS.md   # Technical documentation & progress
├── CLAUDE.md           # Development guide & rules
└── README.md           # This file
```

---

## 🌍 Internalizare (i18n)

Bricli este configurat pentru suport multi-limbă:

```python
# settings.py
LANGUAGES = [
    ('ro', 'Romanian'),
    ('en', 'English'),
]
```

### Comenzi i18n

```bash
# Extrage stringuri traducibile
python manage.py makemessages -l en

# Compilează traducerile
python manage.py compilemessages

# Sau folosind Makefile
make makemessages
make compilemessages
```

### Marcare Stringuri pentru Traducere

În template-uri:

```django
{% load i18n %}
<h1>{% trans "Welcome to Bricli" %}</h1>
<p>{% trans "Find the best craftsmen in Romania" %}</p>
```

În Python:

```python
from django.utils.translation import gettext as _

message = _("Order created successfully")
```

---

## 🔐 Deployment în Producție

### Checklist Pre-Deployment

1. **Environment Variables** (.env):

```env
DEBUG=False
SECRET_KEY=your-long-random-secret-key-here
ALLOWED_HOSTS=bricli.ro,www.bricli.ro

# Database
DATABASE_URL=postgres://user:password@localhost:5432/bricli_db

# Stripe (chei reale de producție)
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key
STRIPE_SECRET_KEY=sk_live_your_live_key
STRIPE_WEBHOOK_SECRET=whsec_live_webhook_secret

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@bricli.ro
EMAIL_HOST_PASSWORD=your-app-password
```

2. **Security Settings** (activate automat când DEBUG=False):

```python
# În settings.py - deja configurate:
SESSION_COOKIE_SECURE = not DEBUG  # True în producție
CSRF_COOKIE_SECURE = not DEBUG      # True în producție
CSRF_TRUSTED_ORIGINS = ['https://bricli.ro', 'https://www.bricli.ro']
```

3. **Database Migration**:

```bash
# Instalează psycopg2 (uncomment în requirements.txt)
pip install psycopg2-binary

# Configurează DATABASE_URL în .env
# Rulează migrații
python manage.py migrate --settings=bricli.settings
```

4. **Static Files**:

```bash
# Colectează toate static files
python manage.py collectstatic --noinput

# Whitenoise va servi static files automat
```

5. **Run Deployment Checks**:

```bash
# Verifică security warnings
python manage.py check --deploy

# Fix toate CRITICAL și WARNING issues
```

6. **Monitoring**:

```python
# settings.py - configurează Sentry
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
)
```

### Deployment cu Gunicorn

```bash
# Instalează gunicorn (deja în requirements.txt)
pip install gunicorn

# Pornește server
gunicorn bricli.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 60
```

### Deployment cu Docker (viitor)

```dockerfile
# Dockerfile (TODO - P2)
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "bricli.wsgi:application"]
```

---

## 🔧 Troubleshooting

### 1. "Insufficient Balance" Error

**Problema:** Meșterul nu poate face shortlist.

**Soluție:**

```python
# Django shell
python manage.py shell

from services.models import CreditWallet

# Check balance
wallet = CreditWallet.objects.get(user__username='meșter1')
print(wallet.balance_lei)  # Ex: 0.0

# Top up (dummy mode or real)
wallet.add_amount(amount_cents=10000, reason='top_up', meta={})
print(wallet.balance_lei)  # 100.0
```

### 2. Stripe Errors în Local Dev

**Problema:** `stripe.error.AuthenticationError: Invalid API Key`

**Soluție 1:** Folosește dummy mode (lasă STRIPE_SECRET_KEY placeholder)

**Soluție 2:** Obține chei test de la Stripe:
- https://dashboard.stripe.com/test/apikeys
- Actualizează `.env` cu chei reale

### 3. Static Files Nu Se Încarcă

**Problema:** 404 pentru CSS/JS

**Soluție:**

```bash
# Verifică STATIC_ROOT și STATICFILES_DIRS
python manage.py collectstatic

# Check Whitenoise middleware order
# Should be after SecurityMiddleware in settings.py

# În development, asigură-te că DEBUG=True
```

### 4. CSRF Verification Failed

**Problema:** 403 Forbidden la POST requests

**Soluție:**

```python
# Verifică CSRF_TRUSTED_ORIGINS în settings.py
CSRF_TRUSTED_ORIGINS = [
    'https://bricli.ro',
    'https://www.bricli.ro',
]

# În development, asigură-te că incluzi localhost:
# (doar pentru test local, nu commita)
CSRF_TRUSTED_ORIGINS += ['http://localhost:8000']
```

### 5. Tests Failing

**Problema:** `pytest` returnează erori

**Soluție:**

```bash
# Recreează database de test
pytest --create-db

# Rulează cu verbose pentru detalii
pytest -vv --tb=short

# Check specific test
pytest services/test_wallet.py::TestWalletOperations::test_wallet_top_up -v
```

---

## 📚 Resurse Adiționale

### Documentație

- **PROJECT_STATUS.md** - Status proiect, arhitectură, decizii tehnice
- **CLAUDE.md** - Ghid dezvoltare pentru agenți Claude
- **.vscode/settings.json** - Configurare IDE pentru Python/Django

### Links Utile

- [Django Documentation](https://docs.djangoproject.com/en/5.2/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Stripe Testing](https://stripe.com/docs/testing)
- [pytest-django](https://pytest-django.readthedocs.io/)

### Testing Cards (Stripe)

Pentru testare Stripe (dacă nu folosești dummy mode):

```
Card Number: 4242 4242 4242 4242
Expiry: Any future date (ex: 12/34)
CVC: Any 3 digits (ex: 123)
ZIP: Any 5 digits (ex: 12345)
```

---

## 👥 Contributing

1. Fork repository
2. Creează branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Commit Message Format

```
type(scope): subject

Types: feat, fix, docs, style, refactor, test, chore
Examples:
  feat(wallet): add DummyPaymentProvider for local dev
  fix(csrf): add trusted origins for production domains
  docs(readme): add E2E testing scenario
```

---

## 📄 License

**Proprietary** - Toate drepturile rezervate.

---

## 📞 Support

Pentru suport tehnic:
- **Issues:** [GitHub Issues](https://github.com/your-org/bricli/issues)
- **Email:** support@bricli.ro
- **Documentație:** Citește `PROJECT_STATUS.md` și `CLAUDE.md`

---

**Ultima actualizare:** 10 Ianuarie 2025
**Versiune:** 1.0.0 (P1 Production Hardening)
