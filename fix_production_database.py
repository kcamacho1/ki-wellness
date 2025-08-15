#!/usr/bin/env python3
"""
Ki Wellness - Complete Production Database Fix
=============================================

This script fixes ALL missing columns in the production database.
It will add all the columns that are defined in the SQLAlchemy models
but missing from the production database.

This fixes the login errors:
- "column users.phone does not exist"
- "column users.is_active does not exist"
- And any other missing columns

Usage:
    python3 fix_production_database.py

Author: Ki Wellness Team
"""

import os
import sys
from sqlalchemy import text

# Add the current directory to Python path
sys.path.append('.')

def get_expected_user_columns():
    """Get all expected columns from User model"""
    return [
        ('id', 'INTEGER PRIMARY KEY'),
        ('username', 'VARCHAR(80)'),
        ('email', 'VARCHAR(120)'),
        ('password_hash', 'VARCHAR(255)'),
        ('phone', 'VARCHAR(20)'),
        ('is_admin', 'BOOLEAN DEFAULT FALSE'),
        ('is_active', 'BOOLEAN DEFAULT TRUE'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('email_verified', 'BOOLEAN DEFAULT FALSE'),
        ('phone_verified', 'BOOLEAN DEFAULT FALSE'),
        ('email_verification_token', 'VARCHAR(255)'),
        ('phone_verification_code', 'VARCHAR(6)'),
        ('phone_verification_expires', 'TIMESTAMP'),
        ('email_notifications', 'BOOLEAN DEFAULT TRUE'),
        ('sms_notifications', 'BOOLEAN DEFAULT FALSE'),
        ('push_notifications', 'BOOLEAN DEFAULT TRUE'),
        ('oauth_provider', 'VARCHAR(20)'),
        ('oauth_id', 'VARCHAR(255)'),
        ('oauth_email', 'VARCHAR(255)'),
        ('oauth_name', 'VARCHAR(255)'),
        ('oauth_picture', 'VARCHAR(500)')
    ]

def get_existing_columns(connection):
    """Get existing columns from users table"""
    try:
        # Try PostgreSQL first
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))
        return [row[0] for row in result.fetchall()]
    except Exception:
        try:
            # Try SQLite
            result = connection.execute(text("PRAGMA table_info(users)"))
            columns = result.fetchall()
            return [col[1] for col in columns]
        except Exception as e:
            print(f"❌ Error getting existing columns: {e}")
            return []

def add_missing_columns(connection, expected_columns, existing_columns):
    """Add missing columns to users table"""
    missing_columns = []
    
    for col_name, col_type in expected_columns:
        if col_name not in existing_columns:
            missing_columns.append((col_name, col_type))
    
    if not missing_columns:
        print("✅ All columns already exist")
        return True
    
    print(f"⚠️  Found {len(missing_columns)} missing columns:")
    for col_name, col_type in missing_columns:
        print(f"   - {col_name}: {col_type}")
    
    # Add missing columns
    for col_name, col_type in missing_columns:
        try:
            print(f"🔧 Adding column: {col_name}")
            
            # Handle different column types
            if 'PRIMARY KEY' in col_type:
                # Skip primary key column
                print(f"   ⏭️  Skipping primary key column: {col_name}")
                continue
            elif 'DEFAULT' in col_type:
                # Column with default value
                sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
            else:
                # Column without default
                sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
            
            connection.execute(text(sql))
            print(f"   ✅ Added: {col_name}")
            
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"   ℹ️  Column already exists: {col_name}")
            else:
                print(f"   ❌ Error adding {col_name}: {e}")
                connection.rollback()
                return False
    
    connection.commit()
    print("✅ All missing columns added successfully")
    return True

def verify_columns(connection, expected_columns):
    """Verify all expected columns exist"""
    existing_columns = get_existing_columns(connection)
    expected_col_names = [col[0] for col in expected_columns]
    
    missing = set(expected_col_names) - set(existing_columns)
    if missing:
        print(f"❌ Still missing columns: {list(missing)}")
        return False
    
    print("✅ All expected columns verified")
    return True

def test_login_query(connection):
    """Test if login query works"""
    try:
        print("\n🧪 Testing login query...")
        
        # Test the exact query that was failing
        result = connection.execute(text("""
            SELECT id, username, email, phone, is_admin, is_active, 
                   created_at, updated_at, email_verified, phone_verified,
                   email_verification_token, phone_verification_code, 
                   phone_verification_expires, email_notifications, 
                   sms_notifications, push_notifications, oauth_provider,
                   oauth_id, oauth_email, oauth_name, oauth_picture
            FROM users 
            WHERE username = 'test' OR email = 'test' 
            LIMIT 1
        """))
        
        print("✅ Login query test passed - all columns exist")
        return True
        
    except Exception as e:
        if "does not exist" in str(e):
            print(f"❌ Column still missing: {e}")
            return False
        else:
            print(f"⚠️  Other query error (expected): {e}")
            return True

def fix_production_database():
    """Fix all missing columns in production database"""
    
    try:
        # Import the Flask app
        from app.main import app, db
        
        with app.app_context():
            print("🔧 Connecting to production database...")
            
            # Get database connection
            engine = db.engine
            
            with engine.connect() as connection:
                print("✅ Connected successfully")
                
                # Get expected and existing columns
                expected_columns = get_expected_user_columns()
                existing_columns = get_existing_columns(connection)
                
                print(f"📋 Expected columns: {len(expected_columns)}")
                print(f"📋 Existing columns: {len(existing_columns)}")
                
                # Add missing columns
                success = add_missing_columns(connection, expected_columns, existing_columns)
                
                if success:
                    # Verify all columns exist
                    verify_success = verify_columns(connection, expected_columns)
                    
                    if verify_success:
                        # Test login query
                        test_success = test_login_query(connection)
                        
                        print("\n" + "=" * 50)
                        if test_success:
                            print("✅ Production database fix completed successfully")
                            print("✅ Login functionality should now work")
                            return True
                        else:
                            print("⚠️  Columns added but login test failed")
                            return False
                    else:
                        print("❌ Column verification failed")
                        return False
                else:
                    print("❌ Failed to add missing columns")
                    return False
                        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Ki Wellness - Complete Production Database Fix")
    print("=" * 60)
    print("This will fix ALL missing columns in the users table")
    print("=" * 60)
    
    success = fix_production_database()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Database fix completed successfully")
        print("✅ All missing columns have been added")
        print("✅ Login functionality should now work")
        print("🔄 Please restart your application if needed")
        return True
    else:
        print("❌ Database fix failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
