#!/bin/bash

# Quick Fix for Login Issue - Missing is_active Column
# ====================================================
# This script quickly fixes the login issue by adding the missing is_active column

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

echo "🔧 Quick Fix for Login Issue"
echo "============================"
echo ""

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    print_error "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "❌ Error: Virtual environment not found"
    print_warning "💡 Please create a virtual environment first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    print_error "❌ Error: DATABASE_URL environment variable not set"
    print_warning "💡 Please set the DATABASE_URL environment variable"
    exit 1
fi

print_status "🔧 Activating virtual environment..."
source venv/bin/activate

print_status "🔧 Running quick fix..."
python quick_fix_is_active.py

# Check the exit code
if [ $? -eq 0 ]; then
    print_success "✅ Quick fix completed successfully!"
    print_success "🔄 Users should now be able to log in successfully."
    echo ""
    print_warning "💡 If you're still experiencing issues:"
    echo "   1. Restart your application"
    echo "   2. Try logging in again"
    echo "   3. Check the application logs for any new errors"
else
    print_error "❌ Quick fix failed!"
    print_warning "💡 Please check the error messages above and try again."
    exit 1
fi

echo ""
print_success "🎉 Fix completed! The login functionality should now work properly."
