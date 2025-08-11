#!/usr/bin/env python3
"""
Migration script to add verification system to existing databases.
This script adds email and phone verification fields to the users table.
"""

import sqlite3
import os
import sys
from datetime import datetime

def migrate_verification_system():
    """Add verification fields to users table"""
    
    # Get the database path
    db_path = 'ki_wellness.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starting verification system migration...")
        
        # Check if verification fields already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add verification fields if they don't exist
        fields_to_add = [
            ('email_verified', 'BOOLEAN DEFAULT 0'),
            ('phone_verified', 'BOOLEAN DEFAULT 0'),
            ('email_verification_token', 'VARCHAR(255)'),
            ('phone_verification_code', 'VARCHAR(6)'),
            ('phone_verification_expires', 'DATETIME')
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                print(f"➕ Adding {field_name} field...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
            else:
                print(f"ℹ️  Field {field_name} already exists")
        
        # Add unique constraints after adding columns
        try:
            print("🔒 Adding unique constraint to email_verification_token...")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_token ON users(email_verification_token)")
        except sqlite3.OperationalError as e:
            print(f"⚠️  Warning: Could not add unique constraint to email_verification_token: {e}")
        
        # Update phone field to be unique if it exists
        if 'phone' in columns:
            try:
                print("🔒 Making phone field unique...")
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
            except sqlite3.OperationalError as e:
                if "UNIQUE constraint failed" in str(e):
                    print("⚠️  Warning: Some users have duplicate phone numbers. Please resolve duplicates before making phone field unique.")
                else:
                    print(f"⚠️  Warning: Could not make phone field unique: {e}")
        
        # Set existing users as email verified (since they've already been using the system)
        print("✅ Marking existing users as email verified...")
        cursor.execute("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL")
        
        # Set admin users as fully verified
        print("✅ Marking admin users as fully verified...")
        cursor.execute("UPDATE users SET email_verified = 1, phone_verified = 1 WHERE is_admin = 1")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(users)")
        final_columns = [column[1] for column in cursor.fetchall()]
        
        print("\n✅ Verification system migration completed successfully!")
        print(f"📊 Users table now has {len(final_columns)} columns")
        
        # Show verification status for existing users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE email_verified = 1")
        email_verified = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE phone_verified = 1")
        phone_verified = cursor.fetchone()[0]
        
        print(f"\n📈 Verification Status:")
        print(f"   Total Users: {total_users}")
        print(f"   Email Verified: {email_verified}")
        print(f"   Phone Verified: {phone_verified}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Verification System Migration Script")
    print("=" * 50)
    
    success = migrate_verification_system()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("Users can now verify their email and phone numbers to access AI features.")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)
