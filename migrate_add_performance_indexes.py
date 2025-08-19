#!/usr/bin/env python3
"""
Migration script to add performance indexes for AI chat optimization
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def add_performance_indexes():
    """Add database indexes for better AI chat performance"""
    
    with app.app_context():
        try:
            print("Adding performance indexes for AI chat optimization...")
            
            # Create indexes for faster queries with correct table names
            indexes = [
                # Food logs indexes
                "CREATE INDEX IF NOT EXISTS idx_food_log_user_date ON food_log(user_id, date)",
                "CREATE INDEX IF NOT EXISTS idx_food_log_date ON food_log(date)",
                
                # Mood logs indexes
                "CREATE INDEX IF NOT EXISTS idx_mood_log_user_date ON mood_log(user_id, date)",
                "CREATE INDEX IF NOT EXISTS idx_mood_log_date ON mood_log(date)",
                
                # Water logs indexes
                "CREATE INDEX IF NOT EXISTS idx_water_log_user_date ON water_log(user_id, date)",
                "CREATE INDEX IF NOT EXISTS idx_water_log_date ON water_log(date)",
                
                # Notes indexes
                "CREATE INDEX IF NOT EXISTS idx_note_user_date ON note(user_id, date)",
                "CREATE INDEX IF NOT EXISTS idx_note_date ON note(date)",
                
                # AI Analysis indexes
                "CREATE INDEX IF NOT EXISTS idx_ai_analysis_user ON ai_analysis(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_ai_analysis_updated ON ai_analysis(updated_at)"
            ]
            
            for index_sql in indexes:
                try:
                    db.session.execute(text(index_sql))
                    print(f"✓ Created index: {index_sql.split('IF NOT EXISTS ')[1].split(' ON ')[0]}")
                except Exception as e:
                    print(f"⚠ Index might already exist: {e}")
            
            db.session.commit()
            print("✓ All performance indexes added successfully!")
            
        except Exception as e:
            print(f"❌ Error adding indexes: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    add_performance_indexes()
