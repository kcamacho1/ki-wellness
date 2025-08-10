#!/usr/bin/env python3
"""
Migration script to create the food_journal table
"""

import psycopg2
import os
from config import DevelopmentConfig

def migrate_food_journal():
    """Create the food_journal table"""
    conn = None
    cursor = None
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=DevelopmentConfig.POSTGRES_HOST,
            port=DevelopmentConfig.POSTGRES_PORT,
            database=DevelopmentConfig.POSTGRES_DB,
            user=DevelopmentConfig.POSTGRES_USER,
            password=DevelopmentConfig.POSTGRES_PASSWORD
        )
        
        cursor = conn.cursor()
        
        # Create food_journal table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS food_journal (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            food_name VARCHAR(200) NOT NULL,
            brand VARCHAR(100),
            serving_size FLOAT NOT NULL,
            serving_unit VARCHAR(20) NOT NULL,
            calories FLOAT,
            protein FLOAT,
            carbs FLOAT,
            fat FLOAT,
            fiber FLOAT,
            sugar FLOAT,
            sodium FLOAT,
            mood VARCHAR(50),
            notes TEXT,
            consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_food_journal_user_id ON food_journal(user_id);
        CREATE INDEX IF NOT EXISTS idx_food_journal_consumed_at ON food_journal(consumed_at);
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        print("✅ Food journal table created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating food journal table: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_food_journal()
