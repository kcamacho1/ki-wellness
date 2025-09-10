#!/usr/bin/env python3
"""
Script to check what recipe-related tables exist in the database.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from config.environment import get_environment_detector

def check_recipe_tables():
    """Check what recipe-related tables exist in the database"""
    print("🔍 Checking for recipe-related tables...")
    
    # Initialize environment detector
    env_detector = get_environment_detector()
    print(f"Environment: {'Production' if env_detector.is_production else 'Development'}")
    
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print(f"\n📋 All tables in database ({len(existing_tables)} total):")
        for table in sorted(existing_tables):
            print(f"   - {table}")
        
        # Look for recipe-related tables
        recipe_keywords = ['recipe', 'recipes', 'ingredient', 'instruction', 'rating']
        recipe_tables = []
        
        for table in existing_tables:
            for keyword in recipe_keywords:
                if keyword in table.lower():
                    recipe_tables.append(table)
                    break
        
        print(f"\n🍳 Recipe-related tables found ({len(recipe_tables)}):")
        if recipe_tables:
            for table in recipe_tables:
                # Get row count for each table
                try:
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                    count = result.scalar()
                    print(f"   - {table}: {count} rows")
                except Exception as e:
                    print(f"   - {table}: Error getting count - {e}")
        else:
            print("   No recipe-related tables found")
        
        # Check for any tables with 'recipe' in the name specifically
        recipe_specific = [t for t in existing_tables if 'recipe' in t.lower()]
        if recipe_specific:
            print(f"\n📝 Tables with 'recipe' in name:")
            for table in recipe_specific:
                try:
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                    count = result.scalar()
                    print(f"   - {table}: {count} rows")
                except Exception as e:
                    print(f"   - {table}: Error getting count - {e}")
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        raise

if __name__ == '__main__':
    load_dotenv()
    
    # Import Flask app to get database context
    from app import app
    
    with app.app_context():
        check_recipe_tables()
