# Bricli - Production Deployment Guide

**Last Updated:** 20 Octombrie 2025
**Target Environment:** Ubuntu 22.04 LTS / Debian-based Linux
**Database:** PostgreSQL 14+
**Python:** 3.11+

---

## 📋 Pre-Deployment Checklist

### ✅ Local Development Complete
- [x] All tests passing (213 tests)
- [x] Django check: 0 issues
- [x] `.env` configuration implemented
- [x] Static files working (Whitenoise)
- [x] Git repository clean

### ⏳ Server Prerequisites
- [ ] Ubuntu 22.04 LTS server with root access
- [ ] Domain name configured (bricli.ro)
- [ ] SSL certificate ready (Let's Encrypt)
- [ ] Email SMTP credentials (Gmail/SendGrid)
- [ ] Minimum 2GB RAM, 20GB disk

---

## 🚀 Part 1: Server Setup

### Step 1: Update System & Install Dependencies

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and essentials
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install -y build-essential libpq-dev nginx git curl

# Install PostgreSQL 14+
sudo apt install -y postgresql postgresql-contrib

# Verify installations
python3.11 --version  # Should show 3.11+
psql --version        # Should show PostgreSQL 14+
nginx -v              # Nginx version
```

---

### Step 2: Create PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Inside PostgreSQL shell, create database and user:
CREATE DATABASE bricli;
CREATE USER bricli_user WITH PASSWORD 'your_strong_password_here';

-- Grant privileges
ALTER ROLE bricli_user SET client_encoding TO 'utf8';
ALTER ROLE bricli_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE bricli_user SET timezone TO 'Europe/Bucharest';
GRANT ALL PRIVILEGES ON DATABASE bricli TO bricli_user;

-- Grant schema permissions (PostgreSQL 15+)
\c bricli
GRANT ALL ON SCHEMA public TO bricli_user;

-- Exit PostgreSQL shell
\q
```

**Security:** Change `your_strong_password_here` to a strong password (20+ chars, random).

---

### Step 3: Create Application User & Directory

```bash
# Create dedicated user for the app (no sudo access)
sudo useradd -m -s /bin/bash bricli
sudo passwd bricli  # Set password

# Create application directory
sudo mkdir -p /var/www/bricli
sudo chown bricli:bricli /var/www/bricli

# Switch to bricli user
sudo su - bricli
```

---

### Step 4: Clone Repository & Setup Virtual Environment

```bash
# As bricli user, navigate to app directory
cd /var/www/bricli

# Clone repository (use HTTPS or SSH)
git clone https://github.com/your-username/bricli.git .
# OR if using SSH:
# git clone git@github.com:your-username/bricli.git .

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

---

### Step 5: Create Production `.env` File

```bash
# As bricli user, create .env file
nano /var/www/bricli/.env
```

**Contents of `/var/www/bricli/.env`:**

```env
# ==============================================================================
# Bricli - Production Environment Variables
# ==============================================================================

# ------------------------------------------------------------------------------
# Django Core Settings
# ------------------------------------------------------------------------------

# SECURITY: Generate new secret key on server
# Run: python3 -c "import secrets; print(secrets.token_urlsafe(50))"
SECRET_KEY=<GENERATE_NEW_SECRET_KEY_ON_SERVER>

# Production mode
DEBUG=False

# Your actual domain(s)
ALLOWED_HOSTS=bricli.ro,www.bricli.ro

# HTTPS only in production
CSRF_TRUSTED_ORIGINS=https://bricli.ro,https://www.bricli.ro

# ------------------------------------------------------------------------------
# Database Configuration (PostgreSQL)
# ------------------------------------------------------------------------------

DATABASE_URL=postgresql://bricli_user:your_strong_password_here@localhost:5432/bricli

# ------------------------------------------------------------------------------
# Email Configuration (Production SMTP)
# ------------------------------------------------------------------------------

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@bricli.ro
EMAIL_HOST_PASSWORD=<your_gmail_app_password>
DEFAULT_FROM_EMAIL=Bricli <noreply@bricli.ro>

# ------------------------------------------------------------------------------
# Feature Flags
# ------------------------------------------------------------------------------

# Keep False for BETA launch (no payments)
SUBSCRIPTIONS_ENABLED=False

# ------------------------------------------------------------------------------
# Payment Processing (DISABLED for now)
# ------------------------------------------------------------------------------

# Leave as placeholders for now
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

# ------------------------------------------------------------------------------
# Optional: Monitoring (Sentry)
# ------------------------------------------------------------------------------

# SENTRY_DSN=https://your-sentry-dsn-here
```

**Important:**
- Generate new `SECRET_KEY` on server (don't reuse local key)
- Replace `your_strong_password_here` with PostgreSQL password from Step 2
- Configure Gmail App Password or use SendGrid/Mailgun

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

---

### Step 6: Run Database Migrations

```bash
# As bricli user, with venv activated
cd /var/www/bricli
source venv/bin/activate

# Run migrations
python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: accounts, admin, auth, contenttypes, core, messaging, ...
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   ... (many more)
#   No migrations to apply.
```

---

### Step 7: Seed Initial Data (Management Commands)

```bash
# Still as bricli user, with venv activated

# 1. Create service categories (33 categories with icons)
python manage.py populate_categories

# 2. Create county slugs for all Romanian counties
python manage.py populate_county_slugs

# 3. Create subscription tiers (Free/Plus/Pro)
python manage.py seed_tiers

# 4. Migrate existing craftsmen to Free tier (if any)
python manage.py migrate_existing_craftsmen

# 5. Create superuser for admin panel
python manage.py createsuperuser
# Follow prompts to set email and password
```

---

### Step 8: Collect Static Files

```bash
# Collect all static files to STATIC_ROOT
python manage.py collectstatic --noinput

# Expected output:
# 176 static files copied to '/var/www/bricli/staticfiles'
```

---

### Step 9: Test Django Application

```bash
# Run Django development server to test
python manage.py runserver 0.0.0.0:8000

# In another terminal, test with curl:
curl http://localhost:8000/

# Expected: HTML content of homepage
# Press Ctrl+C to stop the server
```

---

## 🌐 Part 2: Gunicorn & Nginx Setup

### Step 10: Configure Gunicorn (WSGI Server)

```bash
# As bricli user, create gunicorn config
nano /var/www/bricli/gunicorn_config.py
```

**Contents of `gunicorn_config.py`:**

```python
"""Gunicorn configuration for Bricli production."""

import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/www/bricli/logs/gunicorn_access.log"
errorlog = "/var/www/bricli/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "bricli"

# Server mechanics
daemon = False
pidfile = "/var/www/bricli/gunicorn.pid"
user = "bricli"
group = "bricli"
tmp_upload_dir = None

# SSL (handled by Nginx, not Gunicorn)
forwarded_allow_ips = "127.0.0.1"
```

**Create logs directory:**

```bash
mkdir -p /var/www/bricli/logs
```

---

### Step 11: Create Systemd Service for Gunicorn

```bash
# Exit bricli user, back to root/sudo user
exit

# Create systemd service file
sudo nano /etc/systemd/system/bricli.service
```

**Contents of `/etc/systemd/system/bricli.service`:**

```ini
[Unit]
Description=Bricli Gunicorn Application
After=network.target postgresql.service

[Service]
Type=notify
User=bricli
Group=bricli
WorkingDirectory=/var/www/bricli
Environment="PATH=/var/www/bricli/venv/bin"
ExecStart=/var/www/bricli/venv/bin/gunicorn \
    --config /var/www/bricli/gunicorn_config.py \
    bricli.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**Enable and start the service:**

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable bricli

# Start the service
sudo systemctl start bricli

# Check status
sudo systemctl status bricli

# Expected output:
# ● bricli.service - Bricli Gunicorn Application
#    Loaded: loaded (/etc/systemd/system/bricli.service; enabled)
#    Active: active (running) since ...
```

**Useful commands:**

```bash
# View logs
sudo journalctl -u bricli -f

# Restart after code changes
sudo systemctl restart bricli

# Stop service
sudo systemctl stop bricli
```

---

### Step 12: Configure Nginx (Reverse Proxy)

```bash
# Create Nginx site configuration
sudo nano /etc/nginx/sites-available/bricli
```

**Contents of `/etc/nginx/sites-available/bricli`:**

```nginx
# Bricli - Nginx Configuration
# HTTP (redirect to HTTPS)
server {
    listen 80;
    listen [::]:80;
    server_name bricli.ro www.bricli.ro;

    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name bricli.ro www.bricli.ro;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/bricli.ro/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bricli.ro/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size (for profile pictures, review images)
    client_max_body_size 10M;

    # Static files (served by Whitenoise via Django)
    location /static/ {
        alias /var/www/bricli/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files (user uploads)
    location /media/ {
        alias /var/www/bricli/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Favicon
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    # robots.txt
    location = /robots.txt {
        access_log off;
        log_not_found off;
    }

    # Logging
    access_log /var/log/nginx/bricli_access.log;
    error_log /var/log/nginx/bricli_error.log;
}
```

**Enable the site:**

```bash
# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/bricli /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Expected output:
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# Reload Nginx
sudo systemctl reload nginx
```

---

### Step 13: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d bricli.ro -d www.bricli.ro

# Follow prompts:
# - Enter email address
# - Agree to Terms of Service
# - Choose whether to redirect HTTP to HTTPS (recommended: Yes)

# Test auto-renewal
sudo certbot renew --dry-run

# Certificate will auto-renew via cron job
```

---

## 🔒 Part 3: Security & Monitoring

### Step 14: Configure Firewall (UFW)

```bash
# Enable UFW firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Check status
sudo ufw status

# Expected output:
# Status: active
# To                         Action      From
# --                         ------      ----
# OpenSSH                    ALLOW       Anywhere
# Nginx Full                 ALLOW       Anywhere
```

---

### Step 15: Setup Automatic Backups

```bash
# Create backup script
sudo nano /usr/local/bin/backup_bricli.sh
```

**Contents of `/usr/local/bin/backup_bricli.sh`:**

```bash
#!/bin/bash
# Bricli - Automated Backup Script

BACKUP_DIR="/var/backups/bricli"
DATE=$(date +"%Y%m%d_%H%M%S")
DB_NAME="bricli"
DB_USER="bricli_user"

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL database
PGPASSWORD="your_strong_password_here" pg_dump -U "$DB_USER" -h localhost "$DB_NAME" > "$BACKUP_DIR/bricli_db_$DATE.sql"

# Backup media files
tar -czf "$BACKUP_DIR/bricli_media_$DATE.tar.gz" -C /var/www/bricli media/

# Delete backups older than 30 days
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Make executable and setup cron:**

```bash
# Make script executable
sudo chmod +x /usr/local/bin/backup_bricli.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e

# Add this line:
0 2 * * * /usr/local/bin/backup_bricli.sh >> /var/log/bricli_backup.log 2>&1
```

---

### Step 16: Final Deployment Checks

```bash
# 1. Django deployment check
sudo -u bricli bash -c "cd /var/www/bricli && source venv/bin/activate && python manage.py check --deploy"

# Expected: 0 CRITICAL/WARNING issues

# 2. Test website
curl -I https://bricli.ro/

# Expected: HTTP/2 200 OK

# 3. Check all services are running
sudo systemctl status bricli
sudo systemctl status nginx
sudo systemctl status postgresql

# 4. Check logs for errors
sudo journalctl -u bricli -n 50
sudo tail -f /var/log/nginx/bricli_error.log
```

---

## 📊 Part 4: Post-Deployment Tasks

### Create Initial Content

1. **Login to Admin Panel:**
   - URL: `https://bricli.ro/admin/`
   - Use superuser credentials from Step 7

2. **Verify Categories:**
   - Navigate to: Services → Service Categories
   - Should see 33 categories with icons

3. **Test User Registration:**
   - Register as client
   - Register as craftsman
   - Verify email notifications

4. **Test Order Flow:**
   - Create order as client
   - Shortlist as craftsman
   - Post review

---

### Monitoring Checklist

- [ ] Setup Sentry for error tracking (optional)
- [ ] Configure uptime monitoring (UptimeRobot, Pingdom)
- [ ] Setup log rotation for Nginx/Gunicorn
- [ ] Monitor disk space: `df -h`
- [ ] Monitor database size: `sudo -u postgres psql -c "\l+"`

---

## 🆘 Troubleshooting

### Issue: 502 Bad Gateway

```bash
# Check Gunicorn is running
sudo systemctl status bricli

# Check Gunicorn logs
sudo journalctl -u bricli -n 100

# Check Nginx error log
sudo tail -f /var/log/nginx/bricli_error.log

# Restart services
sudo systemctl restart bricli
sudo systemctl restart nginx
```

### Issue: Static files not loading

```bash
# Re-collect static files
sudo -u bricli bash -c "cd /var/www/bricli && source venv/bin/activate && python manage.py collectstatic --noinput"

# Check Nginx serves static files
curl -I https://bricli.ro/static/css/custom.css
```

### Issue: Database connection error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d bricli -U bricli_user -h localhost

# Check DATABASE_URL in .env
cat /var/www/bricli/.env | grep DATABASE_URL
```

---

## 📝 Maintenance Tasks

### Update Code (Deploy New Version)

```bash
# 1. Switch to bricli user
sudo su - bricli
cd /var/www/bricli

# 2. Activate virtual environment
source venv/bin/activate

# 3. Pull latest code
git pull origin main

# 4. Install new dependencies (if any)
pip install -r requirements.txt

# 5. Run new migrations (if any)
python manage.py migrate

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Exit bricli user
exit

# 8. Restart Gunicorn
sudo systemctl restart bricli

# 9. Clear browser cache and test
```

### Database Maintenance

```bash
# Vacuum database (monthly)
sudo -u postgres psql -d bricli -c "VACUUM ANALYZE;"

# Check database size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('bricli'));"
```

---

## ✅ Deployment Complete!

Your Bricli application is now live at: **https://bricli.ro**

### Next Steps:
1. Monitor logs for first 48 hours
2. Test all critical user flows
3. Collect user feedback
4. Setup weekly backups verification
5. Plan feature releases

---

**Questions or Issues?**
- Check logs: `/var/log/nginx/` and `sudo journalctl -u bricli`
- Review Django docs: https://docs.djangoproject.com/en/5.2/howto/deployment/
- PostgreSQL docs: https://www.postgresql.org/docs/

**Last updated:** 20 Octombrie 2025
