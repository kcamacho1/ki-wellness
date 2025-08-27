#!/usr/bin/env python3
"""
Migration script to add time_of_day column to FoodLog table
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_add_time_of_day():
    """Add time_of_day column to FoodLog table"""
    
    with app.app_context():
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('food_log')]
            
            if 'time_of_day' not in columns:
                # Add the time_of_day column
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE food_log 
                        ADD COLUMN time_of_day VARCHAR(20) NOT NULL DEFAULT 'snack'
                    """))
                    conn.commit()
                print("✅ Added time_of_day column to food_log table")
            else:
                print("ℹ️  time_of_day column already exists")
                
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False
            
        return True

if __name__ == '__main__':
    print("🔄 Starting migration to add time_of_day column...")
    success = migrate_add_time_of_day()
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
