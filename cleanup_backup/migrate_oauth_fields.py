#!/usr/bin/env python3
"""
Migration script to add OAuth-related fields to the users table.
This adds fields for Google OAuth integration.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, db
from sqlalchemy import text, inspect

def migrate_oauth_fields():
    """Add OAuth fields to users table"""
    with app.app_context():
        try:
            print("🔧 Starting OAuth fields migration...")
            
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'users' not in existing_tables:
                print("❌ users table does not exist. Creating it...")
                db.create_all()
                print("✅ users table created successfully!")
                return
            
            # Get current columns
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            print(f"📊 Current columns: {column_names}")
            
            # Define OAuth fields to add
            oauth_fields = {
                'oauth_provider': 'VARCHAR(20)',  # 'google', 'facebook', etc.
                'oauth_id': 'VARCHAR(255)',  # OAuth provider's user ID
                'oauth_email': 'VARCHAR(255)',  # Email from OAuth provider
                'oauth_name': 'VARCHAR(255)',  # Name from OAuth provider
                'oauth_picture': 'VARCHAR(500)'  # Profile picture URL from OAuth provider
            }
            
            # Add missing fields
            added_count = 0
            for field_name, field_type in oauth_fields.items():
                if field_name not in column_names:
                    print(f"   Adding field: {field_name} ({field_type})")
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}"))
                            conn.commit()
                        print(f"     ✅ Added {field_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"     ⚠️  Could not add {field_name}: {e}")
                else:
                    print(f"   ✅ {field_name} already exists")
            
            if added_count > 0:
                print(f"✅ Successfully added {added_count} OAuth fields to users table!")
            else:
                print("✅ All OAuth fields already exist in users table!")
            
            # Verify the table structure
            print("\n📋 Final users table structure:")
            final_columns = inspector.get_columns('users')
            for col in final_columns:
                print(f"   - {col['name']}: {col['type']}")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            raise

if __name__ == "__main__":
    migrate_oauth_fields()
