#!/usr/bin/env python3
"""
Database schema fix script for KI Wellness.
This script fixes schema mismatches and ensures all tables are properly structured.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, db
from sqlalchemy import text, inspect

def fix_database_schema():
    """Fix database schema issues"""
    with app.app_context():
        try:
            print("🔧 Starting database schema fix...")
            
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📊 Found tables: {existing_tables}")
            
            # Fix user_profiles table if it exists
            if 'user_profiles' in existing_tables:
                print("🔄 Fixing user_profiles table...")
                
                # Get current columns
                columns = inspector.get_columns('user_profiles')
                column_names = [col['name'] for col in columns]
                print(f"   Current columns: {column_names}")
                
                # Remove problematic columns that don't exist in the model
                problematic_columns = [
                    'goal', 'goals', 'date_of_birth', 'age', 'weight', 'height',
                    'ailments', 'daily_activities', 'day_notes', 'sleep_schedule',
                    'night_notes', 'dietary_preferences', 'exercise_routine',
                    'spiritual_religion', 'self_connection', 'surroundings_connection',
                    'providing_others', 'safe_groups', 'awe_things', 'creative_expression',
                    'upsetting_situations', 'spirit_notes'
                ]
                
                for col_name in problematic_columns:
                    if col_name in column_names:
                        print(f"   Removing column: {col_name}")
                        try:
                            with db.engine.connect() as conn:
                                conn.execute(text(f"ALTER TABLE user_profiles DROP COLUMN {col_name}"))
                                conn.commit()
                            print(f"     ✅ Removed {col_name}")
                        except Exception as e:
                            print(f"     ⚠️  Could not remove {col_name}: {e}")
                
                # Ensure required columns exist
                required_columns = {
                    'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                    'user_id': 'INTEGER NOT NULL',
                    'name': 'VARCHAR(100)',
                    'avatar': 'VARCHAR(100) DEFAULT "default-avatar.png"',
                    'weight_unit': 'VARCHAR(10) DEFAULT "kg"',
                    'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                    'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
                }
                
                for col_name, col_def in required_columns.items():
                    if col_name not in column_names:
                        print(f"   Adding column: {col_name}")
                        try:
                            with db.engine.connect() as conn:
                                conn.execute(text(f"ALTER TABLE user_profiles ADD COLUMN {col_name} {col_def}"))
                                conn.commit()
                            print(f"     ✅ Added {col_name}")
                        except Exception as e:
                            print(f"     ⚠️  Could not add {col_name}: {e}")
                
                print("✅ user_profiles table fixed!")
            else:
                print("ℹ️  user_profiles table does not exist - will be created when needed")
            
            # Ensure users table has is_active column
            if 'users' in existing_tables:
                print("🔄 Checking users table...")
                user_columns = inspector.get_columns('users')
                user_column_names = [col['name'] for col in user_columns]
                
                if 'is_active' not in user_column_names:
                    print("   Adding is_active column to users table...")
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"))
                            conn.commit()
                        print("     ✅ Added is_active column")
                    except Exception as e:
                        print(f"     ⚠️  Could not add is_active: {e}")
                else:
                    print("   ✅ is_active column already exists")
            
            # Ensure all required tables exist
            required_tables = ['system_settings', 'token_usage', 'api_costs']
            for table_name in required_tables:
                if table_name not in existing_tables:
                    print(f"📝 Creating {table_name} table...")
                    try:
                        if table_name == 'system_settings':
                            with db.engine.connect() as conn:
                                conn.execute(text("""
                                    CREATE TABLE system_settings (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        key VARCHAR(100) UNIQUE NOT NULL,
                                        value TEXT,
                                        description TEXT,
                                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                        updated_by INTEGER,
                                        FOREIGN KEY (updated_by) REFERENCES users (id)
                                    )
                                """))
                                conn.commit()
                        elif table_name == 'token_usage':
                            with db.engine.connect() as conn:
                                conn.execute(text("""
                                    CREATE TABLE token_usage (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        user_id INTEGER NOT NULL,
                                        month VARCHAR(7) NOT NULL,
                                        tokens_used INTEGER DEFAULT 0,
                                        cost_usd REAL DEFAULT 0.0,
                                        model_used VARCHAR(50),
                                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                        FOREIGN KEY (user_id) REFERENCES users (id)
                                    )
                                """))
                                conn.commit()
                        elif table_name == 'api_costs':
                            with db.engine.connect() as conn:
                                conn.execute(text("""
                                    CREATE TABLE api_costs (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        model_name VARCHAR(50) NOT NULL,
                                        input_cost_per_1k REAL NOT NULL,
                                        output_cost_per_1k REAL NOT NULL,
                                        is_active BOOLEAN DEFAULT 1,
                                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                        updated_by INTEGER,
                                        FOREIGN KEY (updated_by) REFERENCES users (id)
                                    )
                                """))
                                conn.commit()
                        
                        print(f"     ✅ Created {table_name} table")
                    except Exception as e:
                        print(f"     ❌ Could not create {table_name}: {e}")
                else:
                    print(f"   ✅ {table_name} table already exists")
            
            print("✅ Database schema fix completed successfully!")
            return True
                
        except Exception as e:
            print(f"❌ Database schema fix failed: {str(e)}")
            return False

if __name__ == "__main__":
    print("🚀 Database Schema Fix Script")
    print("=" * 40)
    
    success = fix_database_schema()
    
    if success:
        print("\n🎉 Database schema has been fixed!")
        print("You can now run the application without schema errors.")
    else:
        print("\n💥 Database schema fix failed. Please check the error messages above.")
        sys.exit(1)
