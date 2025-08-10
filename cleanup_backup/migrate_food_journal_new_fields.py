#!/usr/bin/env python3
"""
Migration script to add new fields to food_journal table:
- time_of_day (VARCHAR(20))
- water_amount (FLOAT)
- water_unit (VARCHAR(20))
"""

import psycopg2
from config import DevelopmentConfig

def migrate_food_journal_new_fields():
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
        
        print("🔧 Adding new fields to food_journal table...")
        
        # Add time_of_day column
        cursor.execute("""
            ALTER TABLE food_journal 
            ADD COLUMN IF NOT EXISTS time_of_day VARCHAR(20)
        """)
        
        # Add water_amount column
        cursor.execute("""
            ALTER TABLE food_journal 
            ADD COLUMN IF NOT EXISTS water_amount FLOAT
        """)
        
        # Add water_unit column
        cursor.execute("""
            ALTER TABLE food_journal 
            ADD COLUMN IF NOT EXISTS water_unit VARCHAR(20)
        """)
        
        conn.commit()
        print("✅ Successfully added new fields to food_journal table!")
        print("   - time_of_day (VARCHAR(20))")
        print("   - water_amount (FLOAT)")
        print("   - water_unit (VARCHAR(20))")
        
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
    migrate_food_journal_new_fields()
