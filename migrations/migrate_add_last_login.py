#!/usr/bin/env python3
"""
Migration script to add last_login field to User model
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from sqlalchemy import text

def add_last_login_field():
    """Add last_login field to User table"""
    with app.app_context():
        try:
            # Check if we're using PostgreSQL or SQLite
            db_url = str(db.engine.url.drivername)
            
            if 'postgresql' in db_url:
                # PostgreSQL version with quoted table name
                sql = '''
                    ALTER TABLE "user" 
                    ADD COLUMN last_login TIMESTAMP
                '''
            else:
                # SQLite version
                sql = '''
                    ALTER TABLE user 
                    ADD COLUMN last_login DATETIME
                '''
            
            # Add last_login column to User table
            with db.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print("✅ Successfully added last_login field to User table")
            
        except Exception as e:
            print(f"❌ Error adding last_login field: {e}")
            # Check if column already exists
            try:
                with db.engine.connect() as conn:
                    if 'postgresql' in db_url:
                        result = conn.execute(text('SELECT last_login FROM "user" LIMIT 1'))
                    else:
                        result = conn.execute(text('SELECT last_login FROM user LIMIT 1'))
                print("✅ last_login field already exists")
            except:
                print("❌ Column does not exist and could not be created")
                return False
        
        return True

if __name__ == '__main__':
    print("🔄 Adding last_login field to User model...")
    success = add_last_login_field()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
