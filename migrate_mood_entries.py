#!/usr/bin/env python3
"""
Migration script to add mood_entries table
"""

import psycopg2
from config import DevelopmentConfig

def migrate_mood_entries():
    """Add mood_entries table to the database"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DevelopmentConfig.POSTGRES_HOST,
            database=DevelopmentConfig.POSTGRES_DB,
            user=DevelopmentConfig.POSTGRES_USER,
            password=DevelopmentConfig.POSTGRES_PASSWORD,
            port=DevelopmentConfig.POSTGRES_PORT
        )
        
        cursor = conn.cursor()
        
        # Create mood_entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mood_entries (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                mood VARCHAR(50) NOT NULL,
                notes TEXT,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles(id)
            );
        """)
        
        # Create index on user_id for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mood_entries_user_id ON mood_entries(user_id);
        """)
        
        # Create index on logged_at for date range queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mood_entries_logged_at ON mood_entries(logged_at);
        """)
        
        conn.commit()
        print("✅ mood_entries table created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating mood_entries table: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_mood_entries()
