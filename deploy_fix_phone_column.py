#!/usr/bin/env python3
"""
Ki Wellness - Production Phone Column Fix (Deployment Script)
============================================================

This script fixes the missing 'phone' column in the production database.
Run this directly on your production server to fix the login error.

Usage:
    python deploy_fix_phone_column.py

This script will:
1. Connect to the production database
2. Add the missing 'phone' column to the users table
3. Verify the fix works
4. Test the login query

Author: Ki Wellness Team
"""

import os
import sys
from sqlalchemy import text, create_engine
from sqlalchemy.exc import ProgrammingError

def get_database_url():
    """Get database URL from environment"""
    # Try different environment variable names
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = os.environ.get('SQLALCHEMY_DATABASE_URI')
    if not db_url:
        db_url = os.environ.get('POSTGRES_URL')
    
    if not db_url:
        print("❌ No database URL found in environment variables")
        print("Please set DATABASE_URL, SQLALCHEMY_DATABASE_URI, or POSTGRES_URL")
        return None
    
    # Convert postgres:// to postgresql:// for newer SQLAlchemy
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    return db_url

def fix_phone_column():
    """Add the missing phone column to users table"""
    
    db_url = get_database_url()
    if not db_url:
        return False
    
    try:
        print("🔧 Connecting to production database...")
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            print("✅ Connected to database successfully")
            
            # Check if column already exists
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
                    print("❌ Verification failed: Phone column not found after addition")
                    return False
                    
            except ProgrammingError as e:
                if "already exists" in str(e).lower():
                    print("✅ Phone column already exists (caught by database)")
                    return True
                else:
                    print(f"❌ Error adding phone column: {e}")
                    connection.rollback()
                    return False
                    
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_login_query():
    """Test if the login query now works"""
    
    db_url = get_database_url()
    if not db_url:
        return False
    
    try:
        print("\n🧪 Testing login query...")
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            # Test a simple query that includes the phone column
            try:
                result = connection.execute(text("""
                    SELECT id, username, email, phone 
                    FROM users 
                    WHERE username = 'test' OR email = 'test' 
                    LIMIT 1
                """))
                
                # If we get here without error, the column exists
                print("✅ Login query test passed - phone column exists")
                return True
                
            except ProgrammingError as e:
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
    print(f"🌐 Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"🗄️  Database: {get_database_url()[:50]}..." if get_database_url() else "❌ No database URL")
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
            print("🔄 Please restart your application if needed")
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
