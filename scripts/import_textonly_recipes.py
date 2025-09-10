#!/usr/bin/env python3
"""
Script to import recipes from textonlyrecipes.com into the Ki Wellness database.
This script scrapes recipe data and creates structured recipe entries with ingredients and instructions.
"""

import os
import sys
import requests
import re
import time
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db, Recipe, RecipeIngredient, RecipeInstruction, User
from config.environment import get_environment_detector

class TextOnlyRecipeImporter:
    def __init__(self):
        self.base_url = "https://www.textonlyrecipes.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.imported_count = 0
        self.failed_count = 0
        
    def get_recipe_links(self):
        """Get all recipe links from the main page"""
        print("🔍 Fetching recipe links from textonlyrecipes.com...")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all recipe links - they appear to be in a list format
            recipe_links = []
            
            # Look for links that contain recipe names
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                text = link.get_text().strip()
                
                # Skip empty links or navigation links
                if not text or text in ['Random Recipe', 'Add New Recipe', 'Create Account', 'Login', 'Search']:
                    continue
                    
                # Check if it looks like a recipe link
                if href and not href.startswith('http') and not href.startswith('#'):
                    full_url = urljoin(self.base_url, href)
                    recipe_links.append({
                        'name': text,
                        'url': full_url
                    })
            
            print(f"✅ Found {len(recipe_links)} recipe links")
            return recipe_links
            
        except Exception as e:
            print(f"❌ Error fetching recipe links: {e}")
            return []
    
    def scrape_recipe(self, recipe_url, recipe_name):
        """Scrape individual recipe data with enhanced error handling"""
        try:
            print(f"📖 Scraping: {recipe_name}")
            
            # Add retry logic for network requests
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(recipe_url, timeout=15)
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"⚠️  Network error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)  # Wait before retry
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract recipe content
            content = soup.get_text()
            
            if not content or len(content.strip()) < 50:
                print(f"⚠️  Insufficient content for {recipe_name}")
                return None
            
            # Parse ingredients and instructions
            ingredients, instructions = self.parse_recipe_content(content, recipe_name)
            
            if not ingredients:
                print(f"⚠️  No ingredients found for {recipe_name}")
                return None
            
            if not instructions:
                print(f"⚠️  No instructions found for {recipe_name}")
                # Still create recipe if ingredients exist
                instructions = ["Instructions not available"]
                
            return {
                'name': recipe_name,
                'description': f"Imported from {self.base_url}",
                'ingredients': ingredients,
                'instructions': instructions,
                'category': self.categorize_recipe(recipe_name),
                'difficulty': 'Easy',  # Default difficulty
                'servings': 4,  # Default servings
                'prep_time': None,
                'cook_time': None
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error scraping {recipe_name}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error scraping {recipe_name}: {e}")
            return None
    
    def parse_recipe_content(self, content, recipe_name):
        """Parse recipe content to extract ingredients and instructions"""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        ingredients = []
        instructions = []
        
        # Look for common ingredient patterns
        ingredient_patterns = [
            r'^(\d+(?:\.\d+)?)\s*(cups?|tablespoons?|tbsp|teaspoons?|tsp|ounces?|oz|pounds?|lb|grams?|g|kilograms?|kg|ml|milliliters?|liters?|l|pieces?|slices?|cloves?|cans?|packages?)\s+(.+)$',
            r'^(\d+(?:\.\d+)?)\s+(.+)$',
            r'^(.+?)\s+(\d+(?:\.\d+)?)\s*(cups?|tablespoons?|tbsp|teaspoons?|tsp|ounces?|oz|pounds?|lb|grams?|g|kilograms?|kg|ml|milliliters?|liters?|l|pieces?|slices?|cloves?|cans?|packages?)$'
        ]
        
        in_ingredients = False
        in_instructions = False
        
        for line in lines:
            line_lower = line.lower()
            
            # Detect ingredients section
            if any(keyword in line_lower for keyword in ['ingredients:', 'ingredient:', 'for the']):
                in_ingredients = True
                in_instructions = False
                continue
                
            # Detect instructions section
            if any(keyword in line_lower for keyword in ['instructions:', 'directions:', 'method:', 'how to', 'steps:']):
                in_ingredients = False
                in_instructions = True
                continue
            
            # Skip empty lines and headers
            if not line or len(line) < 3:
                continue
                
            # Parse ingredients
            if in_ingredients and not in_instructions:
                ingredient = self.parse_ingredient_line(line)
                if ingredient:
                    ingredients.append(ingredient)
            
            # Parse instructions
            elif in_instructions:
                if len(line) > 10:  # Only add substantial instruction lines
                    instructions.append(line)
        
        # If we didn't find clear sections, try to parse the whole content
        if not ingredients and not instructions:
            ingredients, instructions = self.fallback_parse(lines)
        
        return ingredients, instructions
    
    def parse_ingredient_line(self, line):
        """Parse a single ingredient line with improved pattern matching"""
        # Clean the line
        line = line.strip()
        
        # Handle fractions and mixed numbers
        line = re.sub(r'(\d+)\s+(\d+)/(\d+)', r'\1+\2/\3', line)  # "1 1/2" -> "1+1/2"
        line = re.sub(r'(\d+)/(\d+)', r'(\1/\2)', line)  # "1/2" -> "(1/2)"
        
        # Enhanced ingredient patterns
        patterns = [
            # Standard: "2 cups flour"
            r'^(\d+(?:\.\d+)?(?:\(\d+/\d+\))?(?:[+\-]\d+(?:\.\d+)?(?:\(\d+/\d+\))?)*)\s*(cups?|tablespoons?|tbsp|teaspoons?|tsp|ounces?|oz|pounds?|lb|grams?|g|kilograms?|kg|ml|milliliters?|liters?|l|pieces?|slices?|cloves?|cans?|packages?|pinches?|dashes?|splashes?)\s+(.+)$',
            # Just number and ingredient: "2 eggs"
            r'^(\d+(?:\.\d+)?(?:\(\d+/\d+\))?(?:[+\-]\d+(?:\.\d+)?(?:\(\d+/\d+\))?)*)\s+(.+)$',
            # Ingredient first: "flour 2 cups"
            r'^(.+?)\s+(\d+(?:\.\d+)?(?:\(\d+/\d+\))?(?:[+\-]\d+(?:\.\d+)?(?:\(\d+/\d+\))?)*)\s*(cups?|tablespoons?|tbsp|teaspoons?|tsp|ounces?|oz|pounds?|lb|grams?|g|kilograms?|kg|ml|milliliters?|liters?|l|pieces?|slices?|cloves?|cans?|packages?|pinches?|dashes?|splashes?)$',
            # Range amounts: "2-3 cups" or "1/4 to 1/2 cup"
            r'^(\d+(?:\.\d+)?(?:\(\d+/\d+\))?(?:[+\-]\d+(?:\.\d+)?(?:\(\d+/\d+\))?)*)\s*[-–—to]\s*(\d+(?:\.\d+)?(?:\(\d+/\d+\))?(?:[+\-]\d+(?:\.\d+)?(?:\(\d+/\d+\))?)*)\s*(cups?|tablespoons?|tbsp|teaspoons?|tsp|ounces?|oz|pounds?|lb|grams?|g|kilograms?|kg|ml|milliliters?|liters?|l|pieces?|slices?|cloves?|cans?|packages?|pinches?|dashes?|splashes?)\s+(.+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) == 4:  # Range pattern
                    amount1, amount2, unit, food_name = groups
                    # Use the first amount for simplicity
                    amount = self.parse_amount(amount1)
                    return {
                        'food_name': food_name.strip(),
                        'amount': amount,
                        'unit': unit.strip()
                    }
                elif len(groups) == 3:
                    amount, unit, food_name = groups
                    return {
                        'food_name': food_name.strip(),
                        'amount': self.parse_amount(amount),
                        'unit': unit.strip()
                    }
                elif len(groups) == 2:
                    if groups[0].replace('.', '').replace('(', '').replace(')', '').replace('+', '').replace('-', '').replace('/', '').isdigit():
                        amount, food_name = groups
                        # Try to infer unit from food name
                        unit = self.infer_unit_from_food_name(food_name)
                        return {
                            'food_name': food_name.strip(),
                            'amount': self.parse_amount(amount),
                            'unit': unit
                        }
                    else:
                        food_name, amount = groups
                        unit = self.infer_unit_from_food_name(food_name)
                        return {
                            'food_name': food_name.strip(),
                            'amount': self.parse_amount(amount),
                            'unit': unit
                        }
        
        # Fallback: treat the whole line as a food name with inferred unit
        unit = self.infer_unit_from_food_name(line)
        return {
            'food_name': line,
            'amount': 1,
            'unit': unit
        }
    
    def parse_amount(self, amount_str):
        """Parse amount string that may contain fractions and mixed numbers"""
        try:
            # Handle mixed numbers like "1+1/2"
            if '+' in amount_str:
                parts = amount_str.split('+')
                whole = float(parts[0])
                fraction = self.parse_fraction(parts[1])
                return whole + fraction
            
            # Handle fractions like "(1/2)"
            if '(' in amount_str and ')' in amount_str:
                fraction_str = amount_str.strip('()')
                return self.parse_fraction(fraction_str)
            
            # Handle simple numbers
            return float(amount_str)
        except:
            return 1.0
    
    def parse_fraction(self, fraction_str):
        """Parse fraction string like '1/2'"""
        try:
            if '/' in fraction_str:
                num, den = fraction_str.split('/')
                return float(num) / float(den)
            return float(fraction_str)
        except:
            return 1.0
    
    def infer_unit_from_food_name(self, food_name):
        """Infer appropriate unit based on food name"""
        food_lower = food_name.lower()
        
        # Liquids
        if any(word in food_lower for word in ['milk', 'water', 'broth', 'stock', 'juice', 'oil', 'vinegar', 'sauce', 'soup']):
            return 'cup'
        
        # Powders and dry ingredients
        if any(word in food_lower for word in ['flour', 'sugar', 'salt', 'pepper', 'spice', 'herb', 'powder', 'baking soda', 'baking powder']):
            return 'cup' if 'flour' in food_lower or 'sugar' in food_lower else 'tsp'
        
        # Eggs
        if 'egg' in food_lower:
            return 'piece'
        
        # Meat and proteins
        if any(word in food_lower for word in ['chicken', 'beef', 'pork', 'fish', 'turkey', 'ham', 'bacon', 'sausage']):
            return 'lb'
        
        # Vegetables (countable)
        if any(word in food_lower for word in ['onion', 'garlic', 'clove', 'carrot', 'potato', 'tomato', 'pepper', 'bell pepper']):
            return 'piece'
        
        # Canned goods
        if 'can' in food_lower or 'package' in food_lower:
            return 'can'
        
        # Dairy
        if any(word in food_lower for word in ['cheese', 'butter', 'cream', 'yogurt']):
            return 'cup'
        
        # Default to cup for most ingredients
        return 'cup'
    
    def fallback_parse(self, lines):
        """Fallback parsing when clear sections aren't found"""
        ingredients = []
        instructions = []
        
        for line in lines:
            # Skip very short lines
            if len(line) < 5:
                continue
                
            # Check if line looks like an ingredient (contains numbers and common units)
            if re.search(r'\d+.*(cup|tbsp|tsp|oz|lb|g|kg|ml|l|piece|slice|clove|can|package)', line, re.IGNORECASE):
                ingredient = self.parse_ingredient_line(line)
                if ingredient:
                    ingredients.append(ingredient)
            # Otherwise, treat as instruction
            elif len(line) > 15:
                instructions.append(line)
        
        return ingredients, instructions
    
    def categorize_recipe(self, recipe_name):
        """Categorize recipe based on name"""
        name_lower = recipe_name.lower()
        
        if any(word in name_lower for word in ['breakfast', 'pancake', 'waffle', 'cereal', 'oatmeal', 'muffin']):
            return 'breakfast'
        elif any(word in name_lower for word in ['lunch', 'sandwich', 'salad', 'soup']):
            return 'lunch'
        elif any(word in name_lower for word in ['dinner', 'main', 'chicken', 'beef', 'pork', 'fish', 'pasta', 'rice']):
            return 'dinner'
        elif any(word in name_lower for word in ['dessert', 'cake', 'pie', 'cookie', 'brownie', 'cheesecake']):
            return 'dessert'
        elif any(word in name_lower for word in ['snack', 'dip', 'cracker', 'trail mix']):
            return 'snack'
        else:
            return 'dinner'  # Default category
    
    def create_recipe_in_db(self, recipe_data, admin_user):
        """Create recipe in database"""
        try:
            # Create recipe
            recipe = Recipe(
                user_id=admin_user.id,
                name=recipe_data['name'],
                description=recipe_data['description'],
                servings=recipe_data['servings'],
                prep_time=recipe_data['prep_time'],
                cook_time=recipe_data['cook_time'],
                difficulty=recipe_data['difficulty'],
                category=recipe_data['category'],
                is_public=True  # Make imported recipes public
            )
            
            db.session.add(recipe)
            db.session.flush()  # Get the recipe ID
            
            # Add ingredients
            for ingredient_data in recipe_data['ingredients']:
                ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    food_name=ingredient_data['food_name'],
                    amount=ingredient_data['amount'],
                    unit=ingredient_data['unit'],
                    serving_size_grams=0,  # Will be calculated later
                    calories=0,  # Will be calculated later
                    protein=0,
                    carbs=0,
                    fat=0,
                    fiber=0,
                    sugar=0,
                    sodium=0
                )
                db.session.add(ingredient)
            
            # Add instructions
            for i, instruction_text in enumerate(recipe_data['instructions'], 1):
                instruction = RecipeInstruction(
                    recipe_id=recipe.id,
                    step_number=i,
                    instruction=instruction_text
                )
                db.session.add(instruction)
            
            db.session.commit()
            self.imported_count += 1
            print(f"✅ Imported: {recipe_data['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating recipe {recipe_data['name']}: {e}")
            db.session.rollback()
            self.failed_count += 1
            return False
    
    def import_recipes(self, max_recipes=50, skip_errors=True, continue_on_error=True):
        """Main import function with enhanced error handling"""
        print("🚀 Starting recipe import from textonlyrecipes.com...")
        print(f"⚙️  Settings: Skip errors={skip_errors}, Continue on error={continue_on_error}")
        
        # Get admin user
        admin_user = User.query.filter_by(email='admin@kiwellness.org').first()
        if not admin_user:
            print("❌ Admin user not found. Please create an admin user first.")
            return
        
        # Get recipe links
        recipe_links = self.get_recipe_links()
        if not recipe_links:
            print("❌ No recipe links found.")
            return
        
        # Limit the number of recipes to import
        recipe_links = recipe_links[:max_recipes]
        
        print(f"📋 Importing {len(recipe_links)} recipes...")
        
        failed_recipes = []
        
        for i, recipe_link in enumerate(recipe_links, 1):
            print(f"\n[{i}/{len(recipe_links)}] Processing: {recipe_link['name']}")
            
            try:
                # Scrape recipe data
                recipe_data = self.scrape_recipe(recipe_link['url'], recipe_link['name'])
                
                if recipe_data:
                    # Create recipe in database
                    success = self.create_recipe_in_db(recipe_data, admin_user)
                    if not success:
                        failed_recipes.append({
                            'name': recipe_link['name'],
                            'url': recipe_link['url'],
                            'error': 'Database creation failed'
                        })
                else:
                    failed_recipes.append({
                        'name': recipe_link['name'],
                        'url': recipe_link['url'],
                        'error': 'Failed to scrape recipe data'
                    })
                    
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                print(f"❌ Error processing {recipe_link['name']}: {error_msg}")
                
                failed_recipes.append({
                    'name': recipe_link['name'],
                    'url': recipe_link['url'],
                    'error': error_msg
                })
                
                if not continue_on_error:
                    print("🛑 Stopping import due to error (continue_on_error=False)")
                    break
            
            # Be respectful - add delay between requests
            time.sleep(1)
        
        # Print summary
        print(f"\n🎉 Import completed!")
        print(f"✅ Successfully imported: {self.imported_count} recipes")
        print(f"❌ Failed imports: {len(failed_recipes)} recipes")
        
        # Show failed recipes if any
        if failed_recipes:
            print(f"\n📋 Failed Recipes:")
            for failed in failed_recipes:
                print(f"  • {failed['name']}: {failed['error']}")
            
            if skip_errors:
                print(f"\n💡 Tip: Failed recipes were skipped and import continued.")
            else:
                print(f"\n⚠️  Some recipes failed but import continued.")
        
        return {
            'imported': self.imported_count,
            'failed': len(failed_recipes),
            'failed_recipes': failed_recipes
        }

def test_ingredient_parsing():
    """Test function to show what ingredient formats the script can handle"""
    print("🧪 Testing ingredient parsing capabilities...")
    
    importer = TextOnlyRecipeImporter()
    
    test_ingredients = [
        "2 cups all-purpose flour",
        "1/2 cup sugar",
        "1 1/2 teaspoons baking powder",
        "3 large eggs",
        "1 lb ground beef",
        "2-3 tablespoons olive oil",
        "1/4 to 1/2 cup milk",
        "1 pinch salt",
        "1 dash pepper",
        "1 can (14 oz) diced tomatoes",
        "2 cloves garlic, minced",
        "1 large onion, diced",
        "flour 2 cups",
        "salt to taste",
        "1 package (8 oz) cream cheese"
    ]
    
    print("\n📋 Test Results:")
    for ingredient in test_ingredients:
        result = importer.parse_ingredient_line(ingredient)
        print(f"  '{ingredient}' → {result['amount']} {result['unit']} {result['food_name']}")
    
    print("\n✅ Parsing test completed!")

def main():
    """Main function"""
    load_dotenv()
    
    # Initialize environment detector
    env_detector = get_environment_detector()
    print(f"Environment: {'Production' if env_detector.is_production else 'Development'}")
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Test ingredient parsing")
    print("2. Import recipes from textonlyrecipes.com")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_ingredient_parsing()
        return
    
    # Import Flask app to get database context
    from app import app
    
    with app.app_context():
        importer = TextOnlyRecipeImporter()
        
        # Ask user for import settings
        try:
            max_recipes = int(input("How many recipes would you like to import? (default: 20): ") or "20")
        except ValueError:
            max_recipes = 20
        
        # Ask about error handling
        skip_errors_input = input("Skip recipes with errors and continue? (y/N): ").strip().lower()
        skip_errors = skip_errors_input in ['y', 'yes']
        
        continue_on_error_input = input("Continue importing if errors occur? (Y/n): ").strip().lower()
        continue_on_error = continue_on_error_input not in ['n', 'no']
        
        print(f"\n⚙️  Import Settings:")
        print(f"   • Max recipes: {max_recipes}")
        print(f"   • Skip errors: {skip_errors}")
        print(f"   • Continue on error: {continue_on_error}")
        
        confirm = input("\nProceed with import? (Y/n): ").strip().lower()
        if confirm in ['n', 'no']:
            print("Import cancelled.")
            return
        
        # Run the import
        result = importer.import_recipes(
            max_recipes=max_recipes,
            skip_errors=skip_errors,
            continue_on_error=continue_on_error
        )
        
        # Show final summary
        if result:
            print(f"\n📊 Final Summary:")
            print(f"   ✅ Successfully imported: {result['imported']} recipes")
            print(f"   ❌ Failed: {result['failed']} recipes")
            
            if result['failed'] > 0:
                print(f"\n💡 You can run the script again to retry failed recipes.")

if __name__ == '__main__':
    main()
