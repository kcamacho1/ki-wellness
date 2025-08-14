#!/usr/bin/env python3
"""
Migration script to add phone column to users table
==================================================

This script adds the missing phone column to the users table
to fix the production database schema issue.

Author: Ki Wellness Team
Version: 1.0
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db

def migrate_phone_column():
    """Add phone column to users table if it doesn't exist"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if phone column exists
            result = db.session.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'phone'
            """)
            
            if result.fetchone():
                print("✅ Phone column already exists in users table")
                return True
            
            # Add phone column
            print("🔧 Adding phone column to users table...")
            db.session.execute("""
                ALTER TABLE users 
                ADD COLUMN phone VARCHAR(20)
            """)
            
            # Add index for phone column
            db.session.execute("""
                CREATE INDEX IF NOT EXISTS ix_users_phone 
                ON users (phone)
            """)
            
            db.session.commit()
            print("✅ Phone column added successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error adding phone column: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🔧 Migrating phone column to users table...")
    success = migrate_phone_column()
    
    if success:
        print("✅ Migration completed successfully")
        sys.exit(0)
    else:
        print("❌ Migration failed")
        sys.exit(1)
