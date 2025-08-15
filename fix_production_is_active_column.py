#!/usr/bin/env python3
"""
Fix production database - Add missing is_active column to users table
This script specifically addresses the login error where is_active column doesn't exist.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def fix_is_active_column():
    """Add missing is_active column to users table"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    # Convert SQLite URL to PostgreSQL if needed
    if database_url.startswith('sqlite://'):
        print("❌ This script is for PostgreSQL production database")
        return False
    
    print("🔧 Starting is_active column fix for production database...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Check if users table exists
        inspector = inspect(engine)
        if 'users' not in inspector.get_table_names():
            print("❌ users table does not exist")
            return False
        
        # Check current columns
        user_columns = inspector.get_columns('users')
        user_column_names = [col['name'] for col in user_columns]
        print(f"📊 Current users table columns: {user_column_names}")
        
        # Check if is_active column already exists
        if 'is_active' in user_column_names:
            print("✅ is_active column already exists")
            return True
        
        # Add is_active column
        print("➕ Adding is_active column to users table...")
        with engine.connect() as conn:
            # Add the column with default value
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL"))
            conn.commit()
        
        print("✅ Successfully added is_active column to users table")
        
        # Verify the column was added
        inspector = inspect(engine)
        user_columns = inspector.get_columns('users')
        user_column_names = [col['name'] for col in user_columns]
        
        if 'is_active' in user_column_names:
            print("✅ Verification: is_active column is now present")
            return True
        else:
            print("❌ Verification failed: is_active column not found after addition")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing is_active column: {e}")
        return False

if __name__ == "__main__":
    success = fix_is_active_column()
    if success:
        print("🎉 is_active column fix completed successfully!")
        sys.exit(0)
    else:
        print("💥 is_active column fix failed!")
        sys.exit(1)
