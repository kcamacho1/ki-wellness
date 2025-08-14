#!/usr/bin/env python3
"""
Ki Wellness - Fix Missing Phone Column Migration
===============================================

This script adds the missing 'phone' column to the users table
in the production database.

Usage:
    python cleanup_backup/fix_missing_phone_column.py

Author: Ki Wellness Team
"""

import os
import sys
from sqlalchemy import text, inspect
from sqlalchemy.exc import ProgrammingError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_and_fix_phone_column():
    """Check if phone column exists and add it if missing"""
    
    try:
        # Import Flask app and database
        from app.main import app, db
        
        with app.app_context():
            print("🔍 Checking database schema...")
            
            # Get database connection
            engine = db.engine
            
            # Check if phone column exists
            inspector = inspect(engine)
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            
            print(f"📋 Current columns in users table: {column_names}")
            
            if 'phone' in column_names:
                print("✅ Phone column already exists - no action needed")
                return True
            
            print("⚠️  Phone column missing - adding it now...")
            
            # Add the phone column
            with engine.connect() as connection:
                # Add phone column with same specifications as in the model
                alter_sql = text("""
                    ALTER TABLE users 
                    ADD COLUMN phone VARCHAR(20)
                """)
                
                connection.execute(alter_sql)
                connection.commit()
                
                print("✅ Phone column added successfully")
                
                # Verify the column was added
                inspector = inspect(engine)
                columns = inspector.get_columns('users')
                column_names = [col['name'] for col in columns]
                
                if 'phone' in column_names:
                    print("✅ Verification: Phone column confirmed in table")
                    return True
                else:
                    print("❌ Verification failed: Phone column not found after addition")
                    return False
                    
    except ProgrammingError as e:
        if "column users.phone does not exist" in str(e):
            print("❌ Phone column still missing after migration attempt")
            return False
        else:
            print(f"❌ Database error: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Ki Wellness - Phone Column Migration")
    print("=" * 50)
    
    success = check_and_fix_phone_column()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Migration completed successfully")
        return True
    else:
        print("❌ Migration failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
