#!/usr/bin/env python3
"""
Direct migration script to add last_login field to User model
This script connects directly to the database without Flask context
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def add_last_login_field():
    """Add last_login field to User table"""
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    print(f"🔄 Connecting to database...")
    
    try:
        # Create database engine
        engine = create_engine(database_url)
        
        # Check if we're using PostgreSQL or SQLite
        db_url = str(engine.url.drivername)
        
        if 'postgresql' in db_url:
            # PostgreSQL version with quoted table name
            sql = '''
                ALTER TABLE "user" 
                ADD COLUMN last_login TIMESTAMP
            '''
            print("📊 Using PostgreSQL syntax")
        else:
            # SQLite version
            sql = '''
                ALTER TABLE user 
                ADD COLUMN last_login DATETIME
            '''
            print("📊 Using SQLite syntax")
        
        # Add last_login column to User table
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print("✅ Successfully added last_login field to User table")
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'already exists' in error_msg or 'duplicate column' in error_msg:
            print("✅ last_login field already exists")
            return True
        else:
            print(f"❌ Error adding last_login field: {e}")
            # Try to check if column already exists
            try:
                with engine.connect() as conn:
                    if 'postgresql' in db_url:
                        conn.execute(text('SELECT last_login FROM "user" LIMIT 1'))
                    else:
                        conn.execute(text('SELECT last_login FROM user LIMIT 1'))
                print("✅ last_login field already exists (verified)")
                return True
            except:
                print("❌ Column does not exist and could not be created")
                return False
    
    return True

if __name__ == '__main__':
    print("🔄 Adding last_login field to User model...")
    print("📍 Working directory:", os.getcwd())
    print("📁 Script location:", os.path.dirname(os.path.abspath(__file__)))
    
    success = add_last_login_field()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
