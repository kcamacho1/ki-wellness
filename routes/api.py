"""
API routes for the Ki Wellness application
Handles all /api/* endpoints for data operations, AI services, and user interactions
"""
from flask import Blueprint, request, jsonify, session, current_app
from flask_login import login_required, current_user
from sqlalchemy import text, func, desc, and_, or_
from datetime import datetime, date, timedelta
import json
import re
import requests
import os

# Import database models
from database import db, User, FoodLog, WaterLog, MoodLog, Note, Recipe, RecipeIngredient, RecipeInstruction, AIUsageLog, AIAnalysis

# Import services
from services.openrouter_client import get_openrouter_client, generate_ai_response
from services.food_data import BASIC_FOODS, COMMON_FOODS_DB
from services.health_resources import get_relevant_resources, format_resources_for_prompt
from services.analytics_service import analytics_service

# Import utilities
from utils.decorators import premium_required, admin_required
from utils.helpers import get_app_setting, check_ai_usage_limits
from security_middleware import rate_limit, sanitize_input
from database_security import validate_user_input, sanitize_user_input, create_safe_query

# Create blueprint
api_bp = Blueprint('api', __name__)


def _calculate_macro_ratios(nutrition_data):
    """Calculate macronutrient ratios as percentages of total calories"""
    if not nutrition_data or not nutrition_data.avg_calories:
        return {
            'protein_percentage': 0,
            'carbs_percentage': 0,
            'fat_percentage': 0
        }
    
    avg_protein = float(nutrition_data.avg_protein) if nutrition_data.avg_protein else 0
    avg_carbs = float(nutrition_data.avg_carbs) if nutrition_data.avg_carbs else 0
    avg_fat = float(nutrition_data.avg_fat) if nutrition_data.avg_fat else 0
    avg_calories = float(nutrition_data.avg_calories)
    
    # Calculate calories from each macro (protein=4cal/g, carbs=4cal/g, fat=9cal/g)
    protein_calories = avg_protein * 4
    carbs_calories = avg_carbs * 4
    fat_calories = avg_fat * 9
    
    # Calculate percentages
    protein_percentage = (protein_calories / avg_calories * 100) if avg_calories > 0 else 0
    carbs_percentage = (carbs_calories / avg_calories * 100) if avg_calories > 0 else 0
    fat_percentage = (fat_calories / avg_calories * 100) if avg_calories > 0 else 0
    
    return {
        'protein_percentage': round(protein_percentage, 1),
        'carbs_percentage': round(carbs_percentage, 1),
        'fat_percentage': round(fat_percentage, 1)
    }


def _calculate_food_quality_ratio(user_id, start_date, end_date):
    """Calculate ratio of whole foods vs processed foods based on food names"""
    # Get all food logs for the period
    food_logs = FoodLog.query.filter(
        FoodLog.user_id == user_id,
        FoodLog.date >= start_date,
        FoodLog.date <= end_date
    ).all()
    
    if not food_logs:
        return {
            'whole_food_percentage': 0,
            'processed_food_percentage': 0,
            'food_quality_score': 0
        }
    
    # Keywords that typically indicate whole foods
    whole_food_keywords = [
        'apple', 'banana', 'orange', 'broccoli', 'spinach', 'kale', 'carrot', 'tomato',
        'chicken breast', 'salmon', 'tuna', 'eggs', 'almonds', 'walnuts', 'quinoa',
        'brown rice', 'oats', 'sweet potato', 'avocado', 'blueberries', 'strawberries',
        'cucumber', 'bell pepper', 'onion', 'garlic', 'lemon', 'lime', 'beans', 'lentils'
    ]
    
    # Keywords that typically indicate processed foods
    processed_food_keywords = [
        'chips', 'cookies', 'cake', 'candy', 'soda', 'pizza', 'burger', 'fries',
        'ice cream', 'donut', 'crackers', 'cereal', 'bread', 'pasta', 'sauce',
        'dressing', 'frozen', 'canned', 'packaged', 'instant', 'processed'
    ]
    
    whole_food_count = 0
    processed_food_count = 0
    
    for log in food_logs:
        food_name = log.name.lower() if log.name else ''
        
        # Check if it's a whole food
        is_whole_food = any(keyword in food_name for keyword in whole_food_keywords)
        # Check if it's processed
        is_processed = any(keyword in food_name for keyword in processed_food_keywords)
        
        if is_whole_food and not is_processed:
            whole_food_count += 1
        elif is_processed:
            processed_food_count += 1
        # If neither, we don't count it (ambiguous foods)
    
    total_categorized = whole_food_count + processed_food_count
    
    if total_categorized == 0:
        return {
            'whole_food_percentage': 0,
            'processed_food_percentage': 0,
            'food_quality_score': 50  # Neutral score when we can't determine
        }
    
    whole_food_percentage = (whole_food_count / total_categorized * 100)
    processed_food_percentage = (processed_food_count / total_categorized * 100)
    
    # Quality score: higher percentage of whole foods = higher score
    food_quality_score = whole_food_percentage
    
    return {
        'whole_food_percentage': round(whole_food_percentage, 1),
        'processed_food_percentage': round(processed_food_percentage, 1),
        'food_quality_score': round(food_quality_score, 1)
    }


@api_bp.route('/api/ai-usage/current-user')
@login_required
def get_current_user_ai_usage():
    """Get current user's AI usage statistics"""
    try:
        today = date.today()
        
        # Get today's usage
        today_usage = db.session.query(func.count(AIUsageLog.id)).filter(
            AIUsageLog.user_id == current_user.id,
            func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        # Get this month's usage
        month_start = today.replace(day=1)
        month_usage = db.session.query(func.count(AIUsageLog.id)).filter(
            AIUsageLog.user_id == current_user.id,
            AIUsageLog.created_at >= month_start
        ).scalar() or 0
        
        # Get limits
        daily_limit = get_app_setting('ai_daily_limit_free', 10) if not current_user.has_premium_access() else get_app_setting('ai_daily_limit_premium', 50)
        monthly_limit = get_app_setting('ai_monthly_limit_free', 100) if not current_user.has_premium_access() else get_app_setting('ai_monthly_limit_premium', 1000)
        
        # Get today's token usage and cost
        today_tokens = db.session.query(
            func.sum(AIUsageLog.input_tokens + AIUsageLog.output_tokens)
        ).filter(
            AIUsageLog.user_id == current_user.id,
            func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        today_cost = db.session.query(
            func.sum(AIUsageLog.total_cost)
        ).filter(
            AIUsageLog.user_id == current_user.id,
            func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        # Return data in the format expected by the JavaScript
        return jsonify({
            'success': True,
            'usage': {
                'today': {
                    'calls': today_usage,
                    'tokens': today_tokens,
                    'cost': float(today_cost)
                }
            },
            'limits': {
                'daily_calls': daily_limit,
                'daily_tokens': 0,  # Not implemented yet
                'monthly_cost': 0   # Not implemented yet
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting AI usage: {e}")
        return jsonify({'success': False, 'error': 'Failed to get AI usage data'}), 500


@api_bp.route('/api/user-data-for-analysis')
@login_required
def get_user_data_for_analysis():
    """Get user data for AI analysis"""
    try:
        # Get date range from query parameters or default to last 7 days
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str and end_date_str:
            from datetime import datetime as dt
            start_date = dt.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = dt.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to last 7 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
        
        # Get food logs for the date range
        food_logs = FoodLog.query.filter(
            FoodLog.user_id == current_user.id,
            FoodLog.date >= start_date,
            FoodLog.date <= end_date
        ).order_by(FoodLog.timestamp.desc()).all()
        
        # Get water logs for the date range
        water_logs = WaterLog.query.filter(
            WaterLog.user_id == current_user.id,
            WaterLog.date >= start_date,
            WaterLog.date <= end_date
        ).order_by(WaterLog.timestamp.desc()).all()
        
        # Get mood logs for the date range
        mood_logs = MoodLog.query.filter(
            MoodLog.user_id == current_user.id,
            MoodLog.date >= start_date,
            MoodLog.date <= end_date
        ).order_by(MoodLog.timestamp.desc()).all()
        
        # Get notes for the date range
        notes = Note.query.filter(
            Note.user_id == current_user.id,
            Note.date >= start_date,
            Note.date <= end_date
        ).order_by(Note.timestamp.desc()).all()
        
        # Calculate 7-day and 30-day averages for efficient AI analysis
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Calculate nutrition averages for 7 days
        week_nutrition = db.session.query(
            func.avg(FoodLog.calories).label('avg_calories'),
            func.avg(FoodLog.protein).label('avg_protein'),
            func.avg(FoodLog.carbs).label('avg_carbs'),
            func.avg(FoodLog.fat).label('avg_fat'),
            func.avg(FoodLog.fiber).label('avg_fiber'),
            func.avg(FoodLog.sugar).label('avg_sugar'),
            func.count(FoodLog.id).label('total_entries')
        ).filter(
            FoodLog.user_id == current_user.id,
            FoodLog.date >= week_ago,
            FoodLog.date <= today
        ).first()
        
        # Calculate nutrition averages for 30 days
        month_nutrition = db.session.query(
            func.avg(FoodLog.calories).label('avg_calories'),
            func.avg(FoodLog.protein).label('avg_protein'),
            func.avg(FoodLog.carbs).label('avg_carbs'),
            func.avg(FoodLog.fat).label('avg_fat'),
            func.avg(FoodLog.fiber).label('avg_fiber'),
            func.avg(FoodLog.sugar).label('avg_sugar'),
            func.count(FoodLog.id).label('total_entries')
        ).filter(
            FoodLog.user_id == current_user.id,
            FoodLog.date >= month_ago,
            FoodLog.date <= today
        ).first()
        
        # Calculate water intake averages
        week_water = db.session.query(
            func.avg(WaterLog.amount).label('avg_daily_water'),
            func.count(WaterLog.id).label('total_entries')
        ).filter(
            WaterLog.user_id == current_user.id,
            WaterLog.date >= week_ago,
            WaterLog.date <= today
        ).first()
        
        month_water = db.session.query(
            func.avg(WaterLog.amount).label('avg_daily_water'),
            func.count(WaterLog.id).label('total_entries')
        ).filter(
            WaterLog.user_id == current_user.id,
            WaterLog.date >= month_ago,
            WaterLog.date <= today
        ).first()
        
        # Calculate mood averages
        week_mood = db.session.query(
            func.avg(MoodLog.mood).label('avg_mood'),
            func.count(MoodLog.id).label('total_entries')
        ).filter(
            MoodLog.user_id == current_user.id,
            MoodLog.date >= week_ago,
            MoodLog.date <= today
        ).first()
        
        month_mood = db.session.query(
            func.avg(MoodLog.mood).label('avg_mood'),
            func.count(MoodLog.id).label('total_entries')
        ).filter(
            MoodLog.user_id == current_user.id,
            MoodLog.date >= month_ago,
            MoodLog.date <= today
        ).first()
        
        # Get recent notes for context (limit to last 10 for efficiency)
        recent_notes = Note.query.filter(
            Note.user_id == current_user.id,
            Note.date >= week_ago
        ).order_by(Note.timestamp.desc()).limit(10).all()
        
        # Format optimized data for AI analysis
        data = {
            'user_info': {
                'age': current_user.age,
                'weight': current_user.weight,
                'height': current_user.height,
                'health_goals': current_user.health_goals,
                'ailments_concerns': current_user.ailments_concerns
            },
            'nutrition_summary': {
                'last_7_days': {
                    'avg_calories': float(week_nutrition.avg_calories) if week_nutrition.avg_calories else 0,
                    'avg_protein': float(week_nutrition.avg_protein) if week_nutrition.avg_protein else 0,
                    'avg_carbs': float(week_nutrition.avg_carbs) if week_nutrition.avg_carbs else 0,
                    'avg_fat': float(week_nutrition.avg_fat) if week_nutrition.avg_fat else 0,
                    'avg_fiber': float(week_nutrition.avg_fiber) if week_nutrition.avg_fiber else 0,
                    'avg_sugar': float(week_nutrition.avg_sugar) if week_nutrition.avg_sugar else 0,
                    'total_food_entries': week_nutrition.total_entries or 0,
                    **_calculate_macro_ratios(week_nutrition),
                    **_calculate_food_quality_ratio(current_user.id, week_ago, today)
                },
                'last_30_days': {
                    'avg_calories': float(month_nutrition.avg_calories) if month_nutrition.avg_calories else 0,
                    'avg_protein': float(month_nutrition.avg_protein) if month_nutrition.avg_protein else 0,
                    'avg_carbs': float(month_nutrition.avg_carbs) if month_nutrition.avg_carbs else 0,
                    'avg_fat': float(month_nutrition.avg_fat) if month_nutrition.avg_fat else 0,
                    'avg_fiber': float(month_nutrition.avg_fiber) if month_nutrition.avg_fiber else 0,
                    'avg_sugar': float(month_nutrition.avg_sugar) if month_nutrition.avg_sugar else 0,
                    'total_food_entries': month_nutrition.total_entries or 0,
                    **_calculate_macro_ratios(month_nutrition),
                    **_calculate_food_quality_ratio(current_user.id, month_ago, today)
                }
            },
            'water_summary': {
                'last_7_days': {
                    'avg_daily_water': float(week_water.avg_daily_water) if week_water.avg_daily_water else 0,
                    'total_entries': week_water.total_entries or 0
                },
                'last_30_days': {
                    'avg_daily_water': float(month_water.avg_daily_water) if month_water.avg_daily_water else 0,
                    'total_entries': month_water.total_entries or 0
                }
            },
            'mood_summary': {
                'last_7_days': {
                    'avg_mood': float(week_mood.avg_mood) if week_mood.avg_mood else 0,
                    'total_entries': week_mood.total_entries or 0
                },
                'last_30_days': {
                    'avg_mood': float(month_mood.avg_mood) if month_mood.avg_mood else 0,
                    'total_entries': month_mood.total_entries or 0
                }
            },
            'recent_notes': [{
                'content': note.content,
                'date': note.date.isoformat() if note.date else None
            } for note in recent_notes],
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_days': (end_date - start_date).days + 1
            }
        }
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        current_app.logger.error(f"Error getting user data for analysis: {e}")
        return jsonify({'success': False, 'error': 'Failed to get user data'}), 500


@api_bp.route('/api/get-stored-analysis')
@login_required
def get_stored_analysis():
    """Get the most recent stored AI analysis for the user"""
    try:
        # Get the most recent analysis for the user
        analysis = AIAnalysis.query.filter_by(
            user_id=current_user.id
        ).order_by(AIAnalysis.created_at.desc()).first()
        
        if analysis:
            # Parse the JSON analysis data
            try:
                analysis_data = json.loads(analysis.analysis_data) if isinstance(analysis.analysis_data, str) else analysis.analysis_data
            except json.JSONDecodeError:
                # If JSON parsing fails, return a fallback analysis
                analysis_data = {
                    "patterns": [
                        {"title": "Analysis Update Required", "description": "Your analysis data needs to be updated. Please refresh your analysis to get new insights."}
                    ],
                    "suggestions": [
                        {"title": "Refresh Analysis", "description": "Click the refresh button to generate updated insights based on your recent wellness data."}
                    ]
                }
            
            return jsonify({
                'success': True,
                'analysis': analysis_data,
                'created_at': analysis.created_at.isoformat(),
                'updated_at': analysis.updated_at.isoformat() if analysis.updated_at else None
            })
        else:
            return jsonify({'success': True, 'analysis': None})
    except Exception as e:
        current_app.logger.error(f"Error getting stored analysis: {e}")
        return jsonify({'success': False, 'error': 'Failed to get stored analysis'}), 500


# Note: /api/generate-ai-analysis route moved to routes/ai.py to avoid duplication
# Note: /api/food-log, /api/water-log, /api/mood-log, /api/notes routes moved to routes/food.py to avoid duplication