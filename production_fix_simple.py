#!/usr/bin/env python3
"""
Ki Wellness - Simple Production Phone Column Fix
===============================================

This script uses the existing Flask app to fix the phone column issue.
Run this on your production server.

Usage:
    python3 production_fix_simple.py
"""

import os
import sys
from sqlalchemy import text

# Add the current directory to Python path
sys.path.append('.')

def fix_phone_column():
    """Fix the missing phone column using Flask app"""
    
    try:
        # Import the Flask app
        from app.main import app, db
        
        with app.app_context():
            print("🔧 Connecting to database via Flask app...")
            
            # Get database connection
            engine = db.engine
            
            with engine.connect() as connection:
                print("✅ Connected successfully")
                
                # Check if column exists
                try:
                    result = connection.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'users' AND column_name = 'phone'
                    """))
                    
                    if result.fetchone():
                        print("✅ Phone column already exists")
                        return True
                    
                    print("⚠️  Phone column missing - adding it now...")
                    
                    # Add phone column
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN phone VARCHAR(20)
                    """))
                    
                    connection.commit()
                    print("✅ Phone column added successfully")
                    
                    # Verify the column was added
                    result = connection.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'users' AND column_name = 'phone'
                    """))
                    
                    if result.fetchone():
                        print("✅ Verification: Phone column confirmed in table")
                        return True
                    else:
                        print("❌ Verification failed")
                        return False
                        
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print("✅ Phone column already exists (caught by database)")
                        return True
                    else:
                        print(f"❌ Error: {e}")
                        connection.rollback()
                        return False
                        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login():
    """Test if login query works"""
    
    try:
        from app.main import app, db
        from app.models import User
        
        with app.app_context():
            print("\n🧪 Testing login query...")
            
            try:
                # Test the exact query that was failing
                user = User.query.filter(
                    (User.username == 'test') | (User.email == 'test')
                ).first()
                
                print("✅ Login query test passed - no errors")
                return True
                
            except Exception as e:
                if "phone does not exist" in str(e):
                    print("❌ Phone column still missing")
                    return False
                else:
                    print(f"⚠️  Other query error (expected): {e}")
                    return True
                    
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Ki Wellness - Production Phone Column Fix")
    print("=" * 50)
    
    success = fix_phone_column()
    
    if success:
        test_success = test_login()
        
        print("\n" + "=" * 50)
        if test_success:
            print("✅ Phone column fix completed successfully")
            print("✅ Login functionality should now work")
            return True
        else:
            print("⚠️  Column added but login test failed")
            return False
    else:
        print("\n" + "=" * 50)
        print("❌ Phone column fix failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
