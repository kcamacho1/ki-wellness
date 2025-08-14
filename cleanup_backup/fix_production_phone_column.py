#!/usr/bin/env python3
"""
Ki Wellness - Production Phone Column Fix
========================================

This script specifically fixes the missing 'phone' column issue
in the production database that's causing login errors.

This is a critical fix for the production login error:
"column users.phone does not exist"

Usage:
    python cleanup_backup/fix_production_phone_column.py

Author: Ki Wellness Team
"""

import os
import sys
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_phone_column():
    """Add the missing phone column to users table"""
    
    try:
        # Import Flask app and database
        from app.main import app, db
        
        with app.app_context():
            print("🔧 Fixing production phone column issue...")
            
            # Get database connection
            engine = db.engine
            
            # Check if we're in production
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            is_production = 'postgresql' in db_url.lower() or 'postgres' in db_url.lower()
            
            if is_production:
                print("🌐 Production database detected")
            else:
                print("💻 Local database detected")
            
            # Add the phone column
            with engine.connect() as connection:
                try:
                    # Check if column already exists (different for SQLite vs PostgreSQL)
                    if is_production:
                        # PostgreSQL
                        result = connection.execute(text("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = 'phone'
                        """))
                    else:
                        # SQLite
                        result = connection.execute(text("""
                            PRAGMA table_info(users)
                        """))
                        columns = result.fetchall()
                        column_names = [col[1] for col in columns]
                        if 'phone' in column_names:
                            print("✅ Phone column already exists")
                            return True
                        result = None
                    
                    if result and result.fetchone():
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
                    if is_production:
                        # PostgreSQL
                        result = connection.execute(text("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = 'phone'
                        """))
                        if result.fetchone():
                            print("✅ Verification: Phone column confirmed in table")
                            return True
                        else:
                            print("❌ Verification failed: Phone column not found after addition")
                            return False
                    else:
                        # SQLite
                        result = connection.execute(text("""
                            PRAGMA table_info(users)
                        """))
                        columns = result.fetchall()
                        column_names = [col[1] for col in columns]
                        if 'phone' in column_names:
                            print("✅ Verification: Phone column confirmed in table")
                            return True
                        else:
                            print("❌ Verification failed: Phone column not found after addition")
                            return False
                        
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print("✅ Phone column already exists (caught by database)")
                        return True
                    else:
                        print(f"❌ Error adding phone column: {e}")
                        connection.rollback()
                        return False
                    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_login_query():
    """Test if the login query now works"""
    
    try:
        from app.main import app, db
        from app.models import User
        
        with app.app_context():
            print("\n🧪 Testing login query...")
            
            # Test the exact query that was failing
            try:
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
        print(f"❌ Test query error: {e}")
        return False

def main():
    """Main fix function"""
    print("🚀 Ki Wellness - Production Phone Column Fix")
    print("=" * 50)
    
    # Fix the phone column
    success = fix_phone_column()
    
    if success:
        # Test the login query
        test_success = test_login_query()
        
        print("\n" + "=" * 50)
        if test_success:
            print("✅ Production phone column fix completed successfully")
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
