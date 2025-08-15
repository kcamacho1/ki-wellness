#!/bin/bash

# Fix production login issue - Add missing is_active column
# This script addresses the login error where is_active column doesn't exist

echo "🔧 Fixing production login issue - Adding missing is_active column..."

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "🔧 Checking dependencies..."
python -c "import sqlalchemy" 2>/dev/null || {
    echo "❌ Error: SQLAlchemy not installed. Please run: pip install -r requirements.txt"
    exit 1
}

# Run the fix script
echo "🔧 Running is_active column fix..."
python fix_production_is_active_column.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo "✅ Production login fix completed successfully!"
    echo "🔄 The login functionality should now work properly."
else
    echo "❌ Production login fix failed!"
    echo "🔍 Please check the error messages above and try again."
    exit 1
fi

echo "🎉 Fix completed! Users should now be able to log in successfully."
