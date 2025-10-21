# Bricli - Pre-Deployment Checklist

**Last Updated:** 20 Octombrie 2025
**Version:** 1.0 (BETA - No Payments)

Use this checklist to ensure everything is ready before deploying to production.

---

## ✅ Phase 1: Code & Configuration

### Local Development Complete

- [ ] **All tests passing**
  ```bash
  pytest -v
  # Expected: 213 passed
  ```

- [ ] **Django system check clean**
  ```bash
  python manage.py check
  # Expected: System check identified no issues (0 silenced)
  ```

- [ ] **No pending migrations**
  ```bash
  python manage.py makemigrations --check --dry-run
  # Expected: No changes detected
  ```

- [ ] **Git repository clean**
  ```bash
  git status
  # No uncommitted changes (except .env)
  ```

- [ ] **.env.example updated** with all required variables

- [ ] **.gitignore includes .env** (verify `.env` not tracked)

- [ ] **requirements.txt up to date**
  - `psycopg2-binary==2.9.9` uncommented
  - `django-environ==0.12.0` included

---

## ✅ Phase 2: Server Prerequisites

### Server Access & Domain

- [ ] **Server ready**
  - Ubuntu 22.04 LTS (or Debian-based)
  - Minimum 2GB RAM, 20GB disk
  - Root/sudo access configured

- [ ] **Domain configured**
  - DNS A record: `bricli.ro` → Server IP
  - DNS A record: `www.bricli.ro` → Server IP
  - DNS propagated (check with `dig bricli.ro`)

- [ ] **SSL Certificate plan**
  - Let's Encrypt Certbot ready
  - OR existing SSL certificate files

### External Services

- [ ] **Email SMTP credentials**
  - Gmail App Password created
  - OR SendGrid/Mailgun API key
  - Test email send works

- [ ] **Monitoring (Optional)**
  - Sentry account created (optional)
  - UptimeRobot configured (optional)

---

## ✅ Phase 3: Production Environment Variables

Create `/var/www/bricli/.env` on server with:

### Required Variables

- [ ] **SECRET_KEY**
  ```bash
  # Generate new key on server:
  python3 -c "import secrets; print(secrets.token_urlsafe(50))"
  ```

- [ ] **DEBUG=False**
  - CRITICAL: Never set to True in production

- [ ] **ALLOWED_HOSTS**
  ```env
  ALLOWED_HOSTS=bricli.ro,www.bricli.ro
  ```

- [ ] **CSRF_TRUSTED_ORIGINS**
  ```env
  CSRF_TRUSTED_ORIGINS=https://bricli.ro,https://www.bricli.ro
  ```

- [ ] **DATABASE_URL** (PostgreSQL)
  ```env
  DATABASE_URL=postgresql://bricli_user:STRONG_PASSWORD@localhost:5432/bricli
  ```

- [ ] **Email Configuration**
  ```env
  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  EMAIL_HOST=smtp.gmail.com
  EMAIL_PORT=587
  EMAIL_USE_TLS=True
  EMAIL_HOST_USER=noreply@bricli.ro
  EMAIL_HOST_PASSWORD=<gmail_app_password>
  DEFAULT_FROM_EMAIL=Bricli <noreply@bricli.ro>
  ```

- [ ] **SUBSCRIPTIONS_ENABLED=False**
  - Keep False for BETA launch (no payments)

### Optional Variables

- [ ] **SENTRY_DSN** (if using Sentry)
- [ ] **STRIPE_* keys** (placeholders for now)
- [ ] **SMARTBILL_* credentials** (for future invoicing)

---

## ✅ Phase 4: Database Setup

### PostgreSQL Installation

- [ ] **PostgreSQL 14+ installed**
  ```bash
  sudo apt install postgresql postgresql-contrib
  psql --version  # Verify version
  ```

- [ ] **Database created**
  ```sql
  CREATE DATABASE bricli;
  CREATE USER bricli_user WITH PASSWORD 'strong_password';
  GRANT ALL PRIVILEGES ON DATABASE bricli TO bricli_user;
  ```

- [ ] **Database connection tested**
  ```bash
  psql -U bricli_user -h localhost -d bricli
  # Should connect successfully
  ```

### Data Migration (if migrating from existing SQLite)

- [ ] **SQLite backup created**
  ```bash
  cp db.sqlite3 backups/db.sqlite3.$(date +%Y%m%d).backup
  ```

- [ ] **Data exported from SQLite**
  ```bash
  python manage.py dumpdata > data_export.json
  ```

- [ ] **Migrations run on PostgreSQL**
  ```bash
  python manage.py migrate
  ```

- [ ] **Data imported into PostgreSQL**
  ```bash
  python manage.py loaddata data_export.json
  ```

### Fresh Installation (no data migration)

- [ ] **Migrations applied**
  ```bash
  python manage.py migrate
  ```

- [ ] **Management commands executed** (in order):
  ```bash
  python manage.py populate_categories       # 33 service categories
  python manage.py populate_county_slugs     # Romanian counties
  python manage.py seed_tiers                # Free/Plus/Pro tiers
  python manage.py migrate_existing_craftsmen # Assign Free tier
  ```

- [ ] **Superuser created**
  ```bash
  python manage.py createsuperuser
  # Email: admin@bricli.ro
  # Password: <strong_password>
  ```

---

## ✅ Phase 5: Application Deployment

### Code Deployment

- [ ] **Repository cloned**
  ```bash
  cd /var/www/bricli
  git clone https://github.com/your-username/bricli.git .
  ```

- [ ] **Virtual environment created**
  ```bash
  python3.11 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

- [ ] **Static files collected**
  ```bash
  python manage.py collectstatic --noinput
  # Expected: 176 files copied
  ```

### Gunicorn Setup

- [ ] **Gunicorn config created**
  - File: `/var/www/bricli/gunicorn_config.py`
  - Logs directory created: `/var/www/bricli/logs/`

- [ ] **Systemd service created**
  - File: `/etc/systemd/system/bricli.service`
  - Service enabled: `sudo systemctl enable bricli`
  - Service started: `sudo systemctl start bricli`
  - Service status OK: `sudo systemctl status bricli`

### Nginx Setup

- [ ] **Nginx installed**
  ```bash
  sudo apt install nginx
  ```

- [ ] **Site configuration created**
  - File: `/etc/nginx/sites-available/bricli`
  - Symlink created: `/etc/nginx/sites-enabled/bricli`

- [ ] **Nginx configuration tested**
  ```bash
  sudo nginx -t
  # Expected: syntax is ok
  ```

- [ ] **Nginx reloaded**
  ```bash
  sudo systemctl reload nginx
  ```

### SSL Certificate

- [ ] **Certbot installed**
  ```bash
  sudo apt install certbot python3-certbot-nginx
  ```

- [ ] **SSL certificate obtained**
  ```bash
  sudo certbot --nginx -d bricli.ro -d www.bricli.ro
  ```

- [ ] **Auto-renewal tested**
  ```bash
  sudo certbot renew --dry-run
  # Expected: Congratulations, all renewals succeeded
  ```

---

## ✅ Phase 6: Security & Firewall

### Firewall Configuration

- [ ] **UFW enabled**
  ```bash
  sudo ufw allow OpenSSH
  sudo ufw allow 'Nginx Full'
  sudo ufw enable
  sudo ufw status  # Verify
  ```

### Security Hardening

- [ ] **Fail2ban installed** (optional but recommended)
  ```bash
  sudo apt install fail2ban
  sudo systemctl enable fail2ban
  ```

- [ ] **SSH key-based authentication** enabled
  - Password authentication disabled in `/etc/ssh/sshd_config`

- [ ] **Non-root user created** for deployments
  - User: `bricli`
  - Sudo privileges: NO (security)

---

## ✅ Phase 7: Testing & Verification

### Application Health Checks

- [ ] **Django deployment check**
  ```bash
  python manage.py check --deploy
  # Expected: 0 CRITICAL/WARNING issues
  ```

- [ ] **Website accessible**
  ```bash
  curl -I https://bricli.ro/
  # Expected: HTTP/2 200 OK
  ```

- [ ] **Admin panel accessible**
  - URL: `https://bricli.ro/admin/`
  - Login with superuser credentials
  - Verify categories visible

### Functional Testing

- [ ] **User registration works**
  - Register as client
  - Register as craftsman
  - Email notifications received

- [ ] **Order creation works**
  - Client creates order
  - Order visible in `/servicii/comenzi/`

- [ ] **Craftsman shortlist works**
  - Craftsman can view available orders
  - Shortlist button functional
  - No payment required (BETA mode)

- [ ] **Review system works**
  - Client can post review
  - Images upload successfully
  - Review visible on craftsman profile

- [ ] **Search works**
  - `/cautare/` loads correctly
  - Filters work (county, category, rating)
  - Results display properly

### Performance Checks

- [ ] **Static files load correctly**
  ```bash
  curl -I https://bricli.ro/static/css/custom.css
  # Expected: 200 OK
  ```

- [ ] **Media files accessible**
  ```bash
  curl -I https://bricli.ro/media/
  # Expected: Directory listing or 403 (depends on config)
  ```

- [ ] **Page load time < 2 seconds**
  - Test homepage, search, profiles

---

## ✅ Phase 8: Monitoring & Backups

### Logging

- [ ] **Application logs working**
  ```bash
  sudo journalctl -u bricli -n 50
  # Check for errors
  ```

- [ ] **Nginx logs accessible**
  ```bash
  sudo tail -f /var/log/nginx/bricli_access.log
  sudo tail -f /var/log/nginx/bricli_error.log
  ```

### Backups

- [ ] **Backup script created**
  - File: `/usr/local/bin/backup_bricli.sh`
  - Executable: `chmod +x`

- [ ] **Cron job configured**
  ```bash
  sudo crontab -e
  # Add: 0 2 * * * /usr/local/bin/backup_bricli.sh
  ```

- [ ] **Test backup manually**
  ```bash
  sudo /usr/local/bin/backup_bricli.sh
  # Check /var/backups/bricli/
  ```

### Monitoring (Optional)

- [ ] **Uptime monitoring** (UptimeRobot, Pingdom)
  - Monitor: `https://bricli.ro/`
  - Alert email configured

- [ ] **Error tracking** (Sentry)
  - Sentry DSN added to .env
  - Test error sent successfully

---

## ✅ Phase 9: Documentation & Handoff

### Documentation

- [ ] **DEPLOYMENT_GUIDE.md** reviewed and accurate

- [ ] **Environment variables documented**
  - `.env.example` complete
  - Production `.env` values recorded securely (NOT in Git)

- [ ] **Admin credentials stored securely**
  - Password manager (1Password, LastPass)
  - NOT in repository

### Team Handoff

- [ ] **Server access documented**
  - SSH key location
  - IP address
  - Sudo user credentials

- [ ] **Deployment procedures documented**
  - How to deploy updates
  - How to rollback
  - How to access logs

- [ ] **Emergency contacts**
  - Hosting provider support
  - Domain registrar
  - SSL certificate provider

---

## ✅ Phase 10: Go-Live

### Final Pre-Launch Checks

- [ ] **All above items completed** ✅

- [ ] **Stakeholder approval** received

- [ ] **Launch announcement ready**
  - Social media posts prepared
  - Email notifications scheduled

### Launch Day

- [ ] **Monitor logs actively** for first 4 hours
  ```bash
  sudo journalctl -u bricli -f
  ```

- [ ] **Test from multiple devices**
  - Desktop (Chrome, Firefox, Safari)
  - Mobile (iOS, Android)

- [ ] **Monitor server resources**
  ```bash
  htop  # CPU/RAM usage
  df -h # Disk space
  ```

- [ ] **Respond to user feedback**
  - Have support email ready
  - Monitor admin panel for issues

### Post-Launch (First 48 Hours)

- [ ] **Daily database backups verified**
  ```bash
  ls -lh /var/backups/bricli/
  ```

- [ ] **No critical errors in logs**

- [ ] **Performance metrics acceptable**
  - Page load times < 2s
  - No 500 errors

- [ ] **User feedback collected**

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ **All checklist items complete**
✅ **Website accessible at https://bricli.ro**
✅ **SSL certificate valid (green padlock)**
✅ **Django check --deploy shows 0 issues**
✅ **Users can register, create orders, post reviews**
✅ **No errors in logs for 24 hours**
✅ **Backups running automatically**

---

## 🆘 Rollback Plan

If critical issues arise:

1. **Stop Gunicorn:**
   ```bash
   sudo systemctl stop bricli
   ```

2. **Restore database backup:**
   ```bash
   psql -U bricli_user -d bricli < /var/backups/bricli/latest_backup.sql
   ```

3. **Revert code to previous version:**
   ```bash
   cd /var/www/bricli
   git checkout <previous_commit_hash>
   ```

4. **Restart services:**
   ```bash
   sudo systemctl start bricli
   sudo systemctl reload nginx
   ```

---

## 📞 Support Resources

- **Django Documentation:** https://docs.djangoproject.com/en/5.2/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **Nginx Docs:** https://nginx.org/en/docs/
- **Let's Encrypt:** https://letsencrypt.org/docs/

---

**Good luck with your deployment!** 🚀

**Last updated:** 20 Octombrie 2025
