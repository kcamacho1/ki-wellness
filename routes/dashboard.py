"""
Dashboard and main application page routes
Handles dashboard, profile, barcode scanning, nutrition review, and AI coach pages
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db, User, FoodLog, WaterLog, MoodLog, Note, Recipe, Subscription
from utils.decorators import premium_required
from utils.helpers import get_app_setting, check_ai_usage_limits
from datetime import datetime, date

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template('pages/dashboard/dashboard.html')


@dashboard_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('pages/dashboard/profile.html')


@dashboard_bp.route('/scan-barcode')
@login_required  
def scan_barcode():
    """Standalone barcode scanner page"""
    return render_template('pages/dashboard/scan_barcode.html')


@dashboard_bp.route('/nutrition-review')
@login_required
def nutrition_review():
    """Nutrition review page for adjusting serving size and adding to log"""
    return render_template('pages/dashboard/nutrition_review.html')


@dashboard_bp.route('/ai-coach')
@login_required
def ai_coach():
    """AI Coach interface - All users can view, premium users get full access"""
    # All users can access the AI coach page to see analysis patterns and suggestions
    # Premium features (refresh analysis, AI chat) are controlled in the frontend
    
    # Check premium access using industry-standard method
    has_premium = current_user.has_premium_access()
    
    # For premium users, check AI usage limits
    limits_ok = True
    limit_message = None
    if has_premium:
        limits_ok, limit_message = check_ai_usage_limits(current_user.id)
        if not limits_ok:
            flash(f'AI usage limit exceeded: {limit_message}. Premium features temporarily limited.', 'warning')
    
    # Pass premium status and usage info to template
    return render_template('pages/ai/ai_coach.html', 
                         has_premium=has_premium,
                         limits_ok=limits_ok,
                         limit_message=limit_message)


@dashboard_bp.route('/recipes')
@login_required
def recipes():
    """Recipe management page"""
    try:
        return render_template('recipes/recipes.html', current_user_id=current_user.id)
    except Exception as e:
        print(f"Error in recipes route: {e}")
        return f"Error: {e}", 500


@dashboard_bp.route('/api/dashboard-data')
@login_required
def get_dashboard_data():
    """Get dashboard data for a specific date"""
    user_id = current_user.id
    date_str = request.args.get('date', date.today().isoformat())
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format', 'success': False}), 400
    
    # Get food logs using SQLAlchemy
    food_logs = FoodLog.query.filter_by(
        user_id=user_id,
        date=selected_date
    ).all()
    
    # Get water logs
    water_logs = WaterLog.query.filter_by(
        user_id=user_id,
        date=selected_date
    ).all()
    
    # Get mood logs
    mood_logs = MoodLog.query.filter_by(
        user_id=user_id,
        date=selected_date
    ).all()
    
    # Get notes
    notes = Note.query.filter_by(
        user_id=user_id,
        date=selected_date
    ).order_by(Note.timestamp.desc()).all()
    
    # Calculate totals
    total_calories = sum(log.calories or 0 for log in food_logs)
    total_protein = sum(log.protein or 0 for log in food_logs)
    total_carbs = sum(log.carbs or 0 for log in food_logs)
    total_fat = sum(log.fat or 0 for log in food_logs)
    total_water = sum(log.amount or 0 for log in water_logs)  # Amount already in oz
    
    # Convert to dictionaries for JSON serialization
    food_logs_data = [
        {
            'id': log.id,
            'name': log.name,
            'brand': log.brand,
            'calories': log.calories or 0,
            'protein': log.protein or 0,
            'carbs': log.carbs or 0,
            'fat': log.fat or 0,
            'fiber': log.fiber or 0,
            'sugar': log.sugar or 0,
            'sodium': log.sodium or 0,
            'serving_size': log.serving_size or 0,
            'quantity': log.quantity or 1,
            'time_of_day': log.time_of_day,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None
        } for log in food_logs
    ]
    
    water_logs_data = [
        {
            'id': log.id,
            'amount': log.amount or 0,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None
        } for log in water_logs
    ]
    
    mood_logs_data = [
        {
            'id': log.id,
            'mood': log.mood,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None
        } for log in mood_logs
    ]
    
    notes_data = [
        {
            'id': log.id,
            'content': log.content,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None
        } for log in notes
    ]
    
    # Get recent recipes (limit 5)
    recent_recipes = Recipe.query.filter_by(user_id=user_id).order_by(Recipe.created_at.desc()).limit(5).all()
    recipes_data = [
        {
            'id': recipe.id,
            'name': recipe.name,
            'description': recipe.description,
            'image_path': recipe.image_path,
            'created_at': recipe.created_at.isoformat() if recipe.created_at else None
        } for recipe in recent_recipes
    ]
    
    return jsonify({
        'success': True,
        'data': {
            'food_logs': food_logs_data,
            'water_logs': water_logs_data,
            'mood_logs': mood_logs_data,
            'notes': notes_data,
            'recent_recipes': recipes_data,
            'totals': {
                'calories': total_calories,
                'protein': total_protein,
                'carbs': total_carbs,
                'fat': total_fat,
                'water': total_water
            }
        },
        'date': date_str
    })
