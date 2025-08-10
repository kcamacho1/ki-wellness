#!/usr/bin/env python3
"""
Migration script to create patterns_cache table for storing analysis results.
"""

import psycopg2
from config import DevelopmentConfig

def migrate_patterns_cache():
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            host=DevelopmentConfig.POSTGRES_HOST,
            port=DevelopmentConfig.POSTGRES_PORT,
            database=DevelopmentConfig.POSTGRES_DB,
            user=DevelopmentConfig.POSTGRES_USER,
            password=DevelopmentConfig.POSTGRES_PASSWORD
        )
        cursor = conn.cursor()

        print("🔧 Creating patterns_cache table...")

        # Create patterns_cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns_cache (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES user_profiles(id),
                period_type VARCHAR(10) NOT NULL,
                analysis TEXT,
                suggestions TEXT,
                summary JSON,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add unique constraint to prevent duplicate entries for same user and period
        cursor.execute("""
            ALTER TABLE patterns_cache 
            ADD CONSTRAINT unique_user_period 
            UNIQUE (user_id, period_type)
        """)

        conn.commit()
        print("✅ Successfully created patterns_cache table!")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_patterns_cache()
