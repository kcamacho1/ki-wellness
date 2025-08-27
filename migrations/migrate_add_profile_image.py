#!/usr/bin/env python3
"""
Migration script to add profile_image field to User model
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from sqlalchemy import text

def add_profile_image_field():
    """Add profile_image field to User table"""
    with app.app_context():
        try:
            # Add profile_image column to User table
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE "user" 
                    ADD COLUMN profile_image VARCHAR(255)
                """))
                conn.commit()
            print("✅ Successfully added profile_image field to User table")
            
        except Exception as e:
            print(f"❌ Error adding profile_image field: {e}")
            # Check if column already exists
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT profile_image FROM "user" LIMIT 1
                    """))
                print("✅ profile_image field already exists")
            except:
                print("❌ Column does not exist and could not be created")
                return False
        
        return True

if __name__ == '__main__':
    print("🔄 Adding profile_image field to User model...")
    success = add_profile_image_field()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
