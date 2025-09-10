#!/usr/bin/env python3
"""
Script to clean recipe data from the database while maintaining table structure.
This script will remove all recipe-related data but keep the table schemas intact.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db, Recipe, RecipeIngredient, RecipeInstruction, RecipeRating
from config.environment import get_environment_detector

def clean_recipe_data():
    """Clean all recipe data from the database"""
    print("🧹 Starting recipe data cleanup...")
    
    # Initialize environment detector
    env_detector = get_environment_detector()
    print(f"Environment: {'Production' if env_detector.is_production else 'Development'}")
    
    try:
        # Check if recipe tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        recipe_tables = ['recipe', 'recipe_ingredient', 'recipe_instruction', 'recipe_rating']
        missing_tables = [table for table in recipe_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"⚠️  Recipe tables not found: {missing_tables}")
            print("Please run the recipe migration first to create the tables.")
            return
        
        print("✅ All recipe tables exist in the database")
        
        # Count existing data
        recipe_count = Recipe.query.count()
        ingredient_count = RecipeIngredient.query.count()
        instruction_count = RecipeInstruction.query.count()
        rating_count = RecipeRating.query.count()
        
        print(f"📊 Current data counts:")
        print(f"   - Recipes: {recipe_count}")
        print(f"   - Ingredients: {ingredient_count}")
        print(f"   - Instructions: {instruction_count}")
        print(f"   - Ratings: {rating_count}")
        
        if recipe_count == 0:
            print("✅ No recipe data found. Database is already clean.")
            return
        
        # Confirm deletion
        print(f"\n⚠️  This will delete ALL recipe data:")
        print(f"   - {recipe_count} recipes")
        print(f"   - {ingredient_count} ingredients")
        print(f"   - {instruction_count} instructions")
        print(f"   - {rating_count} ratings")
        
        # In production, require explicit confirmation
        if env_detector.is_production:
            confirmation = input("\nType 'DELETE ALL RECIPES' to confirm: ")
            if confirmation != 'DELETE ALL RECIPES':
                print("❌ Operation cancelled.")
                return
        else:
            # In development, just ask for simple confirmation
            confirmation = input("\nProceed with deletion? (y/N): ")
            if confirmation.lower() != 'y':
                print("❌ Operation cancelled.")
                return
        
        print("\n🗑️  Deleting recipe data...")
        
        # Delete in the correct order to respect foreign key constraints
        # Delete ratings first (they reference recipes)
        deleted_ratings = RecipeRating.query.delete()
        print(f"   ✅ Deleted {deleted_ratings} ratings")
        
        # Delete instructions (they reference recipes)
        deleted_instructions = RecipeInstruction.query.delete()
        print(f"   ✅ Deleted {deleted_instructions} instructions")
        
        # Delete ingredients (they reference recipes)
        deleted_ingredients = RecipeIngredient.query.delete()
        print(f"   ✅ Deleted {deleted_ingredients} ingredients")
        
        # Delete recipes last
        deleted_recipes = Recipe.query.delete()
        print(f"   ✅ Deleted {deleted_recipes} recipes")
        
        # Commit the changes
        db.session.commit()
        
        print(f"\n✅ Recipe data cleanup completed successfully!")
        print(f"   - Deleted {deleted_recipes} recipes")
        print(f"   - Deleted {deleted_ingredients} ingredients")
        print(f"   - Deleted {deleted_instructions} instructions")
        print(f"   - Deleted {deleted_ratings} ratings")
        
        # Verify cleanup
        remaining_recipes = Recipe.query.count()
        if remaining_recipes == 0:
            print("✅ Verification: All recipe data has been removed.")
        else:
            print(f"⚠️  Warning: {remaining_recipes} recipes still remain.")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    load_dotenv()
    
    # Import Flask app to get database context
    from app import app
    
    with app.app_context():
        clean_recipe_data()
