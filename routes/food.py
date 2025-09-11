# Food-related routes
import time
import concurrent.futures
import requests
import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import db, FoodLog, WaterLog, MoodLog, Note
from services.food_data import COMMON_FOODS_DB, BASIC_FOODS

# API Configuration
USDA_API_KEY = os.getenv('USDA_API_KEY')

# Create blueprint
food_bp = Blueprint('food', __name__)

# Cache configuration
MAX_CACHE_SIZE = 1000
CACHE_DURATION = 3600  # 1 hour
food_search_cache = {}

def cleanup_cache():
    """Remove old cache entries"""
    current_time = time.time()
    keys_to_remove = []
    for key, (_, cache_time) in food_search_cache.items():
        if current_time - cache_time > CACHE_DURATION:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del food_search_cache[key]
    
    print(f"Cache cleanup: removed {len(keys_to_remove)} expired entries")

def rank_food_search_results(results, query):
    """Rank food search results by relevance to query"""
    if not results:
        return []
    
    query_lower = query.lower().strip()
    scored_results = []
    
    for result in results:
        name_lower = result['name'].lower()
        score = 0
        
        # Exact match gets highest score
        if name_lower == query_lower:
            score += 100
        # Starts with query gets high score
        elif name_lower.startswith(query_lower):
            score += 80
        # Contains query gets medium score
        elif query_lower in name_lower:
            score += 60
        # Query words in result name
        else:
            query_words = query_lower.split()
            for word in query_words:
                if word in name_lower:
                    score += 20
        
        # Bonus for shorter names (more specific)
        if len(name_lower) < 30:
            score += 10
        
        # Bonus for having complete nutrition info
        if result.get('calories', 0) > 0 and result.get('protein', 0) >= 0:
            score += 5
        
        scored_results.append((score, result))
    
    # Sort by score (highest first) and return results
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [result for score, result in scored_results]

def search_usda_api(query):
    """Search USDA FoodData Central API"""
    try:
        if not USDA_API_KEY:
            return []
        
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            'query': query,
            'api_key': USDA_API_KEY,
            'pageSize': 5,
            'dataType': ['Survey (FNDDS)', 'Foundation']
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for food in data.get('foods', [])[:3]:  # Limit to top 3
            nutrients = {n['nutrientName']: n.get('value', 0) for n in food.get('foodNutrients', [])}
            
            result = {
                'name': food.get('description', 'Unknown'),
                'brand': food.get('brandOwner', ''),
                'calories': int(nutrients.get('Energy', 0) or 0),
                'protein': round(nutrients.get('Protein', 0) or 0, 1),
                'carbs': round(nutrients.get('Carbohydrate, by difference', 0) or 0, 1),
                'fat': round(nutrients.get('Total lipid (fat)', 0) or 0, 1),
                'fiber': round(nutrients.get('Fiber, total dietary', 0) or 0, 1),
                'sugar': round(nutrients.get('Sugars, total including NLEA', 0) or 0, 1),
                'sodium': round((nutrients.get('Sodium, Na', 0) or 0) / 1000, 1),  # Convert mg to g
                'serving_size': 100,
                'serving_unit': 'g',
                'source': 'usda'
            }
            results.append(result)
        
        return results
    except Exception as e:
        print(f"USDA API error: {e}")
        return []

def search_openfoodfacts_api(query):
    """Search Open Food Facts API"""
    try:
        url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            'search_terms': query,
            'search_simple': 1,
            'action': 'process',
            'json': 1,
            'page_size': 8,
            'fields': 'product_name,brands,nutriments,serving_size,serving_quantity'
        }
        headers = {
            'User-Agent': 'KiWellness/1.0 (https://kiwellness.org)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for product in data.get('products', [])[:5]:  # Limit to top 5
            nutriments = product.get('nutriments', {})
            
            result = {
                'name': product.get('product_name', 'Unknown Product'),
                'brand': product.get('brands', ''),
                'calories': int(nutriments.get('energy-kcal_100g', 0) or 0),
                'protein': round(nutriments.get('proteins_100g', 0) or 0, 1),
                'carbs': round(nutriments.get('carbohydrates_100g', 0) or 0, 1),
                'fat': round(nutriments.get('fat_100g', 0) or 0, 1),
                'fiber': round(nutriments.get('fiber_100g', 0) or 0, 1),
                'sugar': round(nutriments.get('sugars_100g', 0) or 0, 1),
                'sodium': round(nutriments.get('sodium_100g', 0) or 0, 1),
                'serving_size': int(product.get('serving_quantity', 100) or 100),
                'serving_unit': product.get('serving_size', 'g') or 'g',
                'source': 'openfoodfacts'
            }
            results.append(result)
        
        return results
    except Exception as e:
        print(f"Open Food Facts API error: {e}")
        return []

@food_bp.route('/api/search-food', methods=['POST'])
@login_required
def search_food():
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'message': 'Query is required'})
    
    # Clean up cache periodically
    if len(food_search_cache) > MAX_CACHE_SIZE * 0.8:  # Clean when 80% full
        cleanup_cache()
    
    # Check cache first
    cache_key = query.lower()
    current_time = time.time()
    if cache_key in food_search_cache:
        cached_result, cache_time = food_search_cache[cache_key]
        if current_time - cache_time < CACHE_DURATION:
            return jsonify({'success': True, 'results': cached_result, 'cached': True})
    
    # Check fallback database first for exact matches (instant)
    fallback_results = []
    exact_matches = []
    partial_matches = []
    query_lower = query.lower()
    
    for food_key, food_data in COMMON_FOODS_DB.items():
        if query_lower == food_key.lower():
            # Exact match - highest priority
            exact_matches.append(food_data)
        elif query_lower in food_key.lower() or food_key.lower() in query_lower:
            # Partial match - lower priority
            partial_matches.append(food_data)
    
    # Combine results with exact matches first
    fallback_results = exact_matches + partial_matches
    
    # If we have good fallback results, rank them and return immediately
    if len(fallback_results) >= 3:
        ranked_fallback = rank_food_search_results(fallback_results, query)
        result = ranked_fallback[:8]
        food_search_cache[cache_key] = (result, current_time)
        return jsonify({'success': True, 'results': result, 'fast': True, 'exact_matches': len(exact_matches)})
    
    # Determine if this is a basic food
    is_basic_food = any(basic_food in query.lower() for basic_food in BASIC_FOODS)
    
    # Run API searches in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        
        # Submit USDA search if applicable
        if is_basic_food and USDA_API_KEY:
            futures['usda'] = executor.submit(search_usda_api, query)
        
        # Submit Open Food Facts search
        futures['openfoodfacts'] = executor.submit(search_openfoodfacts_api, query)
        
        # Collect results as they complete
        usda_results = []
        openfoodfacts_results = []
        
        for name, future in futures.items():
            try:
                result = future.result(timeout=3)  # 3 second timeout per API
                if name == 'usda':
                    usda_results = result
                elif name == 'openfoodfacts':
                    openfoodfacts_results = result
            except concurrent.futures.TimeoutError:
                print(f"Timeout for {name} API")
            except Exception as e:
                print(f"Error in {name} API: {e}")
    
    # Combine all results for ranking
    all_results = fallback_results + usda_results + openfoodfacts_results
    
    # Rank results by match quality (exact matches first)
    ranked_results = rank_food_search_results(all_results, query)
    
    # Remove duplicates while preserving ranking
    unique_results = []
    seen_names = set()
    
    for result in ranked_results:
        # Use normalized name for duplicate detection
        normalized_name = result['name'].lower().strip()
        if normalized_name not in seen_names:
            unique_results.append(result)
            seen_names.add(normalized_name)
    
    final_results = unique_results[:8]
    
    # Cache the results
    food_search_cache[cache_key] = (final_results, current_time)
    
    return jsonify({
        'success': True,
        'results': final_results,
        'cached': False
    })

@food_bp.route('/api/search-food-barcode', methods=['POST'])
@login_required
def search_food_barcode():
    """Search for food by barcode"""
    data = request.get_json()
    barcode = data.get('barcode', '').strip()
    
    if not barcode:
        return jsonify({'success': False, 'message': 'Barcode is required'})
    
    try:
        # Clean and validate barcode
        if not barcode or len(barcode) < 8:
            return jsonify({'success': False, 'message': 'Invalid barcode format'})
        
        # Use the newer API endpoint for better reliability
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}"
        headers = {
            'User-Agent': 'KiWellness/1.0 (https://kiwellness.org)',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        api_data = response.json()
        
        if api_data.get('status') == 1 and api_data.get('product'):
            product = api_data['product']
            nutriments = product.get('nutriments', {})
            
            result = {
                'name': product.get('product_name', 'Unknown Product'),
                'brand': product.get('brands', ''),
                'calories': int(nutriments.get('energy-kcal_100g', 0)),
                'protein': round(nutriments.get('proteins_100g', 0), 1),
                'carbs': round(nutriments.get('carbohydrates_100g', 0), 1),
                'fat': round(nutriments.get('fat_100g', 0), 1),
                'fiber': round(nutriments.get('fiber_100g', 0), 1),
                'sugar': round(nutriments.get('sugars_100g', 0), 1),
                'sodium': round(nutriments.get('sodium_100g', 0), 1),
                'serving_size': 100,
                'serving_unit': 'g'
            }
            
            return jsonify({'success': True, 'result': result})
        else:
            return jsonify({'success': False, 'message': 'Product not found'})
            
    except Exception as e:
        print(f"Barcode search error: {e}")
        return jsonify({'success': False, 'message': 'Failed to search product'})

@food_bp.route('/api/add-product-to-off', methods=['POST'])
@login_required
def add_product_to_open_food_facts():
    """Add a new product to Open Food Facts database"""
    try:
        # Get form data
        barcode = request.form.get('barcode', '').strip()
        product_name = request.form.get('product_name', '').strip()
        
        # Validate required fields
        if not product_name:
            return jsonify({'success': False, 'message': 'Product name is required'})
        
        # Prepare data for Open Food Facts API
        form_data = {
            'user_id': 'kiwellness-app',  # Our app's username
            'password': os.environ.get('OPENFOODFACTS_PASSWORD', ''),  # Set this in environment
            'product_name': product_name,
        }
        
        # Add barcode if provided
        if barcode:
            form_data['code'] = barcode
        
        # Add optional fields if provided
        optional_fields = {
            'brands': request.form.get('brands'),
            'categories': request.form.get('categories'),
            'quantity': request.form.get('quantity'),
            'ingredients_text': request.form.get('ingredients_text'),
        }
        
        for field, value in optional_fields.items():
            if value and value.strip():
                form_data[field] = value.strip()
        
        # Add nutrition facts if provided
        nutrition_fields = {
            'nutrition_data_per': '100g',
            'nutrition_data_prepared_per': '100g',
        }
        
        nutrition_mapping = {
            'nutrition_energy_kcal': 'energy-kcal',
            'nutrition_proteins': 'proteins',
            'nutrition_carbohydrates': 'carbohydrates', 
            'nutrition_fat': 'fat',
            'nutrition_fiber': 'fiber',
            'nutrition_sugars': 'sugars'
        }
        
        for form_field, off_field in nutrition_mapping.items():
            value = request.form.get(form_field)
            if value and value.strip():
                try:
                    # Convert to float and add to form data
                    float_value = float(value)
                    form_data[f'nutriment_{off_field}'] = str(float_value)
                    form_data[f'nutriment_{off_field}_unit'] = 'g' if off_field != 'energy-kcal' else 'kcal'
                except ValueError:
                    pass  # Skip invalid nutrition values
        
        # Handle image uploads
        files = {}
        uploaded_files = request.files.getlist('images')
        
        for i, file in enumerate(uploaded_files):
            if file and file.filename:
                # Determine image type based on order
                if i == 0:
                    field_name = 'imgupload_front'
                elif i == 1:
                    field_name = 'imgupload_ingredients'
                elif i == 2:
                    field_name = 'imgupload_nutrition'
                else:
                    field_name = f'imgupload_other_{i}'
                
                files[field_name] = (file.filename, file.stream, file.content_type)
        
        # Submit to Open Food Facts
        url = 'https://world.openfoodfacts.org/cgi/product_jqm2.pl'
        headers = {
            'User-Agent': 'KiWellness/1.0 (https://kiwellness.org; contact@kiwellness.org)'
        }
        
        response = requests.post(url, data=form_data, files=files, headers=headers, timeout=30)
        
        # Check if submission was successful
        if response.status_code == 200:
            # Open Food Facts doesn't always return clear success indicators
            # We'll assume success if we get a 200 response
            return jsonify({
                'success': True, 
                'message': 'Product successfully added to Open Food Facts database!'
            })
        else:
            return jsonify({
                'success': False, 
                'message': f'Failed to add product (HTTP {response.status_code})'
            })
            
    except Exception as e:
        print(f"Error adding product to Open Food Facts: {e}")
        return jsonify({
            'success': False, 
            'message': 'Network error occurred while adding product'
        })

@food_bp.route('/api/product/<barcode>')
@login_required
def get_product(barcode):
    """Get product information from Open Food Facts API"""
    try:
        # Clean and validate barcode
        barcode = str(barcode).strip()
        if not barcode or len(barcode) < 8:
            return jsonify({'success': False, 'message': 'Invalid barcode format'})
        
        # Use the newer API endpoint for better reliability
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}"
        headers = {
            'User-Agent': 'KiWellness/1.0 (https://kiwellness.org)',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 1 and data.get('product'):
            product = data['product']
            nutriments = product.get('nutriments', {})
            
            # Extract product information with fallbacks
            result = {
                'name': product.get('product_name') or product.get('generic_name') or 'Unknown Product',
                'brand': product.get('brands') or product.get('brand_owner') or 'Unknown Brand',
                'calories': float(nutriments.get('energy-kcal_100g', 0) or 0),
                'protein': float(nutriments.get('proteins_100g', 0) or 0),
                'carbs': float(nutriments.get('carbohydrates_100g', 0) or 0),
                'fat': float(nutriments.get('fat_100g', 0) or 0),
                'fiber': float(nutriments.get('fiber_100g', 0) or 0),
                'sugar': float(nutriments.get('sugars_100g', 0) or 0),
                'sodium': float(nutriments.get('sodium_100g', 0) or 0),
                'source': 'openfoodfacts',
                'barcode': barcode,
                'image_url': product.get('image_front_url') or product.get('image_url'),
                'ingredients': product.get('ingredients_text'),
                'allergens': product.get('allergens_tags', []),
                'nutrition_grade': product.get('nutrition_grade_fr') or product.get('nutrition_grade'),
                'nova_group': product.get('nova_group'),
                'ecoscore_grade': product.get('ecoscore_grade')
            }
            
            # Validate that we have at least basic nutritional info
            if result['calories'] == 0 and result['protein'] == 0 and result['carbs'] == 0 and result['fat'] == 0:
                return jsonify({
                    'success': False, 
                    'message': 'Product found but no nutritional information available',
                    'product_name': result['name'],
                    'barcode': barcode
                })
            
            return jsonify({'success': True, 'product': result})
        else:
            # Try alternative API endpoint for better coverage
            alt_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
            alt_response = requests.get(alt_url, headers=headers, timeout=15)
            
            if alt_response.status_code == 200:
                alt_data = alt_response.json()
                if alt_data.get('status') == 1 and alt_data.get('product'):
                    product = alt_data['product']
                    nutriments = product.get('nutriments', {})
                    
                    result = {
                        'name': product.get('product_name') or product.get('generic_name') or 'Unknown Product',
                        'brand': product.get('brands') or 'Unknown Brand',
                        'calories': float(nutriments.get('energy-kcal_100g', 0) or 0),
                        'protein': float(nutriments.get('proteins_100g', 0) or 0),
                        'carbs': float(nutriments.get('carbohydrates_100g', 0) or 0),
                        'fat': float(nutriments.get('fat_100g', 0) or 0),
                        'fiber': float(nutriments.get('fiber_100g', 0) or 0),
                        'sugar': float(nutriments.get('sugars_100g', 0) or 0),
                        'sodium': float(nutriments.get('sodium_100g', 0) or 0),
                        'source': 'openfoodfacts_alt',
                        'barcode': barcode
                    }
                    
                    if result['calories'] > 0 or result['protein'] > 0 or result['carbs'] > 0 or result['fat'] > 0:
                        return jsonify({'success': True, 'product': result})
            
            return jsonify({
                'success': False, 
                'message': 'Product not found in database',
                'barcode': barcode,
                'suggestion': 'Try searching manually or check the barcode number'
            })
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'Request timeout - please try again'})
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'Network error: {str(e)}'})
    except Exception as e:
        print(f"Error fetching product {barcode}: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch product information'})

@food_bp.route('/api/food-log', methods=['POST'])
@login_required
def add_food_log():
    data = request.get_json()
    
    food_log = FoodLog(
        user_id=current_user.id,
        name=data['name'],
        brand=data.get('brand', ''),
        calories=data['calories'],
        protein=data['protein'],
        carbs=data['carbs'],
        fat=data['fat'],
        fiber=data.get('fiber', 0),
        sugar=data.get('sugar', 0),
        sodium=data.get('sodium', 0),
        serving_size=data['serving_size'],
        original_amount=data['original_amount'],
        original_unit=data['original_unit'],
        quantity=data['quantity'],
        time_of_day=data.get('time_of_day', 'snack'),
        date=datetime.strptime(data['date'], '%Y-%m-%d').date()
    )
    
    db.session.add(food_log)
    db.session.commit()
    
    return jsonify({'success': True})

@food_bp.route('/api/food-log/<int:food_id>', methods=['DELETE'])
@login_required
def delete_food_log(food_id):
    food_log = FoodLog.query.filter_by(id=food_id, user_id=current_user.id).first()
    if food_log:
        db.session.delete(food_log)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Food log entry not found'})

@food_bp.route('/api/food-log/<int:food_id>/edit', methods=['PUT'])
@login_required
def edit_food_log(food_id):
    food_log = FoodLog.query.filter_by(id=food_id, user_id=current_user.id).first()
    if not food_log:
        return jsonify({'success': False, 'message': 'Food log entry not found'})
    
    data = request.get_json()
    
    # Update the food log entry
    food_log.name = data.get('name', food_log.name)
    food_log.brand = data.get('brand', food_log.brand)
    food_log.calories = data.get('calories', food_log.calories)
    food_log.protein = data.get('protein', food_log.protein)
    food_log.carbs = data.get('carbs', food_log.carbs)
    food_log.fat = data.get('fat', food_log.fat)
    food_log.fiber = data.get('fiber', food_log.fiber)
    food_log.sugar = data.get('sugar', food_log.sugar)
    food_log.sodium = data.get('sodium', food_log.sodium)
    food_log.serving_size = data.get('serving_size', food_log.serving_size)
    food_log.original_amount = data.get('original_amount', food_log.original_amount)
    food_log.original_unit = data.get('original_unit', food_log.original_unit)
    food_log.quantity = data.get('quantity', food_log.quantity)
    food_log.time_of_day = data.get('time_of_day', food_log.time_of_day)
    
    # Update date if provided
    if 'date' in data:
        food_log.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    db.session.commit()
    
    return jsonify({'success': True})

@food_bp.route('/api/food-log/<int:food_id>/copy', methods=['POST'])
@login_required
def copy_food_log(food_id):
    # Find the original food log entry
    original_food_log = FoodLog.query.filter_by(id=food_id, user_id=current_user.id).first()
    if not original_food_log:
        return jsonify({'success': False, 'message': 'Food log entry not found'})
    
    data = request.get_json()
    target_date_str = data.get('date')
    target_time_of_day = data.get('time_of_day')
    
    if not target_date_str:
        return jsonify({'success': False, 'message': 'Target date is required'})
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'})
    
    # Use provided time_of_day or fall back to original
    final_time_of_day = target_time_of_day if target_time_of_day else original_food_log.time_of_day
    
    # Create a new food log entry with the same data but different date and time
    new_food_log = FoodLog(
        user_id=current_user.id,
        name=original_food_log.name,
        brand=original_food_log.brand,
        calories=original_food_log.calories,
        protein=original_food_log.protein,
        carbs=original_food_log.carbs,
        fat=original_food_log.fat,
        fiber=original_food_log.fiber,
        sugar=original_food_log.sugar,
        sodium=original_food_log.sodium,
        serving_size=original_food_log.serving_size,
        original_amount=original_food_log.original_amount,
        original_unit=original_food_log.original_unit,
        quantity=original_food_log.quantity,
        time_of_day=final_time_of_day,
        date=target_date
    )
    
    db.session.add(new_food_log)
    db.session.commit()
    
    return jsonify({'success': True})

@food_bp.route('/api/water-log', methods=['POST'])
@login_required
def add_water_log():
    data = request.get_json()
    
    water_log = WaterLog(
        user_id=current_user.id,
        amount=data['amount'],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date()
    )
    
    db.session.add(water_log)
    db.session.commit()
    
    return jsonify({'success': True})

@food_bp.route('/api/mood-log', methods=['POST'])
@login_required
def add_mood_log():
    data = request.get_json()
    
    mood_log = MoodLog(
        user_id=current_user.id,
        mood=data['mood'],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date()
    )
    
    db.session.add(mood_log)
    db.session.commit()
    
    return jsonify({'success': True})

@food_bp.route('/api/notes', methods=['POST'])
@login_required
def save_notes():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        if 'content' not in data or 'date' not in data:
            return jsonify({'success': False, 'error': 'Missing content or date'}), 400
        
        # Check if a note already exists for this user and date
        existing_note = Note.query.filter_by(
            user_id=current_user.id,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date()
        ).first()
        
        if existing_note:
            # Update existing note
            existing_note.content = data['content']
        else:
            # Create new note
            note = Note(
                user_id=current_user.id,
                content=data['content'],
                date=datetime.strptime(data['date'], '%Y-%m-%d').date()
            )
            db.session.add(note)
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400
    except Exception as e:
        print(f"Error saving notes: {e}")
        return jsonify({'success': False, 'error': 'Failed to save notes'}), 500

@food_bp.route('/api/mood-notes-history')
@login_required
def get_mood_notes_history():
    # Get the last 30 days of mood and notes data
    from datetime import timedelta
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Query mood logs
    mood_logs = MoodLog.query.filter(
        MoodLog.user_id == current_user.id,
        MoodLog.date >= start_date,
        MoodLog.date <= end_date
    ).order_by(MoodLog.date.desc()).all()
    
    # Query notes
    notes = Note.query.filter(
        Note.user_id == current_user.id,
        Note.date >= start_date,
        Note.date <= end_date
    ).order_by(Note.date.desc()).all()
    
    # Format the data
    mood_data = {}
    for mood in mood_logs:
        date_str = mood.date.strftime('%Y-%m-%d')
        mood_data[date_str] = mood.mood
    
    notes_data = {}
    for note in notes:
        date_str = note.date.strftime('%Y-%m-%d')
        notes_data[date_str] = {
            'notes': note.content
        }
    
    return jsonify({
        'success': True,
        'moods': mood_data,
        'notes': notes_data
    })
