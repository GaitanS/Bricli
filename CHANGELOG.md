# Changelog - Bricli Platform

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - P0 Critical Features (2025-01-10)

#### Dependencies & Configuration
- Added `stripe` (11.1.1) for payment processing
- Added `pywebpush` (2.0.1) for push notifications
- Added `requests` (2.32.3) as explicit dependency
- Configured Whitenoise middleware for static files serving with compression
- Added comprehensive `.gitignore` for Python/Django projects
- Added `pytest.ini` for test configuration with Django support

#### Lead Fee & Wallet System (BREAKING CHANGE)
- **BREAKING**: Shortlisting craftsmen now requires sufficient wallet balance
- Implemented `LeadFeeService` for automatic wallet deduction on shortlist
- Added `InsufficientBalanceError` exception for balance validation
- Integrated lead fee charging into `ShortlistCraftsmanView`
- Default lead fee: **20 RON (2000 cents)** per shortlist
- All wallet operations are atomic using database transactions

#### Testing Infrastructure
- Implemented 9 comprehensive tests for wallet and lead fee operations:
  - 5 tests for wallet operations (create, top-up, deduct, balance validation)
  - 4 tests for lead fee service (sufficient/insufficient balance, affordability)
- All tests passing ✓

### Changed

- Removed duplicate `Pillow` entry from requirements.txt
- Commented out `psycopg2-binary` (fails on Windows Python 3.13 - use for production with PostgreSQL)
- Updated `ShortlistCraftsmanView` with comprehensive error handling
- Enhanced wallet deduction with detailed transaction metadata

### Fixed

- Static files now properly served in both development and production (Whitenoise)
- Wallet balance validation prevents over-deduction
- Proper handling of non-craftsman users in lead fee charging

### Removed

- Removed tracked artifacts from git: `db.sqlite3`, `media/`, `staticfiles/`

---

## Testing

Run tests with:
```bash
pytest services/test_wallet.py -v
```

## Migration Notes

### For Production Deployment:
1. Ensure PostgreSQL is configured (install `psycopg2-binary` separately on Linux)
2. Set environment variables in `.env`:
   - `SECRET_KEY`
   - `DEBUG=False`
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
3. Run `python manage.py collectstatic` for static files
4. Ensure craftsmen have wallet balance before enabling shortlist feature

### Breaking Changes:
- **Shortlisting now requires wallet balance**: Craftsmen must have at least 20 RON in wallet to be added to shortlists by clients
- Old shortlists without `charged_at` will need manual migration (set to creation date)

---

## Commits in This Release

1. `feat(deps): add stripe, pywebpush, and requests to requirements`
2. `feat(static): configure Whitenoise for static files serving`
3. `chore: add .gitignore and remove tracked artifacts`
4. `feat(wallet): implement automatic lead fee deduction for shortlist`
5. `test(wallet): add comprehensive tests for wallet and lead fee service`

---

## Next Steps (P1 - Production Quality)

- [ ] Configure CSRF_TRUSTED_ORIGINS for production domain
- [ ] Set up Sentry for error tracking
- [ ] Enable CORS headers if needed for API
- [ ] Add geographic filtering for craftsmen
- [ ] Implement Redis caching
- [ ] Add structured logging
