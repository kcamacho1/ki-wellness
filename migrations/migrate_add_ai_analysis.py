#!/usr/bin/env python3
"""
Migration script to add AIAnalysis table
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_add_ai_analysis():
    """Add AIAnalysis table to database"""
    
    # Database configuration
    if os.getenv('DATABASE_URL'):
        # Production - PostgreSQL
        database_url = os.getenv('DATABASE_URL')
    else:
        # Development - SQLite
        database_url = 'sqlite:///ki_wellness.db'
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check if table already exists
            if database_url.startswith('sqlite'):
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='ai_analysis'
                """)).fetchone()
            else:
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'ai_analysis'
                """)).fetchone()
            
            if result:
                print("✅ AIAnalysis table already exists")
                return
            
            # Create AIAnalysis table
            if database_url.startswith('sqlite'):
                conn.execute(text("""
                    CREATE TABLE ai_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        analysis_data TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user (id)
                    )
                """))
            else:
                conn.execute(text("""
                    CREATE TABLE ai_analysis (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        analysis_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES "user" (id)
                    )
                """))
            
            conn.commit()
            print("✅ AIAnalysis table created successfully")
            
    except Exception as e:
        print(f"❌ Error creating AIAnalysis table: {e}")
        sys.exit(1)

if __name__ == '__main__':
    migrate_add_ai_analysis()
