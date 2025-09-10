#!/usr/bin/env python3
"""
Script to update all existing recipes in the database with nutritional data
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db, Recipe, RecipeIngredient
from services.nutrition_service import nutrition_service
from flask import Flask
from config.environment import get_environment_detector

def create_app():
    """Create Flask app with proper configuration"""
    app = Flask(__name__)
    
    # Get environment detector and configure app
    env_detector = get_environment_detector()
    app.config.update(env_detector.get_database_config())
    app.config.update(env_detector.get_flask_config())
    
    # Initialize database
    db.init_app(app)
    
    return app

def update_all_recipes_nutrition():
    """Update nutritional data for all existing recipes"""
    app = create_app()
    
    with app.app_context():
        print("🍎 Updating nutritional data for all existing recipes...")
        print("="*60)
        
        # Get all recipes
        recipes = Recipe.query.all()
        total_recipes = len(recipes)
        
        if total_recipes == 0:
            print("No recipes found in the database.")
            return
        
        print(f"Found {total_recipes} recipes to process")
        print()
        
        # Statistics
        successful_updates = 0
        failed_updates = 0
        total_ingredients_processed = 0
        total_ingredients_found = 0
        
        for i, recipe in enumerate(recipes, 1):
            print(f"[{i}/{total_recipes}] Processing: {recipe.name}")
            
            # Count ingredients
            ingredients = RecipeIngredient.query.filter_by(recipe_id=recipe.id).all()
            ingredient_count = len(ingredients)
            total_ingredients_found += ingredient_count
            
            if ingredient_count == 0:
                print(f"  ⚠️ No ingredients found for this recipe")
                continue
            
            # Check if ingredients already have nutritional data
            ingredients_with_nutrition = sum(1 for ing in ingredients if ing.calories and ing.calories > 0)
            
            if ingredients_with_nutrition == ingredient_count:
                print(f"  ✅ All {ingredient_count} ingredients already have nutritional data")
                successful_updates += 1
                total_ingredients_processed += ingredient_count
                continue
            
            print(f"  📊 {ingredients_with_nutrition}/{ingredient_count} ingredients have nutritional data")
            
            try:
                # Update nutritional data
                result = nutrition_service.bulk_update_recipe_nutrition(recipe.id)
                
                if result['success']:
                    processed = result['nutrition']['ingredients_processed']
                    total = result['nutrition']['ingredients_total']
                    print(f"  ✅ Updated nutrition for {processed}/{total} ingredients")
                    successful_updates += 1
                    total_ingredients_processed += processed
                else:
                    print(f"  ❌ Failed: {result['message']}")
                    failed_updates += 1
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                failed_updates += 1
            
            print()
        
        # Print summary
        print("="*60)
        print("📊 NUTRITION UPDATE SUMMARY")
        print("="*60)
        print(f"Total recipes processed: {total_recipes}")
        print(f"Successful updates: {successful_updates}")
        print(f"Failed updates: {failed_updates}")
        print(f"Total ingredients found: {total_ingredients_found}")
        print(f"Total ingredients processed: {total_ingredients_processed}")
        print(f"Success rate: {(successful_updates/total_recipes)*100:.1f}%")
        print(f"Ingredient coverage: {(total_ingredients_processed/total_ingredients_found)*100:.1f}%")
        
        if failed_updates > 0:
            print(f"\n⚠️ {failed_updates} recipes failed to update. Check the logs above for details.")
        else:
            print(f"\n🎉 All recipes updated successfully!")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function"""
    try:
        update_all_recipes_nutrition()
    except KeyboardInterrupt:
        print("\n\n⏹️ Update cancelled by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
