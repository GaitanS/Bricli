# Bricli Platform - Production Deployment Guide

## Prerequisites

1. **Server Requirements:**
   - Ubuntu 20.04+ or similar Linux distribution
   - Python 3.9+
   - PostgreSQL 13+
   - Redis 6+
   - Nginx
   - SSL certificate (Let's Encrypt recommended)

2. **Domain Setup:**
   - Domain name pointing to your server
   - DNS configured for www and root domain

## Step-by-Step Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3-pip python3-venv postgresql postgresql-contrib redis-server nginx git -y

# Install Node.js (for frontend assets if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Database Setup

```bash
# Create PostgreSQL database and user
sudo -u postgres psql
CREATE DATABASE bricli_db;
CREATE USER bricli_user WITH PASSWORD 'your_secure_password';
ALTER ROLE bricli_user SET client_encoding TO 'utf8';
ALTER ROLE bricli_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE bricli_user SET timezone TO 'Europe/Bucharest';
GRANT ALL PRIVILEGES ON DATABASE bricli_db TO bricli_user;
\q
```

### 3. Application Setup

```bash
# Create application directory
sudo mkdir -p /var/www/bricli
sudo chown $USER:$USER /var/www/bricli
cd /var/www/bricli

# Clone repository
git clone https://github.com/yourusername/bricli.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Create media and static directories
mkdir -p media staticfiles
```

### 4. Environment Configuration

```bash
# Copy and configure environment file
cp .env.example .env
nano .env

# Configure the following variables:
SECRET_KEY=your-super-secret-django-key-here
DEBUG=False
ALLOWED_HOSTS=bricli.ro,www.bricli.ro
DB_NAME=bricli_db
DB_USER=bricli_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST_USER=noreply@bricli.ro
EMAIL_HOST_PASSWORD=your-email-app-password
```

### 5. Django Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Use production settings
export DJANGO_SETTINGS_MODULE=bricli.production_settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Populate initial data
python manage.py populate_data
```

### 6. Gunicorn Configuration

Create `/etc/systemd/system/bricli.service`:

```ini
[Unit]
Description=Bricli Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/bricli
Environment="DJANGO_SETTINGS_MODULE=bricli.production_settings"
ExecStart=/var/www/bricli/venv/bin/gunicorn --workers 3 --bind unix:/var/www/bricli/bricli.sock bricli.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Set permissions
sudo chown -R www-data:www-data /var/www/bricli

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable bricli
sudo systemctl start bricli
sudo systemctl status bricli
```

### 7. Nginx Configuration

Create `/etc/nginx/sites-available/bricli`:

```nginx
server {
    listen 80;
    server_name bricli.ro www.bricli.ro;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bricli.ro www.bricli.ro;

    ssl_certificate /etc/letsencrypt/live/bricli.ro/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bricli.ro/privkey.pem;

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /var/www/bricli;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        root /var/www/bricli;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/bricli/bricli.sock;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/bricli /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d bricli.ro -d www.bricli.ro

# Test auto-renewal
sudo certbot renew --dry-run
```

### 9. Redis Configuration

```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Set password (uncomment and modify):
# requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 10. Monitoring and Maintenance

```bash
# Create backup script
sudo nano /usr/local/bin/backup-bricli.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/bricli"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U bricli_user -h localhost bricli_db > $BACKUP_DIR/db_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /var/www/bricli media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-bricli.sh

# Add to crontab (daily backup at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-bricli.sh
```

## Post-Deployment Checklist

- [ ] Application loads correctly
- [ ] SSL certificate is working
- [ ] Database connections are working
- [ ] Email sending is functional
- [ ] Static files are served correctly
- [ ] Media uploads work
- [ ] Admin panel is accessible
- [ ] User registration/login works
- [ ] Payment processing works (if enabled)
- [ ] Backups are configured
- [ ] Monitoring is set up

## Troubleshooting

### Common Issues:

1. **Static files not loading:**
   ```bash
   python manage.py collectstatic --noinput
   sudo systemctl restart bricli
   ```

2. **Database connection errors:**
   - Check PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify database credentials in `.env`

3. **Permission errors:**
   ```bash
   sudo chown -R www-data:www-data /var/www/bricli
   sudo chmod -R 755 /var/www/bricli
   ```

4. **Gunicorn not starting:**
   ```bash
   sudo journalctl -u bricli -f
   ```

## Security Recommendations

1. **Firewall Configuration:**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Regular Updates:**
   - Keep system packages updated
   - Update Python dependencies regularly
   - Monitor security advisories

3. **Monitoring:**
   - Set up log monitoring
   - Configure error tracking (Sentry)
   - Monitor server resources

## Support

For deployment support or issues, contact: support@bricli.ro