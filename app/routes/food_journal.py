"""
Ki Wellness - Food Journal Routes
=================================

This module contains food journal routes for tracking food intake,
searching food items, and managing food entries.

Author: Ki Wellness Team
Version: 2.0
"""

import csv
import io
from flask import Blueprint, render_template, request, jsonify, send_file, make_response
from datetime import datetime
from ..models import db, FoodJournal
from ..services import UserService, NutritionService, FUZZY_AVAILABLE
from ..decorators import login_required

# Create blueprint
food_journal_bp = Blueprint('food_journal', __name__)


# Food journal route removed - functionality moved to dashboard


@food_journal_bp.route('/food-journal/search', methods=['POST'])
@login_required
def search_food():
    """Search for food items"""
    try:
        data = request.get_json()
        
        # Handle different search types: query, food_name, or barcode
        query = data.get('query', '').strip()
        if not query:
            query = data.get('food_name', '').strip()
        if not query:
            query = data.get('barcode', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query or barcode is required'}), 400
        
        results = []
        
        # Check if this is a barcode search (numeric or alphanumeric with specific patterns)
        # Only treat as barcode if it's all digits or has a specific barcode pattern
        is_barcode = (query.isdigit() or 
                     (len(query) >= 8 and query.replace('-', '').replace(' ', '').isdigit()) or
                     (len(query) >= 8 and query.replace('-', '').replace(' ', '').isalnum() and 
                      any(char.isdigit() for char in query)))
        
        if is_barcode:
            # Barcode search - try FoodJournal history first, then OpenFoodFacts API
            print(f"🔍 Searching for barcode: {query}")
            
            # Check if this barcode was used before in FoodJournal
            current_user = UserService.get_current_user()
            if not current_user:
                return jsonify({'error': 'User not authenticated'}), 401
                
            previous_entry = FoodJournal.query.filter(
                FoodJournal.barcode == query,
                FoodJournal.user_id == current_user.id
            ).order_by(FoodJournal.consumed_at.desc()).first()
            
            if previous_entry:
                print(f"✅ Found barcode in user's food journal history: {query}")
                results.append({
                    'id': previous_entry.id,
                    'food_name': previous_entry.food_name,
                    'brand': previous_entry.brand or '',
                    'serving_size': previous_entry.serving_size,
                    'serving_unit': previous_entry.serving_unit,
                    'calories': previous_entry.calories,
                    'protein': previous_entry.protein,
                    'carbs': previous_entry.carbs,
                    'fat': previous_entry.fat,
                    'source': 'user_history'
                })
            else:
                # Try local barcode database first
                try:
                    print(f"🔍 Searching local barcode database for: {query}")
                    barcode_data = NutritionService.search_barcode_database(query)
                    if barcode_data:
                        print(f"✅ Found barcode data in local database for: {query}")
                        results.append({
                            'id': None,
                            'food_name': barcode_data.get('food_name', f'Product {query}'),
                            'brand': barcode_data.get('brand', ''),
                            'serving_size': barcode_data.get('serving_size', 100),
                            'serving_unit': barcode_data.get('serving_unit', 'g'),
                            'calories': barcode_data.get('calories', 0),
                            'protein': barcode_data.get('protein', 0),
                            'carbs': barcode_data.get('carbs', 0),
                            'fat': barcode_data.get('fat', 0),
                            'fiber': barcode_data.get('fiber', 0),
                            'sugar': barcode_data.get('sugar', 0),
                            'sodium': barcode_data.get('sodium', 0),
                            'source': 'barcode_db'
                        })
                    else:
                        # Try OpenFoodFacts barcode API as fallback
                        print(f"🔍 Searching OpenFoodFacts barcode API for: {query}")
                        barcode_data = NutritionService.search_openfoodfacts_by_barcode(query)
                        if barcode_data:
                            print(f"✅ Found barcode data in OpenFoodFacts for: {query}")
                            results.append({
                                'id': None,
                                'food_name': barcode_data.get('food_name', f'Product {query}'),
                                'brand': barcode_data.get('brand', ''),
                                'serving_size': barcode_data.get('serving_size', 100),
                                'serving_unit': barcode_data.get('serving_unit', 'g'),
                                'calories': barcode_data.get('calories', 0),
                                'protein': barcode_data.get('protein', 0),
                                'carbs': barcode_data.get('carbs', 0),
                                'fat': barcode_data.get('fat', 0),
                                'fiber': barcode_data.get('fiber', 0),
                                'sugar': barcode_data.get('sugar', 0),
                                'sodium': barcode_data.get('sodium', 0),
                                'source': 'openfoodfacts_barcode'
                            })
                        else:
                            print(f"❌ No barcode data found for: {query}")
                except Exception as barcode_error:
                    print(f"❌ Error searching barcode: {barcode_error}")
                    import traceback
                    traceback.print_exc()
        
        # For non-barcode searches, try OpenFoodFacts API and common foods
        if not is_barcode:
            # Enhance search query with spelling corrections and variations
            enhanced_queries = NutritionService.enhance_search_query(query)
            print(f"🔍 Enhanced search queries: {enhanced_queries}")
            
            # Try each enhanced query
            for enhanced_query in enhanced_queries:
                try:
                    print(f"🔍 Searching OpenFoodFacts API for: {enhanced_query}")
                    nutrition_results = NutritionService.search_openfoodfacts_multiple(enhanced_query)
                    if nutrition_results:
                        print(f"✅ Found {len(nutrition_results)} OpenFoodFacts results for: {enhanced_query}")
                        # Add all results to the results list
                        for nutrition_data in nutrition_results:
                            results.append({
                                'id': None,  # No cache ID for API results
                                'food_name': nutrition_data.get('food_name', enhanced_query),
                                'brand': nutrition_data.get('brand', ''),
                                'serving_size': nutrition_data.get('serving_size', 100),
                                'serving_unit': nutrition_data.get('serving_unit', 'g'),
                                'calories': nutrition_data.get('calories', 0),
                                'protein': nutrition_data.get('protein', 0),
                                'carbs': nutrition_data.get('carbs', 0),
                                'fat': nutrition_data.get('fat', 0),
                                'fiber': nutrition_data.get('fiber', 0),
                                'sugar': nutrition_data.get('sugar', 0),
                                'sodium': nutrition_data.get('sodium', 0),
                                'source': 'openfoodfacts_api',
                                'search_query': enhanced_query  # Track which query found this result
                            })
                        # If we found results, we can stop trying other variations
                        break
                    else:
                        print(f"❌ No OpenFoodFacts data found for: {enhanced_query}")
                        
                except Exception as api_error:
                    print(f"❌ Error searching OpenFoodFacts API for {enhanced_query}: {api_error}")
                    import traceback
                    traceback.print_exc()
            
            # Always try common foods database as fallback
            try:
                print(f"🔍 Searching common foods database with enhanced queries: {enhanced_queries}")
                for enhanced_query in enhanced_queries:
                    common_foods = NutritionService.search_common_foods_multiple(enhanced_query)
                    if common_foods:
                        print(f"✅ Found {len(common_foods)} common foods results for: {enhanced_query}")
                        for common_food in common_foods:
                            results.append({
                                'id': None,
                                'food_name': common_food.get('food_name', enhanced_query),
                                'brand': '',
                                'serving_size': common_food.get('serving_size', 100),
                                'serving_unit': common_food.get('serving_unit', 'g'),
                                'calories': common_food.get('calories', 0),
                                'protein': common_food.get('protein', 0),
                                'carbs': common_food.get('carbs', 0),
                                'fat': common_food.get('fat', 0),
                                'fiber': common_food.get('fiber', 0),
                                'sugar': common_food.get('sugar', 0),
                                'sodium': common_food.get('sodium', 0),
                                'source': 'common_foods_db',
                                'search_query': enhanced_query  # Track which query found this result
                            })
                        # If we found results, we can stop trying other variations
                        break
                    else:
                        print(f"❌ No common foods data found for: {enhanced_query}")
            except Exception as common_error:
                print(f"❌ Error searching common foods database: {common_error}")
                import traceback
                traceback.print_exc()
        
        # Score and sort results by nutritional data completeness
        def score_nutritional_completeness(result):
            """Score a result based on how complete its nutritional data is"""
            score = 0
            core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
            for nutrient in core_nutrients:
                if result.get(nutrient) is not None and result.get(nutrient) != 0:
                    score += 1
            return score
        
        # Sort results by completeness (most complete first)
        results.sort(key=score_nutritional_completeness, reverse=True)
        
        # Return results for the frontend
        if results:
            # If we have multiple results, return them all for user selection
            if len(results) > 1:
                # Multiple results found, convert all results based on user's serving size
                user_serving_size = request.json.get('serving_size')
                user_serving_unit = request.json.get('serving_unit', 'g')
                
                converted_results = []
                for result in results:
                    if user_serving_size and user_serving_unit:
                        try:
                            # Convert each result to match user's serving size
                            converted_data = NutritionService.convert_nutritional_data(
                                result, 
                                float(user_serving_size), 
                                user_serving_unit
                            )
                            if converted_data:
                                converted_results.append(converted_data)
                            else:
                                converted_results.append(result)
                        except Exception as conversion_error:
                            print(f"❌ Error converting nutritional data: {conversion_error}")
                            converted_results.append(result)
                    else:
                        converted_results.append(result)
                
                return jsonify({
                    'success': True,
                    'multiple_results': True,
                    'results': converted_results,
                    'count': len(converted_results)
                })
            else:
                # Single result, use it as the main data
                main_result = results[0]
                
                # Convert nutritional data based on user's serving size if provided
                user_serving_size = request.json.get('serving_size')
                user_serving_unit = request.json.get('serving_unit', 'g')
                
                if user_serving_size and user_serving_unit:
                    try:
                        # Convert the nutritional data to match user's serving size
                        converted_data = NutritionService.convert_nutritional_data(
                            main_result, 
                            float(user_serving_size), 
                            user_serving_unit
                        )
                        if converted_data:
                            main_result = converted_data
                    except Exception as conversion_error:
                        print(f"❌ Error converting nutritional data: {conversion_error}")
                        # Continue with original data if conversion fails
                
                return jsonify({
                    'success': True,
                    'data': main_result,
                    'results': results
                })
        else:
            # Provide helpful message for barcode searches
            if is_barcode:
                return jsonify({
                    'success': False,
                    'error': f'No nutritional data found for barcode: {query}. This product may not be in our database yet. You can add it manually below.',
                    'barcode': query,
                    'suggest_manual': True
                })
            else:
                # Try to provide spelling suggestions
                spelling_suggestions = []
                if FUZZY_AVAILABLE:
                    # Get suggestions from common foods database
                    common_food_names = list(NutritionService.COMMON_FOODS_DATABASE.keys())
                    suggestions = NutritionService.get_fuzzy_search_suggestions(query, common_food_names, limit=3)
                    spelling_suggestions = [name for name, score in suggestions if score >= 70]
                
                # Also check for common misspellings
                corrected = NutritionService.correct_spelling(query)
                if corrected != query and corrected not in spelling_suggestions:
                    spelling_suggestions.insert(0, corrected)
                
                response_data = {
                    'success': False,
                    'error': 'No food data found'
                }
                
                if spelling_suggestions:
                    response_data['spelling_suggestions'] = spelling_suggestions
                    response_data['error'] = f'No food data found for "{query}". Did you mean: {", ".join(spelling_suggestions[:3])}?'
                
                return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error searching food: {e}")
        return jsonify({'success': False, 'error': 'Failed to search food'}), 500


@food_journal_bp.route('/food-journal/add', methods=['POST'])
@login_required
def add_food_entry():
    """Add food entry to journal"""
    try:
        data = request.get_json()
        current_user = UserService.get_current_user()
        
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Validate required fields
        food_name = data.get('food_name', '').strip()
        serving_size = data.get('serving_size')
        serving_unit = data.get('serving_unit', 'g')
        
        if not food_name or not serving_size:
            return jsonify({'success': False, 'error': 'Food name and serving size are required'}), 400
        
        # Parse consumed_at date from request or use current time
        consumed_at = data.get('consumed_at')
        if consumed_at:
            try:
                consumed_at = datetime.fromisoformat(consumed_at.replace('Z', '+00:00'))
            except ValueError:
                consumed_at = datetime.utcnow()
        else:
            consumed_at = datetime.utcnow()
        
        # Create food journal entry
        entry = FoodJournal(
            user_id=current_user.id,
            food_name=food_name,
            brand=data.get('brand', ''),
            serving_size=float(serving_size),
            serving_unit=serving_unit,
            time_of_day=data.get('time_of_day', 'snack'),
            consumed_at=consumed_at,
            mood=data.get('mood'),
            notes=data.get('notes', '')
        )
        
        # Add nutritional data if available
        if 'calories' in data and data['calories'] is not None:
            try:
                entry.calories = float(data['calories'])
            except (ValueError, TypeError):
                entry.calories = None
        if 'protein' in data and data['protein'] is not None:
            try:
                entry.protein = float(data['protein'])
            except (ValueError, TypeError):
                entry.protein = None
        if 'carbs' in data and data['carbs'] is not None:
            try:
                entry.carbs = float(data['carbs'])
            except (ValueError, TypeError):
                entry.carbs = None
        if 'fat' in data and data['fat'] is not None:
            try:
                entry.fat = float(data['fat'])
            except (ValueError, TypeError):
                entry.fat = None
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Food entry added successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error adding food entry: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to add food entry'}), 500


@food_journal_bp.route('/food-journal/entries')
@login_required
def get_food_entries():
    """Get user's food journal entries"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = FoodJournal.query.filter_by(user_id=current_user.id)
        
        if start_date:
            query = query.filter(FoodJournal.consumed_at >= start_date)
        if end_date:
            query = query.filter(FoodJournal.consumed_at <= end_date + ' 23:59:59')
        
        entries = query.order_by(FoodJournal.consumed_at.desc(), FoodJournal.created_at.desc()).all()
        
        results = []
        for entry in entries:
            results.append({
                'id': entry.id,
                'food_name': entry.food_name,
                'brand': entry.brand,
                'serving_size': entry.serving_size,
                'serving_unit': entry.serving_unit,
                'calories': entry.calories,
                'protein': entry.protein,
                'carbs': entry.carbs,
                'fat': entry.fat,
                'time_of_day': entry.time_of_day,
                'consumed_at': entry.consumed_at.isoformat(),
                'mood': entry.mood,
                'notes': entry.notes,
                'created_at': entry.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'entries': results
        })
        
    except Exception as e:
        print(f"❌ Error getting food entries: {e}")
        return jsonify({'success': False, 'error': 'Failed to get food entries'}), 500


@food_journal_bp.route('/food-journal/delete', methods=['POST'])
@login_required
def delete_food_entry():
    """Delete food journal entry"""
    try:
        data = request.get_json()
        entry_id = data.get('entry_id')
        
        if not entry_id:
            return jsonify({'success': False, 'error': 'Entry ID is required'}), 400
        
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Find and delete entry
        entry = FoodJournal.query.filter_by(id=entry_id, user_id=current_user.id).first()
        if not entry:
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
        
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Entry deleted successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error deleting food entry: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete entry'}), 500


@food_journal_bp.route('/food-journal/export')
@login_required
def export_food_journal():
    """Export food journal as CSV"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get entries
        entries = FoodJournal.query.filter_by(user_id=current_user.id).order_by(FoodJournal.date.desc()).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Food Name', 'Serving Size', 'Serving Unit', 'Calories', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Meal Type', 'Notes'])
        
        for entry in entries:
            writer.writerow([
                entry.date.strftime('%Y-%m-%d'),
                entry.food_name,
                entry.serving_size,
                entry.serving_unit,
                entry.calories or '',
                entry.protein or '',
                entry.carbs or '',
                entry.fat or '',
                entry.meal_type,
                entry.notes or ''
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=food_journal_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        print(f"❌ Error exporting food journal: {e}")
        return jsonify({'success': False, 'error': 'Failed to export food journal'}), 500


@food_journal_bp.route('/food-journal/import', methods=['POST'])
@login_required
def import_food_journal():
    """Import food journal from CSV"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be a CSV'}), 400
        
        # Read CSV
        content = file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        
        imported_count = 0
        for row in reader:
            try:
                entry = FoodJournal(
                    user_id=current_user.id,
                    food_name=row.get('Food Name', '').strip(),
                    serving_size=float(row.get('Serving Size', 0)),
                    serving_unit=row.get('Serving Unit', 'g'),
                    calories=float(row.get('Calories', 0)) if row.get('Calories') else None,
                    protein=float(row.get('Protein (g)', 0)) if row.get('Protein (g)') else None,
                    carbs=float(row.get('Carbs (g)', 0)) if row.get('Carbs (g)') else None,
                    fat=float(row.get('Fat (g)', 0)) if row.get('Fat (g)') else None,
                    meal_type=row.get('Meal Type', 'snack'),
                    date=datetime.strptime(row.get('Date', ''), '%Y-%m-%d').date(),
                    notes=row.get('Notes', '')
                )
                db.session.add(entry)
                imported_count += 1
            except Exception as e:
                print(f"❌ Error importing row: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {imported_count} entries!'
        })
        
    except Exception as e:
        print(f"❌ Error importing food journal: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to import food journal'}), 500
