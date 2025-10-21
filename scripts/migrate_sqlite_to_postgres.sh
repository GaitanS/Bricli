#!/bin/bash
# ==============================================================================
# Bricli - SQLite to PostgreSQL Migration Script
# ==============================================================================
# This script migrates data from SQLite (development) to PostgreSQL (production)
#
# USAGE:
#   1. Ensure PostgreSQL database is created and configured in .env
#   2. Run: bash scripts/migrate_sqlite_to_postgres.sh
#
# PREREQUISITES:
#   - PostgreSQL database created
#   - DATABASE_URL configured in .env
#   - Virtual environment activated
#   - Both SQLite and PostgreSQL connectors installed
# ==============================================================================

set -e  # Exit on error

echo "=========================================="
echo "Bricli: SQLite → PostgreSQL Migration"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "manage.py" ]; then
    echo -e "${RED}ERROR: Please run this script from the project root directory${NC}"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}WARNING: Virtual environment not activated${NC}"
    echo "Attempting to activate..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}ERROR: Virtual environment not found${NC}"
        exit 1
    fi
fi

# Backup existing SQLite database
echo -e "${YELLOW}Step 1: Backing up SQLite database...${NC}"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 "$BACKUP_DIR/db.sqlite3.backup"
    echo -e "${GREEN}✓ SQLite backup created: $BACKUP_DIR/db.sqlite3.backup${NC}"
else
    echo -e "${RED}ERROR: db.sqlite3 not found${NC}"
    exit 1
fi

# Export data from SQLite using Django's dumpdata
echo ""
echo -e "${YELLOW}Step 2: Exporting data from SQLite...${NC}"
python manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --exclude contenttypes \
    --exclude auth.permission \
    --indent 2 \
    > "$BACKUP_DIR/data_export.json"

echo -e "${GREEN}✓ Data exported to: $BACKUP_DIR/data_export.json${NC}"

# Check if .env has DATABASE_URL configured
echo ""
echo -e "${YELLOW}Step 3: Checking PostgreSQL configuration...${NC}"
if grep -q "^DATABASE_URL=postgresql://" .env 2>/dev/null; then
    echo -e "${GREEN}✓ PostgreSQL DATABASE_URL found in .env${NC}"
else
    echo -e "${RED}ERROR: PostgreSQL DATABASE_URL not configured in .env${NC}"
    echo "Please add: DATABASE_URL=postgresql://user:password@localhost:5432/bricli"
    exit 1
fi

# Test PostgreSQL connection
echo ""
echo -e "${YELLOW}Step 4: Testing PostgreSQL connection...${NC}"
python manage.py check --database default || {
    echo -e "${RED}ERROR: Cannot connect to PostgreSQL${NC}"
    echo "Please verify DATABASE_URL credentials and that PostgreSQL is running"
    exit 1
}
echo -e "${GREEN}✓ PostgreSQL connection successful${NC}"

# Run migrations on PostgreSQL
echo ""
echo -e "${YELLOW}Step 5: Running migrations on PostgreSQL...${NC}"
python manage.py migrate --run-syncdb

echo -e "${GREEN}✓ Migrations applied${NC}"

# Import data into PostgreSQL
echo ""
echo -e "${YELLOW}Step 6: Importing data into PostgreSQL...${NC}"
echo "This may take a few minutes..."

python manage.py loaddata "$BACKUP_DIR/data_export.json" || {
    echo -e "${RED}ERROR: Data import failed${NC}"
    echo "Rolling back... Please check error messages above"
    exit 1
}

echo -e "${GREEN}✓ Data imported successfully${NC}"

# Verify data integrity
echo ""
echo -e "${YELLOW}Step 7: Verifying data integrity...${NC}"

# Count records in key models
echo "Checking record counts..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
from services.models import Service, Order, Review
from accounts.models import CraftsmanProfile

User = get_user_model()

print(f'Users: {User.objects.count()}')
print(f'Craftsmen: {CraftsmanProfile.objects.count()}')
print(f'Services: {Service.objects.count()}')
print(f'Orders: {Order.objects.count()}')
print(f'Reviews: {Review.objects.count()}')
"

echo -e "${GREEN}✓ Data integrity check complete${NC}"

# Update sequences (PostgreSQL-specific)
echo ""
echo -e "${YELLOW}Step 8: Updating PostgreSQL sequences...${NC}"
python manage.py shell -c "
from django.core.management import call_command
from django.db import connection

# Reset all sequences to current max ID
with connection.cursor() as cursor:
    cursor.execute('''
        SELECT setval(pg_get_serial_sequence(table_name, column_name),
               COALESCE(MAX(column_name::integer), 1))
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_default LIKE 'nextval%'
    ''')
print('Sequences updated')
"

echo -e "${GREEN}✓ Sequences updated${NC}"

# Final summary
echo ""
echo "=========================================="
echo -e "${GREEN}Migration Complete!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - SQLite backup: $BACKUP_DIR/db.sqlite3.backup"
echo "  - Data export: $BACKUP_DIR/data_export.json"
echo "  - PostgreSQL database: Populated and ready"
echo ""
echo "Next steps:"
echo "  1. Test the application with PostgreSQL"
echo "  2. Verify all functionality works correctly"
echo "  3. Run: python manage.py check --deploy"
echo "  4. If successful, you can remove DATABASE_URL from .env to use SQLite locally"
echo ""
echo -e "${YELLOW}IMPORTANT: Keep the backup in $BACKUP_DIR safe!${NC}"
echo ""
