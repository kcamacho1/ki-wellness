"""
Ki Wellness - Dashboard Utilities
================================

This module contains utility functions for dashboard functionality,
extracting reusable patterns from dashboard routes and services.

Author: Ki Wellness Team
Version: 1.0
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from flask import jsonify, request
import pytz

from ..models import db, User, UserProfile, FoodJournal, MoodEntry


class DashboardDataService:
    """Service class for dashboard data operations"""
    
    @staticmethod
    def get_user_verification_status(user_id: int) -> Dict[str, bool]:
        """Get user verification status"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'email_verified': False, 'phone_verified': False}
            
            return {
                'email_verified': user.email_verified or False,
                'phone_verified': user.phone_verified or False
            }
        except Exception as e:
            print(f"Error getting user verification status: {e}")
            return {'email_verified': False, 'phone_verified': False}
    
    @staticmethod
    def can_user_use_ai(user_id: int) -> bool:
        """Check if user can use AI features"""
        try:
            # Import here to avoid circular import
            from ..services import UserService
            return UserService.can_user_use_ai(user_id)
        except Exception as e:
            print(f"Error checking AI access: {e}")
            return False
    
    @staticmethod
    def get_user_timezone(user_id: int) -> str:
        """Get user's timezone"""
        try:
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            return profile.timezone if profile and profile.timezone else 'UTC'
        except Exception as e:
            print(f"Error getting user timezone: {e}")
            return 'UTC'
    
    @staticmethod
    def get_browser_timezone() -> str:
        """Get browser timezone from request"""
        try:
            return request.args.get('browser_timezone', 'UTC')
        except Exception as e:
            print(f"Error getting browser timezone: {e}")
            return 'UTC'


class DashboardStatsService:
    """Service class for dashboard statistics calculations"""
    
    @staticmethod
    def calculate_water_intake(entries: List[Dict]) -> float:
        """Calculate total water intake in ounces"""
        total_water = 0.0
        
        for entry in entries:
            # Check for water_amount and water_unit fields (legacy water tracking)
            if entry.get('water_amount') and entry.get('water_unit'):
                water_amount = float(entry['water_amount'])
                water_unit = entry['water_unit']
                
                # Convert to ounces
                if water_unit == 'oz':
                    total_water += water_amount
                elif water_unit == 'liters':
                    total_water += water_amount * 33.814
                elif water_unit == 'gallons':
                    total_water += water_amount * 128
            
            # Check for water entries in food journal (new water tracking)
            elif entry.get('food_name') and entry.get('food_name').lower() == 'water':
                serving_size = float(entry.get('serving_size', 0))
                serving_unit = entry.get('serving_unit', 'oz')
                
                # Convert to ounces
                if serving_unit == 'oz':
                    total_water += serving_size
                elif serving_unit == 'liters':
                    total_water += serving_size * 33.814
                elif serving_unit == 'gallons':
                    total_water += serving_size * 128
                elif serving_unit == 'ml':
                    total_water += serving_size * 0.033814
                elif serving_unit == 'cups':
                    total_water += serving_size * 8
        
        return total_water
    
    @staticmethod
    def calculate_macronutrients(entries: List[Dict]) -> Dict[str, float]:
        """Calculate total macronutrients"""
        total_protein = 0.0
        total_carbs = 0.0
        total_fat = 0.0
        total_calories = 0.0
        
        for entry in entries:
            if entry.get('protein'):
                total_protein += float(entry['protein'])
            if entry.get('carbs'):
                total_carbs += float(entry['carbs'])
            if entry.get('fat'):
                total_fat += float(entry['fat'])
            if entry.get('calories'):
                total_calories += float(entry['calories'])
        
        return {
            'protein': total_protein,
            'carbs': total_carbs,
            'fat': total_fat,
            'calories': total_calories
        }
    
    @staticmethod
    def calculate_average_mood(moods: List[str]) -> Dict[str, str]:
        """Calculate average mood from mood list"""
        if not moods:
            return {'emoji': '😐', 'text': 'No mood data'}
        
        mood_scores = {
            'happy': 5, 'great': 5, 'excellent': 5, 'amazing': 5,
            'good': 4, 'fine': 4, 'okay': 4, 'alright': 4,
            'neutral': 3, 'meh': 3, 'average': 3,
            'sad': 2, 'bad': 2, 'terrible': 2, 'awful': 2,
            'angry': 1, 'frustrated': 1, 'stressed': 1
        }
        
        total_score = 0
        valid_moods = 0
        
        for mood in moods:
            lower_mood = mood.lower()
            for key, score in mood_scores.items():
                if key in lower_mood:
                    total_score += score
                    valid_moods += 1
                    break
        
        if valid_moods == 0:
            return {'emoji': '😐', 'text': 'Neutral'}
        
        average_score = total_score / valid_moods
        
        if average_score >= 4.5:
            return {'emoji': '😄', 'text': 'Excellent'}
        elif average_score >= 3.5:
            return {'emoji': '🙂', 'text': 'Good'}
        elif average_score >= 2.5:
            return {'emoji': '😐', 'text': 'Neutral'}
        elif average_score >= 1.5:
            return {'emoji': '😔', 'text': 'Not Great'}
        else:
            return {'emoji': '😢', 'text': 'Poor'}


class DashboardDateService:
    """Service class for date handling in dashboard"""
    
    @staticmethod
    def get_date_range(days: int, timezone: str = 'UTC') -> Tuple[datetime, datetime]:
        """Get date range for specified number of days"""
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            start_date = now - timedelta(days=days)
            return start_date, now
        except Exception as e:
            print(f"Error getting date range: {e}")
            # Fallback to UTC
            now = datetime.utcnow()
            start_date = now - timedelta(days=days)
            return start_date, now
    
    @staticmethod
    def format_date_for_display(date: datetime, timezone: str = 'UTC') -> str:
        """Format date for display in user's timezone"""
        try:
            if not date.tzinfo:
                tz = pytz.timezone(timezone)
                date = tz.localize(date)
            
            return date.strftime('%a, %b %d, %I:%M %p')
        except Exception as e:
            print(f"Error formatting date: {e}")
            return date.strftime('%Y-%m-%d %H:%M')
    
    @staticmethod
    def get_today_string(timezone: str = 'UTC') -> str:
        """Get today's date string in YYYY-MM-DD format"""
        try:
            tz = pytz.timezone(timezone)
            today = datetime.now(tz)
            return today.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Error getting today string: {e}")
            return datetime.utcnow().strftime('%Y-%m-%d')


class DashboardResponseService:
    """Service class for standardized dashboard responses"""
    
    @staticmethod
    def success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
        """Create success response"""
        response = {'success': True}
        if data is not None:
            response['data'] = data
        if message:
            response['message'] = message
        return response
    
    @staticmethod
    def error_response(error: str, status_code: int = 400) -> Tuple[Dict[str, Any], int]:
        """Create error response"""
        return jsonify({'success': False, 'error': error}), status_code
    
    @staticmethod
    def verification_required_response() -> Tuple[Dict[str, Any], int]:
        """Create verification required response"""
        return jsonify({'success': False, 'error': 'verification_required'}), 403
    
    @staticmethod
    def new_user_response() -> Dict[str, Any]:
        """Create new user call-to-action response"""
        return {
            'success': True,
            'is_new_user': True,
            'needs_more_data': False,
            'call_to_action': {
                'title': 'Start Your Wellness Journey',
                'description': 'Begin tracking your meals and mood to unlock personalized AI insights and recommendations.',
                'actions': [
                    {
                        'title': 'Add Your First Meal',
                        'description': 'Log what you ate today to start building your nutrition profile.',
                        'icon': '🍽️',
                        'action': 'add_food'
                    },
                    {
                        'title': 'Track Your Mood',
                        'description': 'Record how you\'re feeling to understand your wellness patterns.',
                        'icon': '😊',
                        'action': 'add_mood'
                    }
                ]
            },
            'patterns': {},
            'suggestions': {},
            'cache_info': {
                'seven_day_updated': False
            }
        }


class DashboardValidationService:
    """Service class for dashboard data validation"""
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """Validate date range format and logic"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            return start <= end
        except ValueError:
            return False
    
    @staticmethod
    def validate_mood_entry(mood: str, notes: str = None) -> Tuple[bool, str]:
        """Validate mood entry data"""
        if not mood or not mood.strip():
            return False, "Mood is required"
        
        if len(mood) > 100:
            return False, "Mood text too long"
        
        if notes and len(notes) > 500:
            return False, "Notes too long"
        
        return True, ""
    
    @staticmethod
    def validate_water_entry(amount: float, unit: str) -> Tuple[bool, str]:
        """Validate water entry data"""
        if amount <= 0:
            return False, "Water amount must be positive"
        
        if amount > 1000:  # 1000 oz = ~30 liters
            return False, "Water amount too high"
        
        valid_units = ['oz', 'liters', 'gallons']
        if unit not in valid_units:
            return False, "Invalid water unit"
        
        return True, ""


class DashboardCacheService:
    """Service class for dashboard caching operations"""
    
    @staticmethod
    def should_refresh_patterns(user_id: int, last_updated: datetime) -> bool:
        """Check if patterns should be refreshed"""
        try:
            # Refresh if last update was more than 24 hours ago
            if not last_updated:
                return True
            
            now = datetime.utcnow()
            time_diff = now - last_updated
            
            return time_diff.total_seconds() > 86400  # 24 hours
        except Exception as e:
            print(f"Error checking pattern refresh: {e}")
            return True
    
    @staticmethod
    def get_cache_info(user_id: int) -> Dict[str, Any]:
        """Get cache information for user"""
        try:
            # This would typically check against a cache table
            # For now, return basic structure
            return {
                'seven_day_updated': False,
                'thirty_day_updated': False,
                'last_refresh': None
            }
        except Exception as e:
            print(f"Error getting cache info: {e}")
            return {
                'seven_day_updated': False,
                'thirty_day_updated': False,
                'last_refresh': None
            }


class DashboardAnalyticsService:
    """Service class for dashboard analytics"""
    
    @staticmethod
    def get_user_stats(user_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get comprehensive user stats for date range"""
        try:
            # Get food journal entries
            food_entries = FoodJournal.query.filter(
                FoodJournal.user_id == user_id,
                FoodJournal.consumed_at >= start_date,
                FoodJournal.consumed_at <= end_date
            ).all()
            
            # Get mood entries
            mood_entries = MoodEntry.query.filter(
                MoodEntry.user_id == user_id,
                MoodEntry.created_at >= start_date,
                MoodEntry.created_at <= end_date
            ).all()
            
            # Convert to dictionaries
            food_data = [entry.to_dict() for entry in food_entries]
            mood_data = [entry.to_dict() for entry in mood_entries]
            
            # Calculate statistics
            water_intake = DashboardStatsService.calculate_water_intake(food_data)
            macros = DashboardStatsService.calculate_macronutrients(food_data)
            
            # Get moods from both food entries and mood entries
            all_moods = []
            for entry in food_data:
                if entry.get('mood'):
                    all_moods.append(entry['mood'])
            for entry in mood_data:
                if entry.get('mood'):
                    all_moods.append(entry['mood'])
            
            average_mood = DashboardStatsService.calculate_average_mood(all_moods)
            
            return {
                'water_intake': water_intake,
                'macros': macros,
                'average_mood': average_mood,
                'total_entries': len(food_data),
                'total_mood_entries': len(mood_data),
                'date_range': {
                    'start': start_date,
                    'end': end_date
                }
            }
            
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {
                'water_intake': 0,
                'macros': {'protein': 0, 'carbs': 0, 'fat': 0, 'calories': 0},
                'average_mood': {'emoji': '😐', 'text': 'No data'},
                'total_entries': 0,
                'total_mood_entries': 0,
                'date_range': {'start': start_date, 'end': end_date}
            }
    
    @staticmethod
    def get_patterns_analysis(user_id: int) -> Dict[str, Any]:
        """Get AI patterns analysis for user"""
        try:
            # Check if user can use AI
            if not DashboardDataService.can_user_use_ai(user_id):
                return DashboardResponseService.verification_required_response()
            
            # Get AI analysis
            # Import here to avoid circular import
            from ..services import AIService
            result = AIService.analyze_patterns_with_openai(user_id)
            
            if result.get('success'):
                return DashboardResponseService.success_response(result.get('data'))
            else:
                return DashboardResponseService.error_response(
                    result.get('error', 'Failed to analyze patterns')
                )
                
        except Exception as e:
            print(f"Error getting patterns analysis: {e}")
            return DashboardResponseService.error_response('Failed to analyze patterns')
