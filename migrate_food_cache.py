#!/usr/bin/env python3
"""
Migration script to create the food_cache table
"""

import psycopg2
import os
from config import DevelopmentConfig

def migrate_food_cache():
    """Create the food_cache table"""
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
        
        # Create food_cache table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS food_cache (
            id SERIAL PRIMARY KEY,
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
            source VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_food_cache_food_name ON food_cache(food_name);
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        print("✅ Food cache table created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating food cache table: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_food_cache()
