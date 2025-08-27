#!/usr/bin/env python3
"""
Migration to add user roles field
Adds role field to user table with values: 'admin', 'user', 'ff'
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_add_user_roles():
    """Add user roles field to the database"""
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Normalize old Heroku-style URLs
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
    else:
        # Development - SQLite fallback
        db_url = 'sqlite:///ki_wellness.db'
    
    print(f"Connecting to database: {db_url}")
    
    try:
        # Create engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Check if role column already exists
            if db_url.startswith('sqlite'):
                # SQLite
                result = conn.execute(text("PRAGMA table_info(user)"))
                existing_columns = [row[1] for row in result.fetchall()]
                
                if 'role' not in existing_columns:
                    conn.execute(text('ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT "user"'))
                    print("✓ Added role column to user table")
                else:
                    print("✓ Role column already exists")
            else:
                # PostgreSQL
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user' AND column_name = 'role'
                """))
                
                if not result.fetchone():
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN role VARCHAR(20) DEFAULT \'user\''))
                    print("✓ Added role column to user table")
                else:
                    print("✓ Role column already exists")
            
            # Update existing admin users to have 'admin' role
            conn.execute(text("UPDATE \"user\" SET role = 'admin' WHERE is_admin = true"))
            print("✓ Updated existing admin users to have 'admin' role")
            
            # Commit the changes
            conn.commit()
            
            print("✓ Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Running migration: Add user roles")
    print("=" * 40)
    
    success = migrate_add_user_roles()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nUser roles implemented:")
        print("- 'admin': Full access including admin dashboard")
        print("- 'user': Regular user, premium features require payment")
        print("- 'ff': Friends & family, all features unlocked")
    else:
        print("\n❌ Migration failed!")
