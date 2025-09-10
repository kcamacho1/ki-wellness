#!/usr/bin/env python3
"""
Nutrition Service for Ki Wellness
Automatically fetches nutritional data for recipe ingredients using existing APIs
"""

import os
import requests
import concurrent.futures
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from database import db, RecipeIngredient
from services.food_data import COMMON_FOODS_DB, BASIC_FOODS

# Load environment variables
USDA_API_KEY = os.getenv('USDA_API_KEY')

class NutritionService:
    """Service to automatically fetch nutritional data for recipe ingredients"""
    
    def __init__(self):
        self.usda_api_key = USDA_API_KEY
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        self.nutrition_cache = {}  # Simple in-memory cache
    
    def get_ingredient_nutrition(self, ingredient: RecipeIngredient) -> Dict[str, Any]:
        """
        Get nutritional data for a single ingredient
        Returns the ingredient with updated nutritional information
        """
        # Check if ingredient already has nutritional data
        if (ingredient.calories and ingredient.calories > 0 and 
            ingredient.protein and ingredient.protein > 0):
            return ingredient.to_dict()
        
        # Try to fetch nutritional data
        nutrition_data = self._fetch_nutrition_for_ingredient(ingredient)
        
        if nutrition_data:
            # Update the ingredient with nutritional data
            self._update_ingredient_nutrition(ingredient, nutrition_data)
            return ingredient.to_dict()
        
        # Return ingredient as-is if no nutrition data found
        return ingredient.to_dict()
    
    def get_recipe_nutrition(self, recipe_ingredients: List[RecipeIngredient]) -> Dict[str, Any]:
        """
        Get comprehensive nutritional data for all recipe ingredients
        Returns total nutritional breakdown for the recipe
        """
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0,
            'ingredients_processed': 0,
            'ingredients_total': len(recipe_ingredients)
        }
        
        # Process ingredients in parallel for better performance
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for ingredient in recipe_ingredients:
                future = executor.submit(self.get_ingredient_nutrition, ingredient)
                futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                try:
                    ingredient_data = future.result(timeout=10)
                    
                    # Add to total nutrition
                    if ingredient_data.get('calories'):
                        total_nutrition['calories'] += ingredient_data['calories']
                    if ingredient_data.get('protein'):
                        total_nutrition['protein'] += ingredient_data['protein']
                    if ingredient_data.get('carbs'):
                        total_nutrition['carbs'] += ingredient_data['carbs']
                    if ingredient_data.get('fat'):
                        total_nutrition['fat'] += ingredient_data['fat']
                    if ingredient_data.get('fiber'):
                        total_nutrition['fiber'] += ingredient_data['fiber']
                    if ingredient_data.get('sugar'):
                        total_nutrition['sugar'] += ingredient_data['sugar']
                    if ingredient_data.get('sodium'):
                        total_nutrition['sodium'] += ingredient_data['sodium']
                    
                    total_nutrition['ingredients_processed'] += 1
                    
                except Exception as e:
                    print(f"Error processing ingredient nutrition: {e}")
        
        return total_nutrition
    
    def _fetch_nutrition_for_ingredient(self, ingredient: RecipeIngredient) -> Optional[Dict[str, Any]]:
        """
        Fetch nutritional data for an ingredient using multiple sources
        """
        food_name = ingredient.food_name.lower().strip()
        
        # Check cache first
        cache_key = f"{food_name}_{ingredient.amount}_{ingredient.unit}"
        if cache_key in self.nutrition_cache:
            cached_data, timestamp = self.nutrition_cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        # Try different sources in order of preference
        nutrition_data = None
        
        # 1. Check local common foods database
        nutrition_data = self._get_from_common_foods(food_name)
        
        # 2. Try USDA API for basic foods
        if not nutrition_data and self.usda_api_key:
            nutrition_data = self._get_from_usda_api(food_name)
        
        # 3. Try Open Food Facts API
        if not nutrition_data:
            nutrition_data = self._get_from_openfoodfacts_api(food_name)
        
        # Cache the result if found
        if nutrition_data:
            self.nutrition_cache[cache_key] = (nutrition_data, datetime.now())
        
        return nutrition_data
    
    def _get_from_common_foods(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Get nutrition data from local common foods database"""
        # Try exact match first
        if food_name in COMMON_FOODS_DB:
            return COMMON_FOODS_DB[food_name]
        
        # Try partial matches
        for key, data in COMMON_FOODS_DB.items():
            if key in food_name or food_name in key:
                return data
        
        return None
    
    def _get_from_usda_api(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Get nutrition data from USDA FoodData Central API"""
        try:
            if not self.usda_api_key:
                return None
            
            url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            params = {
                'query': food_name,
                'api_key': self.usda_api_key,
                'pageSize': 1,
                'dataType': ['Survey (FNDDS)', 'Foundation']
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get('foods'):
                food = data['foods'][0]
                nutrients = {n['nutrientName']: n.get('value', 0) for n in food.get('foodNutrients', [])}
                
                return {
                    'name': food.get('description', 'Unknown'),
                    'calories': int(nutrients.get('Energy', 0) or 0),
                    'protein': round(nutrients.get('Protein', 0) or 0, 1),
                    'carbs': round(nutrients.get('Carbohydrate, by difference', 0) or 0, 1),
                    'fat': round(nutrients.get('Total lipid (fat)', 0) or 0, 1),
                    'fiber': round(nutrients.get('Fiber, total dietary', 0) or 0, 1),
                    'sugar': round(nutrients.get('Sugars, total including NLEA', 0) or 0, 1),
                    'sodium': round((nutrients.get('Sodium, Na', 0) or 0) / 1000, 1),  # Convert mg to g
                    'source': 'usda'
                }
        
        except Exception as e:
            print(f"USDA API error for {food_name}: {e}")
        
        return None
    
    def _get_from_openfoodfacts_api(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Get nutrition data from Open Food Facts API"""
        try:
            url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                'search_terms': food_name,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 1,
                'fields': 'product_name,brands,nutriments'
            }
            headers = {
                'User-Agent': 'KiWellness/1.0 (https://kiwellness.org)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=8)
            response.raise_for_status()
            data = response.json()
            
            if data.get('products'):
                product = data['products'][0]
                nutriments = product.get('nutriments', {})
                
                return {
                    'name': product.get('product_name', 'Unknown Product'),
                    'calories': int(nutriments.get('energy-kcal_100g', 0) or 0),
                    'protein': round(nutriments.get('proteins_100g', 0) or 0, 1),
                    'carbs': round(nutriments.get('carbohydrates_100g', 0) or 0, 1),
                    'fat': round(nutriments.get('fat_100g', 0) or 0, 1),
                    'fiber': round(nutriments.get('fiber_100g', 0) or 0, 1),
                    'sugar': round(nutriments.get('sugars_100g', 0) or 0, 1),
                    'sodium': round(nutriments.get('sodium_100g', 0) or 0, 1),
                    'source': 'openfoodfacts'
                }
        
        except Exception as e:
            print(f"Open Food Facts API error for {food_name}: {e}")
        
        return None
    
    def _update_ingredient_nutrition(self, ingredient: RecipeIngredient, nutrition_data: Dict[str, Any]):
        """Update ingredient with nutritional data"""
        try:
            # Calculate nutrition per serving based on amount and unit
            amount = ingredient.amount or 1
            unit = ingredient.unit or 'piece'
            
            # Convert to per-100g basis for calculation
            if unit.lower() in ['g', 'gram', 'grams']:
                multiplier = amount / 100
            elif unit.lower() in ['ml', 'milliliter', 'milliliters']:
                multiplier = amount / 100  # Assume 1ml = 1g for most foods
            elif unit.lower() in ['cup', 'cups']:
                multiplier = amount * 0.25  # Rough estimate: 1 cup ≈ 250g
            elif unit.lower() in ['tbsp', 'tablespoon', 'tablespoons']:
                multiplier = amount * 0.015  # Rough estimate: 1 tbsp ≈ 15g
            elif unit.lower() in ['tsp', 'teaspoon', 'teaspoons']:
                multiplier = amount * 0.005  # Rough estimate: 1 tsp ≈ 5g
            else:
                multiplier = amount  # Assume 1 piece = 100g
            
            # Update ingredient with calculated nutrition
            ingredient.calories = round(nutrition_data.get('calories', 0) * multiplier)
            ingredient.protein = round(nutrition_data.get('protein', 0) * multiplier, 1)
            ingredient.carbs = round(nutrition_data.get('carbs', 0) * multiplier, 1)
            ingredient.fat = round(nutrition_data.get('fat', 0) * multiplier, 1)
            ingredient.fiber = round(nutrition_data.get('fiber', 0) * multiplier, 1)
            ingredient.sugar = round(nutrition_data.get('sugar', 0) * multiplier, 1)
            ingredient.sodium = round(nutrition_data.get('sodium', 0) * multiplier, 1)
            
            # Save to database (only if we're in an app context)
            try:
                db.session.commit()
            except Exception as context_error:
                # If we're not in an app context, just update the object
                # The calling code will handle the commit
                pass
            
        except Exception as e:
            print(f"Error updating ingredient nutrition: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def bulk_update_recipe_nutrition(self, recipe_id: int) -> Dict[str, Any]:
        """
        Bulk update nutritional data for all ingredients in a recipe
        """
        try:
            # Get all ingredients for the recipe
            ingredients = RecipeIngredient.query.filter_by(recipe_id=recipe_id).all()
            
            if not ingredients:
                return {'success': False, 'message': 'No ingredients found for recipe'}
            
            # Process all ingredients
            nutrition_summary = self.get_recipe_nutrition(ingredients)
            
            # Commit all changes to database
            try:
                db.session.commit()
            except Exception as commit_error:
                print(f"Database commit error: {commit_error}")
                db.session.rollback()
                return {'success': False, 'message': f'Database error: {str(commit_error)}'}
            
            return {
                'success': True,
                'message': f'Updated nutrition for {nutrition_summary["ingredients_processed"]}/{nutrition_summary["ingredients_total"]} ingredients',
                'nutrition': nutrition_summary
            }
            
        except Exception as e:
            print(f"Error in bulk update: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return {'success': False, 'message': f'Error updating recipe nutrition: {str(e)}'}

# Global instance
nutrition_service = NutritionService()
