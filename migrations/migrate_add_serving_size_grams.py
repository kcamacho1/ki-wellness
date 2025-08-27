#!/usr/bin/env python3
"""
Migration script to add serving_size_grams column to recipe_ingredient table
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_add_serving_size_grams():
    print("🔄 Adding serving_size_grams column to recipe_ingredient table...")
    
    db_url = os.getenv('DATABASE_URL', 'sqlite:///ki_wellness.db')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    engine = create_engine(db_url)
    
    sql_statements = [
        """
        ALTER TABLE recipe_ingredient 
        ADD COLUMN serving_size_grams FLOAT DEFAULT 0
        """
    ]
    
    try:
        with engine.connect() as conn:
            for i, statement in enumerate(sql_statements, 1):
                print(f"  📝 Executing statement {i}/{len(sql_statements)}...")
                conn.execute(text(statement))
            conn.commit()
        print("✅ serving_size_grams column added successfully!")
    except Exception as e:
        print(f"❌ Error adding serving_size_grams column: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_add_serving_size_grams()
