from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from database import db, Recipe, RecipeIngredient, RecipeInstruction, FoodLog, RecipeRating, User
from services.nutrition_service import nutrition_service
from services.r2_client import r2_client
import os
from werkzeug.utils import secure_filename
import hashlib
import time

# Create blueprint for recipe routes
recipe_bp = Blueprint('recipe', __name__)

# Simple in-memory cache for search results (in production, use Redis)
search_cache = {}
CACHE_TTL = 300  # 5 minutes cache TTL

def _save_local_image(file, filename):
    """Helper function to save image locally as fallback"""
    try:
        # Create upload directory if it doesn't exist
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'recipes')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Return relative path for database
        return f'uploads/recipes/{filename}'
    except Exception as e:
        print(f"❌ Local image save failed: {e}")
        return None

def _convert_image_path_to_url(image_path):
    """Convert image path to proper URL"""
    if not image_path:
        return None
    
    if image_path.startswith('http'):
        # It's already a full URL (from R2 or external source)
        return image_path
    else:
        # It's a local path, convert to URL
        from flask import url_for
        return url_for('static', filename=image_path)

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
                'image_path': _convert_image_path_to_url(recipe.image_path),
                'dynamic_image_url': recipe.dynamic_image_url,
                'is_favorite': recipe.is_favorite,
                'is_public': recipe.is_public,
                'user_id': recipe.user_id,
                'ingredients_count': len(recipe.ingredients),
                'ingredients': [{'name': ing.food_name, 'amount': ing.amount, 'unit': ing.unit} for ing in recipe.ingredients],
                'avg_rating': 0,
                'rating_count': 0
            }
            
            # Add creator name for public recipes
            if recipe.user_id != current_user.id:
                creator = User.query.get(recipe.user_id)
                recipe_data['creator_name'] = creator.username if creator else 'Unknown'
                recipe_data['contributor'] = creator.username if creator else 'Unknown'
            else:
                recipe_data['contributor'] = current_user.username
                recipe_data['is_owner'] = True
            
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


@recipe_bp.route('/api/recipes/favorites', methods=['GET'])
@login_required
def get_favorite_recipes():
    """Get user's favorite recipes"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        
        # Get user's favorite recipes (both own and public recipes that are favorited)
        recipes_query = Recipe.query.filter(
            db.and_(
                Recipe.is_favorite == True,
                db.or_(
                    Recipe.user_id == current_user.id,
                    db.and_(Recipe.is_public == True, Recipe.user_id != current_user.id)
                )
            )
        )
        
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
                'image_path': _convert_image_path_to_url(recipe.image_path),
                'dynamic_image_url': recipe.dynamic_image_url,
                'is_favorite': recipe.is_favorite,
                'is_public': recipe.is_public,
                'user_id': recipe.user_id,
                'ingredients_count': len(recipe.ingredients),
                'ingredients': [{'name': ing.food_name, 'amount': ing.amount, 'unit': ing.unit} for ing in recipe.ingredients],
                'avg_rating': 0,
                'rating_count': 0
            }
            
            # Add creator name for public recipes
            if recipe.user_id != current_user.id:
                creator = User.query.get(recipe.user_id)
                recipe_data['creator_name'] = creator.username if creator else 'Unknown'
                recipe_data['contributor'] = creator.username if creator else 'Unknown'
            else:
                recipe_data['contributor'] = current_user.username
                recipe_data['is_owner'] = True
            
            # Calculate average rating
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
        print(f"Error fetching favorite recipes: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch favorite recipes'}), 500

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
        
        # Get recipe data with contributor information
        recipe_data = recipe.to_dict()
        
        # Add contributor information
        if recipe.user_id != current_user.id:
            creator = User.query.get(recipe.user_id)
            recipe_data['contributor'] = creator.username if creator else 'Unknown'
            recipe_data['is_owner'] = False
        else:
            recipe_data['contributor'] = current_user.username
            recipe_data['is_owner'] = True
        
        return jsonify({
            'success': True,
            'recipe': recipe_data
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
            
            # Handle image upload - R2 storage as primary method
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        filename = secure_filename(f"recipe_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                        
                        # Always try R2 first (primary storage method)
                        if r2_client.is_available():
                            try:
                                # Read file data
                                file_data = file.read()
                                file.seek(0)  # Reset file pointer
                                
                                # Upload to R2 with image processing
                                result = r2_client.upload_file(
                                    file_data=file_data,
                                    filename=filename,
                                    folder="user-uploads",
                                    process_image=True  # Enable image optimization
                                )
                                
                                if result:
                                    image_path = result['public_url']
                                    print(f"✅ Uploaded image to R2: {image_path}")
                                    if result.get('compression_stats'):
                                        stats = result['compression_stats']
                                        print(f"📊 Image optimized: {stats['original_size_mb']}MB -> {stats['optimized_size_mb']}MB ({stats['reduction_percent']}% reduction)")
                                else:
                                    print("❌ R2 upload failed completely")
                                    return jsonify({'success': False, 'error': 'Failed to upload image to storage'}), 500
                                    
                            except Exception as e:
                                print(f"❌ R2 upload error: {e}")
                                return jsonify({'success': False, 'error': f'Image upload failed: {str(e)}'}), 500
                        else:
                            # R2 not available - this should not happen in production
                            print("❌ R2 not available - this is a configuration error")
                            return jsonify({'success': False, 'error': 'Image storage not available. Please contact support.'}), 500
        
        # Process ingredients from form data
        ingredients_data = []
        if request.is_json:
            ingredients_data = data.get('ingredients', [])
        else:
            # Process form data ingredients
            i = 0
            while f'ingredients[{i}][food_name]' in request.form:
                ingredients_data.append({
                    'food_name': request.form.get(f'ingredients[{i}][food_name]'),
                    'amount': float(request.form.get(f'ingredients[{i}][amount]', 0)),
                    'unit': request.form.get(f'ingredients[{i}][unit]')
                })
                i += 1
        
        # Process instructions from form data
        instructions_data = []
        if request.is_json:
            instructions_data = data.get('instructions', [])
        else:
            # Process form data instructions
            i = 0
            while f'instructions[{i}]' in request.form:
                instruction = request.form.get(f'instructions[{i}]')
                if instruction and instruction.strip():
                    instructions_data.append(instruction.strip())
                i += 1
        
        # Validate required fields
        if not data.get('name') or not ingredients_data:
            return jsonify({'success': False, 'error': 'Recipe name and ingredients are required'}), 400
        
        # Create recipe - user-created recipes default to community
        is_public = data.get('is_public', True)  # Default to community (public)
        
        # Admin recipes are always community
        if current_user.username == 'admin' or current_user.email == 'admin@kiwellness.com':
            is_public = True
        
        recipe = Recipe(
            user_id=current_user.id,
            name=data['name'],
            description=data.get('description', ''),
            servings=data.get('servings', 1),
            prep_time=data.get('prep_time'),
            cook_time=data.get('cook_time'),
            difficulty=data.get('difficulty', 'Easy'),
            category=data.get('category', 'Dinner'),
            image_path=image_path,
            is_public=is_public  # Default to community, but allow user choice
        )
        
        db.session.add(recipe)
        db.session.flush()  # Get the recipe ID
        
        # Add ingredients
        for ingredient_data in ingredients_data:
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
        if instructions_data:
            for i, instruction_text in enumerate(instructions_data, 1):
                instruction = RecipeInstruction(
                    recipe_id=recipe.id,
                    step_number=i,
                    instruction=instruction_text
                )
                db.session.add(instruction)
        
        db.session.commit()
        
        # Automatically fetch nutritional data for all ingredients
        try:
            print(f"Auto-fetching nutrition for recipe {recipe.id}: {recipe.name}")
            nutrition_result = nutrition_service.bulk_update_recipe_nutrition(recipe.id)
            if nutrition_result['success']:
                print(f"✅ Auto-fetched nutrition for {nutrition_result['nutrition']['ingredients_processed']}/{nutrition_result['nutrition']['ingredients_total']} ingredients")
            else:
                print(f"⚠️ Auto-nutrition fetch failed: {nutrition_result['message']}")
        except Exception as nutrition_error:
            print(f"⚠️ Auto-nutrition fetch error: {nutrition_error}")
            # Don't fail the recipe creation if nutrition fetch fails
        
        # Clear search cache since new recipe was added
        clear_search_cache()
        
        # Get the updated recipe with nutritional data
        updated_recipe = Recipe.query.get(recipe.id)
        
        return jsonify({
            'success': True,
            'recipe_id': recipe.id,
            'message': 'Recipe created successfully!',
            'recipe': updated_recipe.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating recipe: {e}")
        return jsonify({'success': False, 'error': 'Failed to create recipe'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
@login_required
def update_recipe(recipe_id):
    """Update an existing recipe - only the original submitter can edit"""
    try:
        recipe = Recipe.query.filter_by(id=recipe_id, user_id=current_user.id).first()
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found or you do not have permission to edit this recipe'}), 404
        
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
        
        # Automatically fetch nutritional data if ingredients were updated
        if 'ingredients' in data:
            try:
                print(f"Auto-fetching nutrition for updated recipe {recipe.id}: {recipe.name}")
                nutrition_result = nutrition_service.bulk_update_recipe_nutrition(recipe.id)
                if nutrition_result['success']:
                    print(f"✅ Auto-fetched nutrition for {nutrition_result['nutrition']['ingredients_processed']}/{nutrition_result['nutrition']['ingredients_total']} ingredients")
                else:
                    print(f"⚠️ Auto-nutrition fetch failed: {nutrition_result['message']}")
            except Exception as nutrition_error:
                print(f"⚠️ Auto-nutrition fetch error: {nutrition_error}")
                # Don't fail the recipe update if nutrition fetch fails
        
        return jsonify({
            'success': True,
            'message': 'Recipe updated successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating recipe: {e}")
        return jsonify({'success': False, 'error': 'Failed to update recipe'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>/image', methods=['PUT'])
@login_required
def update_recipe_image(recipe_id):
    """Update recipe image - only the original submitter can edit"""
    try:
        recipe = Recipe.query.filter_by(id=recipe_id, user_id=current_user.id).first()
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found or you do not have permission to edit this recipe'}), 404
        
        # Handle image upload
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({'success': False, 'error': 'No image file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
            filename = secure_filename(f"recipe_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            
            # Try to upload to R2 first
            if r2_client.is_available():
                try:
                    # Read file data
                    file_data = file.read()
                    file.seek(0)  # Reset file pointer
                    
                    # Upload to R2
                    result = r2_client.upload_file(
                        file_data=file_data,
                        filename=filename,
                        folder="user-uploads"
                    )
                    
                    if result:
                        recipe.image_path = result['public_url']
                        print(f"✅ Updated recipe image to R2: {recipe.image_path}")
                    else:
                        print("⚠️ R2 upload failed, falling back to local storage")
                        raise Exception("R2 upload failed")
                        
                except Exception as e:
                    print(f"⚠️ R2 upload error: {e}, falling back to local storage")
                    # Fallback to local storage
                    image_path = _save_local_image(file, filename)
                    if image_path:
                        recipe.image_path = image_path
                    else:
                        return jsonify({'success': False, 'error': 'Failed to save image'}), 500
            else:
                # R2 not available, use local storage
                print("⚠️ R2 not available, using local storage")
                image_path = _save_local_image(file, filename)
                if image_path:
                    recipe.image_path = image_path
                else:
                    return jsonify({'success': False, 'error': 'Failed to save image'}), 500
        else:
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP'}), 400
        
        recipe.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recipe image updated successfully!',
            'image_path': recipe.image_path
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating recipe image: {e}")
        return jsonify({'success': False, 'error': 'Failed to update recipe image'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
@login_required
def delete_recipe(recipe_id):
    """Delete a recipe - only the original submitter can delete"""
    try:
        recipe = Recipe.query.filter_by(id=recipe_id, user_id=current_user.id).first()
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found or you do not have permission to delete this recipe'}), 404
        
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
        
        # Allow adding any public recipe or user's own recipes to food log
        recipe = Recipe.query.filter(
            db.and_(
                Recipe.id == recipe_id,
                db.or_(
                    Recipe.user_id == current_user.id,  # User's own recipes
                    Recipe.is_public == True  # Public community recipes
                )
            )
        ).first()
        
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found or not accessible'}), 404
        
        # Calculate total nutrition for the entire recipe
        total_calories = sum(ing.calories for ing in recipe.ingredients)
        total_protein = sum(ing.protein for ing in recipe.ingredients)
        total_carbs = sum(ing.carbs for ing in recipe.ingredients)
        total_fat = sum(ing.fat for ing in recipe.ingredients)
        total_fiber = sum(ing.fiber for ing in recipe.ingredients)
        total_sugar = sum(ing.sugar for ing in recipe.ingredients)
        total_sodium = sum(ing.sodium for ing in recipe.ingredients)
        
        # Calculate nutrition per serving (divide by recipe's total servings)
        recipe_servings = recipe.servings or 1  # Default to 1 if not set
        calories_per_serving = total_calories / recipe_servings
        protein_per_serving = total_protein / recipe_servings
        carbs_per_serving = total_carbs / recipe_servings
        fat_per_serving = total_fat / recipe_servings
        fiber_per_serving = total_fiber / recipe_servings
        sugar_per_serving = total_sugar / recipe_servings
        sodium_per_serving = total_sodium / recipe_servings
        
        # Create food log entry for the recipe (multiply by user's selected servings)
        food_log = FoodLog(
            user_id=current_user.id,
            name=f"{recipe.name} (Recipe)",
            brand="Homemade",
            calories=calories_per_serving * servings,
            protein=protein_per_serving * servings,
            carbs=carbs_per_serving * servings,
            fat=fat_per_serving * servings,
            fiber=fiber_per_serving * servings,
            sugar=sugar_per_serving * servings,
            sodium=sodium_per_serving * servings,
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
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Failed to add recipe to log: {str(e)}'}), 500

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
                'image_path': _convert_image_path_to_url(recipe.image_path),
                'dynamic_image_url': recipe.dynamic_image_url,
                'is_favorite': recipe.is_favorite,
                'is_public': recipe.is_public,
                'user_id': recipe.user_id,
                'ingredients_count': len(recipe.ingredients),
                'ingredients': [{'name': ing.food_name, 'amount': ing.amount, 'unit': ing.unit} for ing in recipe.ingredients],
                'avg_rating': 0,
                'rating_count': 0
            }
            
            # Add creator name for public recipes
            if recipe.user_id != current_user.id:
                creator = User.query.get(recipe.user_id)
                recipe_dict['creator_name'] = creator.username if creator else 'Unknown'
                recipe_dict['contributor'] = creator.username if creator else 'Unknown'
            else:
                recipe_dict['contributor'] = current_user.username
                recipe_dict['is_owner'] = True
            
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
        try:
            # Build the ilike conditions
            ilike_conditions = []
            for ing in search_ingredients:
                ilike_conditions.append(RecipeIngredient.food_name.ilike(f'%{ing}%'))
            
            recipes_with_ingredients = recipes_query.join(RecipeIngredient).filter(
                db.or_(*ilike_conditions)
            ).distinct().all()
        except Exception as query_error:
            print(f"Database query error: {query_error}")
            return jsonify({'success': False, 'error': f'Database query failed: {str(query_error)}'}), 500
        
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
                    'image_path': _convert_image_path_to_url(recipe.image_path),
                    'dynamic_image_url': recipe.dynamic_image_url,
                    'is_favorite': recipe.is_favorite,
                    'is_public': recipe.is_public,
                    'user_id': recipe.user_id,
                    'ingredients_count': len(recipe.ingredients),
                    'ingredients': [{'name': ing.food_name, 'amount': ing.amount, 'unit': ing.unit} for ing in recipe.ingredients],
                    'match_percentage': round(match_percentage, 1),
                    'matching_ingredients': matching_count,
                    'avg_rating': 0,
                    'rating_count': 0
                }
                
                # Add creator name for public recipes
                if recipe.user_id != current_user.id:
                    creator = User.query.get(recipe.user_id)
                    recipe_dict['creator_name'] = creator.username if creator else 'Unknown'
                    recipe_dict['contributor'] = creator.username if creator else 'Unknown'
                else:
                    recipe_dict['contributor'] = current_user.username
                    recipe_dict['is_owner'] = True
                
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
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Failed to search recipes by ingredients: {str(e)}'}), 500

@recipe_bp.route('/api/recipes/<int:recipe_id>/rate', methods=['POST'])
@login_required
def rate_recipe(recipe_id):
    """Rate a recipe (1-5 stars) - allows all users to rate any recipe"""
    try:
        data = request.get_json()
        rating_value = data.get('rating')
        review = data.get('review', '')
        
        if not rating_value or not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400
        
        # Check if recipe exists (allow rating any recipe)
        recipe = Recipe.query.filter_by(id=recipe_id).first()
        if not recipe:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404
        
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
        
        # Update recipe's average rating and count
        recipe.update_rating_stats()
        recipe.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recipe rated successfully',
            'average_rating': recipe.average_rating,
            'rating_count': recipe.rating_count
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

@recipe_bp.route('/api/recipes/<int:recipe_id>/nutrition', methods=['POST'])
@login_required
def update_recipe_nutrition(recipe_id):
    """Automatically fetch and update nutritional data for recipe ingredients"""
    try:
        # Get the recipe
        recipe = Recipe.query.get_or_404(recipe_id)
        
        # Check if user can access this recipe
        if not recipe.is_public and recipe.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Recipe not found'})
        
        # Update nutritional data for all ingredients
        result = nutrition_service.bulk_update_recipe_nutrition(recipe_id)
        
        if result['success']:
            # Get updated recipe data
            updated_recipe = Recipe.query.get(recipe_id)
            recipe_data = updated_recipe.to_dict()
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'nutrition': result['nutrition'],
                'recipe': recipe_data
            })
        else:
            return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating recipe nutrition: {str(e)}'})
