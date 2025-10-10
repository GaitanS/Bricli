# Bricli - Development Makefile
# Provides convenient commands for common Django development tasks
#
# Usage: make <target>
# Example: make run
#
# Requirements:
# - Windows: Use Git Bash, WSL, or install make for Windows
# - Python 3.13+ installed
# - Virtual environment in ./venv/

.PHONY: help init migrate seed run test test-verbose test-coverage lint fmt check deploy-check clean superuser

# Default target - show help
help:
	@echo "Bricli Development Commands"
	@echo "============================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make init          - Create venv, install deps, setup .env, run migrations"
	@echo "  make migrate       - Run Django migrations"
	@echo "  make seed          - Load demo data (TODO: create fixtures)"
	@echo "  make superuser     - Create admin superuser interactively"
	@echo ""
	@echo "Development Commands:"
	@echo "  make run           - Start development server (0.0.0.0:8000)"
	@echo "  make test          - Run pytest test suite"
	@echo "  make test-verbose  - Run pytest with verbose output"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run linter (flake8/ruff)"
	@echo "  make fmt           - Format code (black/ruff format)"
	@echo "  make check         - Run Django system check"
	@echo "  make deploy-check  - Run Django deployment security check"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Remove Python cache, test artifacts"
	@echo "  make collectstatic - Collect static files (for production)"
	@echo ""

# ============================================================================
# Setup Commands
# ============================================================================

init:
	@echo "🚀 Initializing Bricli development environment..."
	@# Create virtual environment
	@if [ ! -d "venv" ]; then \
		echo "📦 Creating virtual environment..."; \
		python -m venv venv; \
	else \
		echo "✅ Virtual environment already exists"; \
	fi
	@# Install dependencies
	@echo "📥 Installing dependencies..."
	@./venv/Scripts/python.exe -m pip install --upgrade pip
	@./venv/Scripts/python.exe -m pip install -r requirements.txt
	@# Create .env if not exists
	@if [ ! -f ".env" ]; then \
		echo "📝 Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env with your configuration"; \
	else \
		echo "✅ .env already exists"; \
	fi
	@# Run migrations
	@echo "🗄️  Running migrations..."
	@./venv/Scripts/python.exe manage.py migrate
	@echo ""
	@echo "✅ Initialization complete!"
	@echo "Next steps:"
	@echo "  1. Edit .env with your settings"
	@echo "  2. make superuser (create admin account)"
	@echo "  3. make run (start development server)"

migrate:
	@echo "🗄️  Running Django migrations..."
	@./venv/Scripts/python.exe manage.py migrate

seed:
	@echo "🌱 Loading demo data..."
	@echo "⚠️  TODO: Create fixtures with demo users/orders"
	@echo "For now, use Django admin to create test data"

superuser:
	@echo "👤 Creating superuser account..."
	@./venv/Scripts/python.exe manage.py createsuperuser

# ============================================================================
# Development Commands
# ============================================================================

run:
	@echo "🚀 Starting Django development server..."
	@echo "📍 Server will be available at: http://localhost:8000"
	@echo "📍 Admin panel: http://localhost:8000/admin"
	@echo ""
	@./venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000

test:
	@echo "🧪 Running test suite..."
	@./venv/Scripts/python.exe -m pytest

test-verbose:
	@echo "🧪 Running test suite (verbose)..."
	@./venv/Scripts/python.exe -m pytest -v

test-coverage:
	@echo "🧪 Running test suite with coverage..."
	@./venv/Scripts/python.exe -m pytest --cov=. --cov-report=html --cov-report=term
	@echo ""
	@echo "📊 Coverage report generated in htmlcov/index.html"

# ============================================================================
# Code Quality
# ============================================================================

lint:
	@echo "🔍 Running linter..."
	@if command -v ruff > /dev/null; then \
		ruff check .; \
	elif command -v flake8 > /dev/null; then \
		./venv/Scripts/python.exe -m flake8 . --max-line-length=120 --exclude=venv,migrations,staticfiles,media; \
	else \
		echo "⚠️  No linter found. Install with: pip install ruff"; \
	fi

fmt:
	@echo "🎨 Formatting code..."
	@if command -v ruff > /dev/null; then \
		ruff format .; \
	elif command -v black > /dev/null; then \
		./venv/Scripts/python.exe -m black . --exclude="/(venv|migrations|staticfiles|media)/"; \
	else \
		echo "⚠️  No formatter found. Install with: pip install black"; \
	fi

check:
	@echo "✅ Running Django system check..."
	@./venv/Scripts/python.exe manage.py check

deploy-check:
	@echo "🔐 Running Django deployment security check..."
	@./venv/Scripts/python.exe manage.py check --deploy

# ============================================================================
# Maintenance
# ============================================================================

clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true
	@echo "✅ Cleanup complete"

collectstatic:
	@echo "📦 Collecting static files..."
	@./venv/Scripts/python.exe manage.py collectstatic --noinput
	@echo "✅ Static files collected to staticfiles/"

# ============================================================================
# Translation Commands (i18n)
# ============================================================================

makemessages:
	@echo "🌍 Extracting translatable strings..."
	@./venv/Scripts/python.exe manage.py makemessages -l en
	@echo "✅ Translation files updated in locale/"

compilemessages:
	@echo "🌍 Compiling translation files..."
	@./venv/Scripts/python.exe manage.py compilemessages
	@echo "✅ Translation files compiled"
