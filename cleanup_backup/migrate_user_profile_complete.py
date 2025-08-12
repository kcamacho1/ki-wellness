#!/usr/bin/env python3
"""
Migration script to add all missing fields to user_profiles table to match the complete UserProfile model.
This ensures the database schema matches the application's expectations.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, db
from sqlalchemy import text, inspect

def migrate_user_profile_complete():
    """Add all missing fields to user_profiles table"""
    with app.app_context():
        try:
            print("🔧 Starting complete user_profiles table migration...")
            
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'user_profiles' not in existing_tables:
                print("❌ user_profiles table does not exist. Creating it...")
                db.create_all()
                print("✅ user_profiles table created successfully!")
                return
            
            # Get current columns
            columns = inspector.get_columns('user_profiles')
            column_names = [col['name'] for col in columns]
            print(f"📊 Current columns: {column_names}")
            
            # Define all required fields for the complete UserProfile model
            required_fields = {
                # Basic profile information
                'date_of_birth': 'DATE',
                'age': 'INTEGER',
                'weight': 'FLOAT',
                'height': 'FLOAT',
                
                # Wellness goals and preferences
                'goal': 'VARCHAR(100)',
                'goals': 'TEXT',
                'custom_goal': 'VARCHAR(200)',
                'ailments': 'TEXT',
                'dietary_preferences': 'TEXT',
                'sleep_schedule': 'VARCHAR(100)',
                
                # Physical wellness
                'daily_activities': 'TEXT',
                'exercise_routine': 'TEXT',
                'day_notes': 'TEXT',
                'night_notes': 'TEXT',
                
                # Spiritual and emotional wellness
                'spiritual_religion': 'TEXT',
                'self_connection': 'TEXT',
                'surroundings_connection': 'TEXT',
                'providing_others': 'TEXT',
                'safe_groups': 'TEXT',
                'awe_things': 'TEXT',
                'creative_expression': 'TEXT',
                'upsetting_situations': 'TEXT',
                'spirit_notes': 'TEXT'
            }
            
            # Add missing fields
            added_count = 0
            for field_name, field_type in required_fields.items():
                if field_name not in column_names:
                    print(f"   Adding field: {field_name} ({field_type})")
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(text(f"ALTER TABLE user_profiles ADD COLUMN {field_name} {field_type}"))
                            conn.commit()
                        print(f"     ✅ Added {field_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"     ⚠️  Could not add {field_name}: {e}")
                else:
                    print(f"   ✅ {field_name} already exists")
            
            if added_count > 0:
                print(f"✅ Successfully added {added_count} new fields to user_profiles table!")
            else:
                print("✅ All required fields already exist in user_profiles table!")
            
            # Verify the table structure
            print("\n📋 Final user_profiles table structure:")
            final_columns = inspector.get_columns('user_profiles')
            for col in final_columns:
                print(f"   - {col['name']}: {col['type']}")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            raise

if __name__ == "__main__":
    migrate_user_profile_complete()
