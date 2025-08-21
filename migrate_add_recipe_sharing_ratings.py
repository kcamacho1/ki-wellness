#!/usr/bin/env python3
"""
Migration script to add recipe sharing and rating functionality
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_add_recipe_sharing_ratings():
    print("🔄 Adding recipe sharing and rating functionality...")
    
    db_url = os.getenv('DATABASE_URL', 'sqlite:///ki_wellness.db')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    engine = create_engine(db_url)
    
    sql_statements = [
        # Add is_public column to recipe table
        """
        ALTER TABLE recipe 
        ADD COLUMN is_public BOOLEAN DEFAULT FALSE
        """,
        
        # Create recipe_rating table
        """
        CREATE TABLE IF NOT EXISTS recipe_rating (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_id) REFERENCES recipe (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE,
            UNIQUE(recipe_id, user_id)
        )
        """,
        
        # Create index for recipe ratings
        """
        CREATE INDEX IF NOT EXISTS idx_recipe_rating_recipe_id 
        ON recipe_rating (recipe_id)
        """,
        
        # Create index for user ratings
        """
        CREATE INDEX IF NOT EXISTS idx_recipe_rating_user_id 
        ON recipe_rating (user_id)
        """
    ]
    
    try:
        with engine.connect() as conn:
            for i, statement in enumerate(sql_statements, 1):
                print(f"  📝 Executing statement {i}/{len(sql_statements)}...")
                conn.execute(text(statement))
            conn.commit()
        print("✅ Recipe sharing and rating functionality added successfully!")
    except Exception as e:
        print(f"❌ Error adding recipe sharing and rating functionality: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_add_recipe_sharing_ratings()
