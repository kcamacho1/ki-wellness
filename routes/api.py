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
# Pexels client removed - only used in separate script
from services.r2_client import r2_client
from botocore.exceptions import ClientError

# Import utilities
from utils.decorators import premium_required, admin_required
from utils.helpers import get_app_setting, check_ai_usage_limits
from security_middleware import rate_limit, sanitize_input
from utils.helpers import validate_user_input, sanitize_user_input
import re

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


# Pexels API endpoints removed - only used in separate script


@api_bp.route('/r2/stats', methods=['GET'])
@login_required
@admin_required
def get_r2_stats():
    """
    Get R2 storage statistics (admin only)
    """
    try:
        stats = r2_client.get_storage_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        current_app.logger.error(f"Error getting R2 stats: {e}")
        return jsonify({'success': False, 'error': 'Failed to get R2 stats'}), 500


@api_bp.route('/r2/upload', methods=['POST'])
@login_required
@rate_limit(max_requests=10, window=60)  # Reduced rate limit for security
def upload_to_r2():
    """
    Upload file to R2 storage with enhanced security
    """
    try:
        # CSRF protection
        if not request.form.get('csrf_token'):
            return jsonify({'success': False, 'error': 'CSRF token required'}), 400
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file size (basic validation only since we'll transform the image)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size < 1024:  # At least 1KB
            return jsonify({'success': False, 'error': 'File too small (min 1KB). Please select a valid image file.'}), 400
        
        # Sanitize folder name to prevent path traversal
        folder = request.form.get('folder', 'uploads')
        folder = sanitize_folder_name(folder)
        
        # Read file data
        file_data = file.read()
        
        # Validate file content and ensure it's a food image
        validation_result = validate_food_image(file_data, file.filename)
        if not validation_result['valid']:
            return jsonify({'success': False, 'error': validation_result['error']}), 400
        
        # Upload to R2
        result = r2_client.upload_file(
            file_data=file_data,
            filename=file.filename,
            folder=folder
        )
        
        if result:
            # Log successful upload for security monitoring
            current_app.logger.info(f"File uploaded to R2 by user {current_user.id}: {file.filename}")
            return jsonify({
                'success': True,
                'file': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Upload failed'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error uploading to R2: {e}")
        return jsonify({'success': False, 'error': 'Upload failed'}), 500


@api_bp.route('/api/r2/proxy/<path:object_key>', methods=['GET'])
def proxy_r2_image(object_key):
    """
    Proxy R2 images to avoid CORS issues
    This endpoint serves R2 images through the Flask app to bypass CORS restrictions
    """
    try:
        if not r2_client.is_available():
            return jsonify({'error': 'R2 storage not available'}), 503
        
        # Get file from R2
        response = r2_client.s3_client.get_object(
            Bucket=r2_client.bucket_name,
            Key=object_key
        )
        
        # Get file content and metadata
        file_data = response['Body'].read()
        content_type = response.get('ContentType', 'application/octet-stream')
        
        # Create Flask response with proper headers
        from flask import Response
        return Response(
            file_data,
            mimetype=content_type,
            headers={
                'Cache-Control': 'public, max-age=31536000',  # Cache for 1 year
                'Access-Control-Allow-Origin': '*',  # Allow CORS
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return jsonify({'error': 'Image not found'}), 404
        return jsonify({'error': 'Failed to retrieve image'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# Security helper functions for R2 uploads
def sanitize_folder_name(folder_name: str) -> str:
    """
    Sanitize folder name to prevent path traversal attacks
    """
    if not folder_name:
        return 'uploads'
    
    # Remove dangerous characters and path traversal attempts
    folder_name = re.sub(r'[^a-zA-Z0-9_-]', '', folder_name)
    
    # Prevent path traversal
    if '..' in folder_name or '/' in folder_name or '\\' in folder_name:
        return 'uploads'
    
    # Limit length
    if len(folder_name) > 50:
        folder_name = folder_name[:50]
    
    return folder_name or 'uploads'

def validate_file_content(file_data: bytes, filename: str) -> bool:
    """
    Validate file content to ensure it's a safe image file
    """
    try:
        # File size validation removed since we'll transform the image
        
        # Check file signature (magic bytes)
        if len(file_data) < 4:
            return False
        
        # Image file signatures
        image_signatures = {
            b'\xFF\xD8\xFF': 'jpeg',
            b'\x89PNG\r\n\x1a\n': 'png',
            b'GIF87a': 'gif',
            b'GIF89a': 'gif',
            b'RIFF': 'webp',  # WebP starts with RIFF
        }
        
        # Check for valid image signatures
        is_valid_image = False
        for signature, file_type in image_signatures.items():
            if file_data.startswith(signature):
                is_valid_image = True
                break
        
        if not is_valid_image:
            return False
        
        # Additional validation for WebP
        if file_data.startswith(b'RIFF') and b'WEBP' not in file_data[:12]:
            return False
        
        # Check file extension matches content
        file_ext = os.path.splitext(filename)[1].lower()
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        if file_ext not in allowed_extensions:
            return False
        
        # Basic content validation - check for executable content
        dangerous_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'data:text/html',
            b'<?php',
            b'#!/bin/',
            b'MZ',  # PE executable
        ]
        
        for pattern in dangerous_patterns:
            if pattern in file_data.lower():
                return False
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"File validation error: {e}")
        return False

def validate_food_image(file_data: bytes, filename: str) -> dict:
    """
    Validate that the uploaded image is actually a food image
    Returns dict with 'valid' boolean and 'error' message
    """
    try:
        # First, basic file validation
        if not validate_file_content(file_data, filename):
            return {'valid': False, 'error': 'Invalid file type or content'}
        
        # File size validation removed since we'll transform the image
        if len(file_data) < 1024:  # At least 1KB
            return {'valid': False, 'error': 'File too small (min 1KB)'}
        
        # Check filename for food-related keywords
        filename_lower = filename.lower()
        food_keywords = [
            'food', 'meal', 'dish', 'recipe', 'cooking', 'kitchen', 'dinner', 'lunch', 'breakfast',
            'snack', 'dessert', 'soup', 'salad', 'pasta', 'pizza', 'burger', 'sandwich',
            'chicken', 'beef', 'fish', 'vegetable', 'fruit', 'bread', 'cake', 'cookie'
        ]
        
        # Check if filename contains food-related keywords
        has_food_keyword = any(keyword in filename_lower for keyword in food_keywords)
        
        # Check for non-food keywords that should be rejected
        non_food_keywords = [
            'document', 'pdf', 'text', 'screenshot', 'photo', 'image', 'picture', 'selfie',
            'portrait', 'landscape', 'nature', 'animal', 'person', 'face', 'body',
            'logo', 'icon', 'banner', 'advertisement', 'ad', 'promo'
        ]
        
        has_non_food_keyword = any(keyword in filename_lower for keyword in non_food_keywords)
        
        # If filename has non-food keywords but no food keywords, reject
        if has_non_food_keyword and not has_food_keyword:
            return {'valid': False, 'error': 'Please upload food-related images only'}
        
        # Check image dimensions (basic validation)
        try:
            from PIL import Image
            import io
            
            # Open image to check dimensions
            image = Image.open(io.BytesIO(file_data))
            width, height = image.size
            
            # Check if image is too small (likely not a proper food photo)
            if width < 100 or height < 100:
                return {'valid': False, 'error': 'Image too small (min 100x100 pixels)'}
            
            # Check if image is too large (likely not a food photo)
            if width > 8000 or height > 8000:
                return {'valid': False, 'error': 'Image too large (max 8000x8000 pixels). Please use a smaller image.'}
            
            # Check aspect ratio (food images should be reasonable)
            aspect_ratio = width / height
            if aspect_ratio > 5 or aspect_ratio < 0.2:  # Very wide or very tall
                return {'valid': False, 'error': 'Please upload properly proportioned food images'}
            
        except ImportError:
            # PIL not available, skip dimension checks
            pass
        except Exception as e:
            # If we can't read the image, it's probably not a valid image
            return {'valid': False, 'error': 'Invalid image format'}
        
        # Basic content analysis for food-related patterns
        # Look for common food-related metadata or content patterns
        content_lower = file_data.lower()
        
        # Check for common non-food content patterns
        non_food_patterns = [
            b'screenshot', b'desktop', b'window', b'dialog', b'menu',
            b'button', b'text', b'document', b'pdf', b'office',
            b'person', b'face', b'portrait', b'selfie'
        ]
        
        for pattern in non_food_patterns:
            if pattern in content_lower:
                return {'valid': False, 'error': 'Please upload food-related images only'}
        
        # If we get here, the image passes basic validation
        return {'valid': True, 'error': None}
        
    except Exception as e:
        current_app.logger.error(f"Food image validation error: {e}")
        return {'valid': False, 'error': 'Image validation failed'}

def sanitize_recipe_data(recipe: dict) -> dict:
    """
    Sanitize recipe data to prevent injection attacks
    """
    sanitized = {}
    
    for key, value in recipe.items():
        if isinstance(value, str):
            # Remove potentially dangerous characters
            sanitized[key] = re.sub(r'[<>"\';(){}[\]\\]', '', value)[:500]  # Limit length
        elif isinstance(value, list):
            # Sanitize list items
            sanitized[key] = []
            for item in value:
                if isinstance(item, str):
                    sanitized[key].append(re.sub(r'[<>"\';(){}[\]\\]', '', item)[:200])
                elif isinstance(item, dict):
                    sanitized[key].append(sanitize_recipe_data(item))
                else:
                    sanitized[key].append(item)
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = sanitize_recipe_data(value)
        else:
            sanitized[key] = value
    
    return sanitized

# Note: /api/generate-ai-analysis route moved to routes/ai.py to avoid duplication
# Note: /api/food-log, /api/water-log, /api/mood-log, /api/notes routes moved to routes/food.py to avoid duplication