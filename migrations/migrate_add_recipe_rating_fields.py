#!/usr/bin/env python3
"""
Migration script to add average_rating and rating_count fields to Recipe model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, Recipe, RecipeRating
from config.environment import get_environment_detector

def migrate_add_rating_fields():
    """Add average_rating and rating_count fields to Recipe table"""
    
    with app.app_context():
        detector = get_environment_detector()
        
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        existing_columns = inspector.get_columns('recipe')
        column_names = [col['name'] for col in existing_columns]
        
        if 'average_rating' not in column_names:
            if detector.is_production:
                # PostgreSQL migration
                print("🔄 Running PostgreSQL migration for recipe rating fields...")
                
                try:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE "recipe" 
                            ADD COLUMN average_rating FLOAT DEFAULT 0.0
                        """))
                        conn.commit()
                    print("✅ Added average_rating column")
                except Exception as e:
                    print(f"❌ Error adding average_rating column: {e}")
            else:
                # SQLite migration
                print("🔄 Running SQLite migration for recipe rating fields...")
                
                try:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE recipe 
                            ADD COLUMN average_rating FLOAT DEFAULT 0.0
                        """))
                        conn.commit()
                    print("✅ Added average_rating column")
                except Exception as e:
                    print(f"❌ Error adding average_rating column: {e}")
        else:
            print("✅ average_rating column already exists")
        
        if 'rating_count' not in column_names:
            if detector.is_production:
                try:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE "recipe" 
                            ADD COLUMN rating_count INTEGER DEFAULT 0
                        """))
                        conn.commit()
                    print("✅ Added rating_count column")
                except Exception as e:
                    print(f"❌ Error adding rating_count column: {e}")
            else:
                try:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE recipe 
                            ADD COLUMN rating_count INTEGER DEFAULT 0
                        """))
                        conn.commit()
                    print("✅ Added rating_count column")
                except Exception as e:
                    print(f"❌ Error adding rating_count column: {e}")
        else:
            print("✅ rating_count column already exists")
        
        # Update existing recipes with calculated ratings
        print("🔄 Calculating ratings for existing recipes...")
        
        recipes = Recipe.query.all()
        updated_count = 0
        
        for recipe in recipes:
            if recipe.ratings:
                total_rating = sum(r.rating for r in recipe.ratings)
                recipe.average_rating = round(total_rating / len(recipe.ratings), 1)
                recipe.rating_count = len(recipe.ratings)
                updated_count += 1
            else:
                recipe.average_rating = 0.0
                recipe.rating_count = 0
        
        try:
            db.session.commit()
            print(f"✅ Updated {updated_count} recipes with calculated ratings")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating recipes: {e}")
            return False
        
        print("✅ Migration completed successfully!")
        return True

if __name__ == "__main__":
    migrate_add_rating_fields()
