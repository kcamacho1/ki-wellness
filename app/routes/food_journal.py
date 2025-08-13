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
from ..models import db, FoodCache, FoodJournal
from ..services import UserService, NutritionService
from ..decorators import login_required

# Create blueprint
food_journal_bp = Blueprint('food_journal', __name__)


@food_journal_bp.route('/food-journal')
@login_required
def food_journal():
    """Food journal page"""
    return render_template('food_journal.html')


@food_journal_bp.route('/food-journal/search', methods=['POST'])
@login_required
def search_food():
    """Search for food items"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        # Search in cache first
        cached_results = FoodCache.query.filter(
            FoodCache.name.ilike(f'%{query}%')
        ).limit(10).all()
        
        results = []
        for item in cached_results:
            results.append({
                'id': item.id,
                'name': item.name,
                'brand': item.brand,
                'serving_size': item.serving_size,
                'serving_unit': item.serving_unit,
                'calories': item.calories,
                'protein': item.protein,
                'carbs': item.carbs,
                'fat': item.fat,
                'source': item.source
            })
        
        return jsonify({
            'success': True,
            'results': results
        })
        
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
        
        # Create food journal entry
        entry = FoodJournal(
            user_id=current_user.id,
            food_name=food_name,
            serving_size=float(serving_size),
            serving_unit=serving_unit,
            meal_type=data.get('meal_type', 'snack'),
            date=datetime.utcnow().date(),
            notes=data.get('notes', '')
        )
        
        # Add nutritional data if available
        if 'calories' in data:
            entry.calories = float(data['calories'])
        if 'protein' in data:
            entry.protein = float(data['protein'])
        if 'carbs' in data:
            entry.carbs = float(data['carbs'])
        if 'fat' in data:
            entry.fat = float(data['fat'])
        
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
            query = query.filter(FoodJournal.date >= start_date)
        if end_date:
            query = query.filter(FoodJournal.date <= end_date)
        
        entries = query.order_by(FoodJournal.date.desc(), FoodJournal.created_at.desc()).all()
        
        results = []
        for entry in entries:
            results.append({
                'id': entry.id,
                'food_name': entry.food_name,
                'serving_size': entry.serving_size,
                'serving_unit': entry.serving_unit,
                'calories': entry.calories,
                'protein': entry.protein,
                'carbs': entry.carbs,
                'fat': entry.fat,
                'meal_type': entry.meal_type,
                'date': entry.date.isoformat(),
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
