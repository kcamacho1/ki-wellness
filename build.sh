#!/usr/bin/env bash
# Build script for Render deployment

echo "🚀 Starting Ki Wellness deployment..."

# Check Python version
echo "🐍 Checking Python version..."
python --version

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
python migrate_add_payment_sessions.py

# Initialize app settings
echo "⚙️ Initializing app settings..."
python -c "
from app import app, initialize_app_settings, create_admin_user
with app.app_context():
    initialize_app_settings()
    create_admin_user()
    print('✅ App settings initialized')
"

echo "✅ Build completed successfully!"
