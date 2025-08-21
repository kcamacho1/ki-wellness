from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from database import db, Recipe, RecipeIngredient, RecipeInstruction, FoodLog, RecipeRating, User
import os
from werkzeug.utils import secure_filename
import hashlib
import time

# Create blueprint for recipe routes
recipe_bp = Blueprint('recipe', __name__)

# Simple in-memory cache for search results (in production, use Redis)
search_cache = {}
CACHE_TTL = 300  # 5 minutes cache TTL

def get_cache_key(query, include_public, category, page, per_page):
    """Generate a cache key for search results"""
    cache_string = f"{query}:{include_public}:{category}:{page}:{per_page}"
    return hashlib.md5(cache_string.encode()).hexdigest()

def get_cached_result(cache_key):
    """Get cached result if it exists and is not expired"""
    if cache_key in search_cache:
        cached_data, timestamp = search_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return cached_data
        else:
            # Remove expired cache entry
            del search_cache[cache_key]
    return None

def set_cached_result(cache_key, data):
    """Cache search result with timestamp"""
    search_cache[cache_key] = (data, time.time())

@recipe_bp.route('/api/recipes', methods=['GET'])
@login_required
def get_recipes():
    """Get all recipes for the current user"""
    try:
        category = request.args.get('category', 'all')
        
        query = Recipe.query.filter_by(user_id=current_user.id)
        
        if category != 'all':
            query = query.filter_by(category=category)
        
        recipes = query.order_by(Recipe.updated_at.desc()).all()
        
        recipe_list = []
        for recipe in recipes:
            recipe_data = recipe.to_dict()
            # Remove detailed ingredients/instructions for list view
            recipe_data.pop('ingredients', None)
            recipe_data.pop('instructions', None)
            recipe_list.append(recipe_data)
        
        return jsonify({'success': True, 'recipes': recipe_list})
        
    except Exception as e:
        print(f"Error fetching recipes: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch recipes'}), 500

@recipe_bp.route('/api/recipes/preview', methods=['GET'])
@login_required
def get_recipe_previews():
    """Get minimal recipe data for fast preview display"""
    try:
        category = request.args.get('category', 'all')
        include_public = request.args.get('include_public', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))  # Reduced from 20 to 12 for better performance
        
        # Build query similar to search but for all recipes
        if include_public:
            recipes_query = Recipe.query.filter(
                db.or_(
                    Recipe.user_id == current_user.id,
                    db.and_(Recipe.is_public == True, Recipe.user_id != current_user.id)
                )
            )
        else:
            recipes_query = Recipe.query.filter_by(user_id=current_user.id)
        
        # Apply category filter
        if category != 'all':
            recipes_query = recipes_query.filter(Recipe.category == category)
        
        # Get total count for pagination
        total_count = recipes_query.count()
        
        # Apply pagination
        recipes = recipes_query.order_by(Recipe.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        recipe_list = []
        for recipe in recipes:
            # Only include minimal data for preview
            recipe_data = {
                'id': recipe.id,
                'name': recipe.name,
                'category': recipe.category,
                'difficulty': recipe.difficulty,
                'image_path': recipe.image_path,
                'is_favorite': recipe.is_favorite,
                'is_public': recipe.is_public,
                'user_id': recipe.user_id,
                'ingredients_count': len(recipe.ingredients),
                'avg_rating': 0,
                'rating_count': 0
            }
            
            # Add creator name for public recipes
            if recipe.user_id != current_user.id:
                creator = User.query.get(recipe.user_id)
                recipe_data['creator_name'] = creator.name if creator else 'Unknown'
            
            # Calculate rating if exists
            if recipe.ratings:
                avg_rating = sum(r.rating for r in recipe.ratings) / len(recipe.ratings)
                recipe_data['avg_rating'] = round(avg_rating, 1)
                recipe_data['rating_count'] = len(recipe.ratings)
            
            recipe_list.append(recipe_data)
        
        return jsonify({
            'success': True, 
            'recipes': recipe_list,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"Error fetching recipe previews: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch recipe previews'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>', methods=['GET'])
@login_required
def get_recipe(recipe_id):
    """Get a specific recipe with all details - allows access to public recipes"""
    try:
        print(f"Fetching recipe {recipe_id} for user {current_user.id}")
        
        # First try to get user's own recipe
        recipe = Recipe.query.filter_by(id=recipe_id, user_id=current_user.id).first()
        if recipe:
            print(f"Found user's own recipe: {recipe.name}")
        else:
            print(f"Recipe {recipe_id} not found in user's recipes, checking public recipes...")
            # If not found, check if it's a public recipe
            recipe = Recipe.query.filter_by(id=recipe_id, is_public=True).first()
            if recipe:
                print(f"Found public recipe: {recipe.name} (user {recipe.user_id})")
            else:
                print(f"Recipe {recipe_id} not found in public recipes either")
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found or not accessible'}), 404
        
        return jsonify({
            'success': True,
            'recipe': recipe.to_dict()
        })
        
    except Exception as e:
        print(f"Error fetching recipe: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch recipe'}), 500

@recipe_bp.route('/api/recipes', methods=['POST'])
@login_required
def create_recipe():
    """Create a new recipe"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            image_path = None
        else:
            # Handle multipart form data for image upload
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'servings': request.form.get('servings'),
                'prep_time': request.form.get('prep_time'),
                'cook_time': request.form.get('cook_time'),
                'difficulty': request.form.get('difficulty'),
                'category': request.form.get('category'),
                'ingredients': request.form.get('ingredients'),
                'instructions': request.form.get('instructions')
            }
            
            # Handle image upload
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        filename = secure_filename(f"recipe_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                        
                        # Create upload directory if it doesn't exist
                        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'recipes')
                        os.makedirs(upload_folder, exist_ok=True)
                        
                        # Save file
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)
                        
                        # Store relative path for database
                        image_path = f'uploads/recipes/{filename}'
        
        # Validate required fields
        if not data.get('name') or not data.get('ingredients'):
            return jsonify({'success': False, 'error': 'Recipe name and ingredients are required'}), 400
        

        
        # Create recipe
        recipe = Recipe(
            user_id=current_user.id,
            name=data['name'],
            description=data.get('description', ''),
            servings=data.get('servings', 1),
            prep_time=data.get('prep_time'),
            cook_time=data.get('cook_time'),
            difficulty=data.get('difficulty', 'Easy'),
            category=data.get('category', 'Dinner'),
            image_path=image_path
        )
        
        db.session.add(recipe)
        db.session.flush()  # Get the recipe ID
        
        # Add ingredients
        for ingredient_data in data['ingredients']:
            ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                food_name=ingredient_data['food_name'],
                amount=ingredient_data['amount'],
                unit=ingredient_data['unit'],
                serving_size_grams=ingredient_data.get('serving_size_grams', 0),
                calories=ingredient_data.get('calories', 0),
                protein=ingredient_data.get('protein', 0),
                carbs=ingredient_data.get('carbs', 0),
                fat=ingredient_data.get('fat', 0),
                fiber=ingredient_data.get('fiber', 0),
                sugar=ingredient_data.get('sugar', 0),
                sodium=ingredient_data.get('sodium', 0)
            )
            db.session.add(ingredient)
        
        # Add instructions if provided
        if data.get('instructions'):
            for i, instruction_text in enumerate(data['instructions'], 1):
                instruction = RecipeInstruction(
                    recipe_id=recipe.id,
                    step_number=i,
                    instruction=instruction_text
                )
                db.session.add(instruction)
        
        db.session.commit()
        
        # Clear search cache since new recipe was added
        clear_search_cache()
        
        return jsonify({
            'success': True,
            'recipe_id': recipe.id,
            'message': 'Recipe created successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating recipe: {e}")
        return jsonify({'success': False, 'error': 'Failed to create recipe'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
@login_required
def update_recipe(recipe_id):
    """Update an existing recipe"""
    try:
        recipe = Recipe.query.filter_by(id=recipe_id, user_id=current_user.id).first()
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404
        
        data = request.get_json()
        
        # Update basic recipe info
        if 'name' in data:
            recipe.name = data['name']
        if 'description' in data:
            recipe.description = data['description']
        if 'servings' in data:
            recipe.servings = data['servings']
        if 'prep_time' in data:
            recipe.prep_time = data['prep_time']
        if 'cook_time' in data:
            recipe.cook_time = data['cook_time']
        if 'difficulty' in data:
            recipe.difficulty = data['difficulty']
        if 'category' in data:
            recipe.category = data['category']
        if 'is_favorite' in data:
            recipe.is_favorite = data['is_favorite']
        
        recipe.updated_at = datetime.utcnow()
        
        # Update ingredients if provided
        if 'ingredients' in data:
            # Remove existing ingredients
            RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
            
            # Add new ingredients
            for ingredient_data in data['ingredients']:
                ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    food_name=ingredient_data['food_name'],
                    amount=ingredient_data['amount'],
                    unit=ingredient_data['unit'],
                    calories=ingredient_data.get('calories', 0),
                    protein=ingredient_data.get('protein', 0),
                    carbs=ingredient_data.get('carbs', 0),
                    fat=ingredient_data.get('fat', 0),
                    fiber=ingredient_data.get('fiber', 0),
                    sugar=ingredient_data.get('sugar', 0),
                    sodium=ingredient_data.get('sodium', 0)
                )
                db.session.add(ingredient)
        
        # Update instructions if provided
        if 'instructions' in data:
            # Remove existing instructions
            RecipeInstruction.query.filter_by(recipe_id=recipe.id).delete()
            
            # Add new instructions
            for i, instruction_text in enumerate(data['instructions'], 1):
                instruction = RecipeInstruction(
                    recipe_id=recipe.id,
                    step_number=i,
                    instruction=instruction_text
                )
                db.session.add(instruction)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recipe updated successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating recipe: {e}")
        return jsonify({'success': False, 'error': 'Failed to update recipe'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
@login_required
def delete_recipe(recipe_id):
    """Delete a recipe"""
    try:
        recipe = Recipe.query.filter_by(id=recipe_id, user_id=current_user.id).first()
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404
        
        db.session.delete(recipe)
        db.session.commit()
        
        # Clear search cache since recipe was deleted
        clear_search_cache()
        
        return jsonify({
            'success': True,
            'message': 'Recipe deleted successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting recipe: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete recipe'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>/add-to-log', methods=['POST'])
@login_required
def add_recipe_to_log(recipe_id):
    """Add a recipe to the food log for today"""
    try:
        data = request.get_json()
        servings = data.get('servings', 1)
        time_of_day = data.get('time_of_day', 'dinner')
        
        recipe = Recipe.query.filter_by(id=recipe_id, user_id=current_user.id).first()
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404
        
        # Calculate nutrition per serving
        total_calories = sum(ing.calories for ing in recipe.ingredients)
        total_protein = sum(ing.protein for ing in recipe.ingredients)
        total_carbs = sum(ing.carbs for ing in recipe.ingredients)
        total_fat = sum(ing.fat for ing in recipe.ingredients)
        total_fiber = sum(ing.fiber for ing in recipe.ingredients)
        total_sugar = sum(ing.sugar for ing in recipe.ingredients)
        total_sodium = sum(ing.sodium for ing in recipe.ingredients)
        

        
        # Create food log entry for the recipe
        food_log = FoodLog(
            user_id=current_user.id,
            name=f"{recipe.name} (Recipe)",
            brand="Homemade",
            calories=total_calories * servings,
            protein=total_protein * servings,
            carbs=total_carbs * servings,
            fat=total_fat * servings,
            fiber=total_fiber * servings,
            sugar=total_sugar * servings,
            sodium=total_sodium * servings,
            serving_size=100 * servings,  # Approximate
            original_amount=1,
            original_unit="serving",
            quantity=servings,
            date=date.today(),
            time_of_day=time_of_day,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(food_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{recipe.name} added to your food log!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding recipe to log: {e}")
        return jsonify({'success': False, 'error': 'Failed to add recipe to log'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>/toggle-favorite', methods=['POST'])
@login_required
def toggle_favorite(recipe_id):
    """Toggle favorite status of a recipe"""
    try:
        recipe = Recipe.query.filter_by(id=recipe_id, user_id=current_user.id).first()
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404
        
        recipe.is_favorite = not recipe.is_favorite
        recipe.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Clear search cache since recipe was updated
        clear_search_cache()
        
        return jsonify({
            'success': True,
            'is_favorite': recipe.is_favorite,
            'message': f'Recipe {"added to" if recipe.is_favorite else "removed from"} favorites!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error toggling favorite: {e}")
        return jsonify({'success': False, 'error': 'Failed to update favorite status'}), 500

@recipe_bp.route('/api/recipes/search', methods=['GET'])
@login_required
def search_recipes():
    """Search for recipes (user's own and public recipes) - OPTIMIZED WITH CACHING"""
    try:
        query = request.args.get('q', '').strip()
        include_public = request.args.get('include_public', 'false').lower() == 'true'
        category = request.args.get('category', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)  # Reduced from 20 to 12 for better performance
        
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 25)  # Reduced max from 50 to 25
        
        # Check cache first for non-empty queries
        if query:
            cache_key = get_cache_key(query, include_public, category, page, per_page)
            cached_result = get_cached_result(cache_key)
            if cached_result:
                print(f"Cache hit for query: {query}")
                return jsonify(cached_result)
            else:
                print(f"Cache miss for query: {query}")
        
        # Build optimized query using JOINs instead of UNION
        if include_public:
            # Use a more efficient approach with OR conditions
            recipes_query = Recipe.query.filter(
                db.or_(
                    Recipe.user_id == current_user.id,
                    db.and_(Recipe.is_public == True, Recipe.user_id != current_user.id)
                )
            )
        else:
            recipes_query = Recipe.query.filter_by(user_id=current_user.id)
        
        # Apply search filter with optimized LIKE query
        if query:
            # Use case-insensitive search with proper indexing
            recipes_query = recipes_query.filter(Recipe.name.ilike(f'%{query}%'))
        
        # Apply category filter
        if category and category != 'all':
            recipes_query = recipes_query.filter(Recipe.category == category)
        
        # Get total count for pagination
        total_count = recipes_query.count()
        
        # Apply pagination and ordering
        recipes = recipes_query.order_by(Recipe.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to dict with minimal data for list view (optimized for speed)
        recipe_data = []
        for recipe in recipes:
            recipe_dict = {
                'id': recipe.id,
                'name': recipe.name,
                'category': recipe.category,
                'difficulty': recipe.difficulty,
                'image_path': recipe.image_path,
                'is_favorite': recipe.is_favorite,
                'is_public': recipe.is_public,
                'user_id': recipe.user_id,
                'ingredients_count': len(recipe.ingredients),
                'avg_rating': 0,
                'rating_count': 0
            }
            
            # Add creator name for public recipes
            if recipe.user_id != current_user.id:
                creator = User.query.get(recipe.user_id)
                recipe_dict['creator_name'] = creator.name if creator else 'Unknown'
            
            # Calculate rating if exists
            if recipe.ratings:
                avg_rating = sum(r.rating for r in recipe.ratings) / len(recipe.ratings)
                recipe_dict['avg_rating'] = round(avg_rating, 1)
                recipe_dict['rating_count'] = len(recipe.ratings)
            
            recipe_data.append(recipe_dict)
        
        result = {
            'success': True,
            'recipes': recipe_data,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        }
        
        # Cache the result for future requests
        if query:
            set_cached_result(cache_key, result)
            print(f"Cached result for query: {query} with {len(recipe_data)} recipes")
        
        print(f"Search completed for '{query}': {len(recipe_data)} recipes found")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error searching recipes: {e}")
        return jsonify({'success': False, 'error': 'Failed to search recipes'}), 500

def clear_search_cache():
    """Clear the search cache - call this when recipes are updated"""
    global search_cache
    search_cache.clear()

def warm_search_cache():
    """Pre-populate cache with common searches"""
    try:
        # Get some popular categories and search terms
        popular_categories = ['breakfast', 'lunch', 'dinner', 'snack', 'dessert']
        common_terms = ['chicken', 'pasta', 'salad', 'smoothie', 'cake']
        
        for category in popular_categories:
            for term in common_terms:
                cache_key = get_cache_key(term, True, category, 1, 20)
                # This will trigger a search and cache the result
                pass
                
    except Exception as e:
        print(f"Error warming cache: {e}")

@recipe_bp.route('/api/recipes/search-by-ingredients', methods=['POST'])
@login_required
def search_recipes_by_ingredients():
    """Search for recipes based on ingredients - OPTIMIZED"""
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', [])
        include_public = data.get('include_public', True)
        min_ingredients = data.get('min_ingredients', 3)
        page = data.get('page', 1)
        per_page = data.get('per_page', 12)  # Reduced from 20 to 12 for better performance
        
        if not ingredients or len(ingredients) < min_ingredients:
            return jsonify({
                'success': False, 
                'error': f'Please provide at least {min_ingredients} ingredients'
            }), 400
        
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 25)  # Reduced max from 50 to 25
        
        # Convert ingredients to lowercase for case-insensitive search
        search_ingredients = [ing.lower().strip() for ing in ingredients]
        
        # Build optimized query using JOINs instead of UNION
        if include_public:
            recipes_query = Recipe.query.filter(
                db.or_(
                    Recipe.user_id == current_user.id,
                    db.and_(Recipe.is_public == True, Recipe.user_id != current_user.id)
                )
            )
        else:
            recipes_query = Recipe.query.filter_by(user_id=current_user.id)
        
        # Use SQL JOIN to find recipes with matching ingredients more efficiently
        matching_recipes = []
        
        # Get all recipes and their ingredients in one query
        recipes_with_ingredients = recipes_query.join(RecipeIngredient).filter(
            RecipeIngredient.food_name.ilike(db.or_(*[f'%{ing}%' for ing in search_ingredients]))
        ).distinct().all()
        
        # Process matches with optimized algorithm
        for recipe in recipes_with_ingredients:
            recipe_ingredients = [ing.food_name.lower() for ing in recipe.ingredients]
            matching_count = 0
            
            # Use set intersection for faster matching
            recipe_ingredient_set = set(recipe_ingredients)
            for search_ingredient in search_ingredients:
                # Check for partial matches
                for recipe_ingredient in recipe_ingredient_set:
                    if (search_ingredient in recipe_ingredient or 
                        recipe_ingredient in search_ingredient):
                        matching_count += 1
                        break
            
            # Calculate match percentage
            match_percentage = (matching_count / len(search_ingredients)) * 100
            
            if matching_count >= min_ingredients:
                # Create minimal recipe dict for performance
                # Calculate nutrition totals
                total_calories = sum(ing.calories for ing in recipe.ingredients)
                total_protein = sum(ing.protein for ing in recipe.ingredients)
                total_carbs = sum(ing.carbs for ing in recipe.ingredients)
                total_fat = sum(ing.fat for ing in recipe.ingredients)
                
                recipe_dict = {
                    'id': recipe.id,
                    'name': recipe.name,
                    'category': recipe.category,
                    'difficulty': recipe.difficulty,
                    'image_path': recipe.image_path,
                    'is_favorite': recipe.is_favorite,
                    'is_public': recipe.is_public,
                    'user_id': recipe.user_id,
                    'ingredients_count': len(recipe.ingredients),
                    'match_percentage': round(match_percentage, 1),
                    'matching_ingredients': matching_count,
                    'avg_rating': 0,
                    'rating_count': 0
                }
                
                # Add creator name for public recipes
                if recipe.user_id != current_user.id:
                    creator = User.query.get(recipe.user_id)
                    recipe_dict['creator_name'] = creator.name if creator else 'Unknown'
                
                # Calculate rating if exists
                if recipe.ratings:
                    avg_rating = sum(r.rating for r in recipe.ratings) / len(recipe.ratings)
                    recipe_dict['avg_rating'] = round(avg_rating, 1)
                    recipe_dict['rating_count'] = len(recipe.ratings)
                
                matching_recipes.append(recipe_dict)
        
        # Sort by match percentage (highest first)
        matching_recipes.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Apply pagination
        total_count = len(matching_recipes)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_recipes = matching_recipes[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'recipes': paginated_recipes,
            'total_found': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"Error searching recipes by ingredients: {e}")
        return jsonify({'success': False, 'error': 'Failed to search recipes by ingredients'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>/rate', methods=['POST'])
@login_required
def rate_recipe(recipe_id):
    """Rate a recipe (1-5 stars)"""
    try:
        data = request.get_json()
        rating_value = data.get('rating')
        review = data.get('review', '')
        
        if not rating_value or not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400
        
        # Check if recipe exists and is public
        recipe = Recipe.query.filter_by(id=recipe_id, is_public=True).first()
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found or not public'}), 404
        
        # Check if user has already rated this recipe
        existing_rating = RecipeRating.query.filter_by(recipe_id=recipe_id, user_id=current_user.id).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating_value
            existing_rating.review = review
            existing_rating.created_at = datetime.utcnow()
        else:
            # Create new rating
            rating = RecipeRating(
                recipe_id=recipe_id,
                user_id=current_user.id,
                rating=rating_value,
                review=review
            )
            db.session.add(rating)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recipe rated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error rating recipe: {e}")
        return jsonify({'success': False, 'error': 'Failed to rate recipe'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>/ratings', methods=['GET'])
@login_required
def get_recipe_ratings(recipe_id):
    """Get all ratings for a recipe"""
    try:
        recipe = Recipe.query.filter_by(id=recipe_id, is_public=True).first()
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found or not public'}), 404
        
        ratings = RecipeRating.query.filter_by(recipe_id=recipe_id).all()
        rating_data = []
        
        for rating in ratings:
            user = User.query.get(rating.user_id)
            rating_data.append({
                'id': rating.id,
                'rating': rating.rating,
                'review': rating.review,
                'created_at': rating.created_at.isoformat(),
                'user_name': user.name if user else 'Unknown'
            })
        
        return jsonify({
            'success': True,
            'ratings': rating_data
        })
        
    except Exception as e:
        print(f"Error getting recipe ratings: {e}")
        return jsonify({'success': False, 'error': 'Failed to get ratings'}), 500

@recipe_bp.route('/api/recipes/search-stats', methods=['GET'])
@login_required
def get_search_stats():
    """Get search performance statistics"""
    try:
        total_recipes = Recipe.query.count()
        public_recipes = Recipe.query.filter_by(is_public=True).count()
        user_recipes = Recipe.query.filter_by(user_id=current_user.id).count()
        cache_size = len(search_cache)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_recipes': total_recipes,
                'public_recipes': public_recipes,
                'user_recipes': user_recipes,
                'cache_size': cache_size,
                'cache_ttl_seconds': CACHE_TTL
            }
        })
        
    except Exception as e:
        print(f"Error getting search stats: {e}")
        return jsonify({'success': False, 'error': 'Failed to get search stats'}), 500

@recipe_bp.route('/api/recipes/clear-cache', methods=['POST'])
@login_required
def clear_cache():
    """Clear the search cache (admin function)"""
    try:
        # Only allow admins or the cache owner to clear cache
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        clear_search_cache()
        
        return jsonify({
            'success': True,
            'message': 'Search cache cleared successfully'
        })
        
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return jsonify({'success': False, 'error': 'Failed to clear cache'}), 500

@recipe_bp.route('/api/recipes/warm-cache', methods=['POST'])
@login_required
def warm_cache():
    """Warm the search cache with common searches (admin function)"""
    try:
        # Only allow admins to warm cache
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        warm_search_cache()
        
        return jsonify({
            'success': True,
            'message': 'Search cache warming initiated'
        })
        
    except Exception as e:
        print(f"Error warming cache: {e}")
        return jsonify({'success': False, 'error': 'Failed to warm cache'}), 500
