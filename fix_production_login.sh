#!/bin/bash

# Ki Wellness - Production Login Fix
# ==================================
# This script fixes the missing phone column issue in production
# Run this on your production server to fix the login error immediately

echo "🚀 Ki Wellness - Production Login Fix"
echo "======================================"

# Check if we're in a Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Check if SQLAlchemy is available
if ! python3 -c "import sqlalchemy" 2>/dev/null; then
    echo "❌ SQLAlchemy not installed"
    exit 1
fi

# Create a temporary Python script to fix the issue
cat > /tmp/fix_phone_column.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
from sqlalchemy import text, create_engine
from sqlalchemy.exc import ProgrammingError

def fix_phone_column():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found")
        return False
    
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        print("🔧 Connecting to database...")
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            print("✅ Connected successfully")
            
            # Check if column exists
            result = connection.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'phone'
            """))
            
            if result.fetchone():
                print("✅ Phone column already exists")
                return True
            
            print("⚠️  Adding phone column...")
            connection.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
            connection.commit()
            print("✅ Phone column added successfully")
            return True
            
    except Exception as e:
        if "already exists" in str(e).lower():
            print("✅ Phone column already exists")
            return True
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_phone_column()
    sys.exit(0 if success else 1)
EOF

# Run the fix script
echo "🔧 Running phone column fix..."
python3 /tmp/fix_phone_column.py

# Clean up
rm -f /tmp/fix_phone_column.py

echo "✅ Fix completed"
echo "🔄 Please restart your application if needed"
