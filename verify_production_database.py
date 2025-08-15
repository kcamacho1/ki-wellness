#!/usr/bin/env python3
"""
Production Database Verification Script
This script checks the current state of the production database schema
and identifies any missing columns or tables that need to be fixed.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

def verify_production_database():
    """Verify the production database schema"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    # Convert SQLite URL to PostgreSQL if needed
    if database_url.startswith('sqlite://'):
        print("❌ This script is for PostgreSQL production database")
        return False
    
    print("🔍 Verifying production database schema...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Get inspector
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"📊 Found tables: {existing_tables}")
        
        # Check users table
        if 'users' in existing_tables:
            print("\n👥 Checking users table...")
            user_columns = inspector.get_columns('users')
            user_column_names = [col['name'] for col in user_columns]
            print(f"   Current columns: {user_column_names}")
            
            # Expected columns for users table
            expected_user_columns = [
                'id', 'username', 'email', 'password_hash', 'phone',
                'is_admin', 'is_active', 'created_at', 'updated_at',
                'email_verified', 'phone_verified', 'email_verification_token',
                'phone_verification_code', 'phone_verification_expires',
                'email_notifications', 'sms_notifications', 'push_notifications',
                'oauth_provider', 'oauth_id', 'oauth_email', 'oauth_name', 'oauth_picture'
            ]
            
            missing_user_columns = [col for col in expected_user_columns if col not in user_column_names]
            if missing_user_columns:
                print(f"   ❌ Missing columns: {missing_user_columns}")
            else:
                print("   ✅ All expected columns present")
        else:
            print("❌ users table does not exist")
        
        # Check user_profiles table
        if 'user_profiles' in existing_tables:
            print("\n👤 Checking user_profiles table...")
            profile_columns = inspector.get_columns('user_profiles')
            profile_column_names = [col['name'] for col in profile_columns]
            print(f"   Current columns: {profile_column_names}")
            
            # Expected columns for user_profiles table
            expected_profile_columns = [
                'id', 'user_id', 'name', 'avatar', 'weight_unit',
                'created_at', 'updated_at'
            ]
            
            missing_profile_columns = [col for col in expected_profile_columns if col not in profile_column_names]
            if missing_profile_columns:
                print(f"   ❌ Missing columns: {missing_profile_columns}")
            else:
                print("   ✅ All expected columns present")
        else:
            print("ℹ️  user_profiles table does not exist")
        
        # Check other important tables
        important_tables = ['food_journal', 'mood_entries', 'patterns_cache', 'token_usage']
        for table_name in important_tables:
            if table_name in existing_tables:
                print(f"\n📋 Checking {table_name} table...")
                table_columns = inspector.get_columns(table_name)
                column_names = [col['name'] for col in table_columns]
                print(f"   Columns: {column_names}")
            else:
                print(f"ℹ️  {table_name} table does not exist")
        
        # Test database connection
        print("\n🔗 Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"   ✅ Connected successfully - PostgreSQL version: {version}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False

if __name__ == "__main__":
    success = verify_production_database()
    if success:
        print("\n🎉 Database verification completed!")
        sys.exit(0)
    else:
        print("\n💥 Database verification failed!")
        sys.exit(1)
