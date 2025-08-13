"""
Ki Wellness - Profile Utilities
==============================

Reusable Python utilities for profile operations
Can be used across different profile-related routes

Author: Ki Wellness Team
Version: 2.0
"""

from datetime import datetime
from typing import Dict, Any, Optional
from flask import jsonify
from ..models import db, User, UserProfile


class ProfileUtils:
    """Utility class for profile operations"""
    
    @staticmethod
    def get_default_profile_data(user: User) -> Dict[str, Any]:
        """Get default profile data for a user"""
        return {
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'name': user.username,
            'age': None,
            'gender': None,
            'date_of_birth': None,
            'height': None,
            'height_ft': None,
            'weight': None,
            'weight_unit': 'kg',
            'goal': None,
            'goals': None,
            'custom_goal': None,
            'ailments': None,
            'dietary_preferences': None,
            'sleep_schedule': None,
            'daily_activities': None,
            'exercise_routine': None,
            'day_notes': None,
            'night_notes': None,
            'spiritual_religion': None,
            'self_connection': None,
            'surroundings_connection': None,
            'providing_others': None,
            'safe_groups': None,
            'awe_things': None,
            'creative_expression': None,
            'upsetting_situations': None,
            'spirit_notes': None,
            'avatar': 'default-avatar.png',
            'created_at': None,
            'updated_at': None
        }
    
    @staticmethod
    def get_profile_data(user: User, profile: Optional[UserProfile]) -> Dict[str, Any]:
        """Get profile data for API response"""
        if not profile:
            return ProfileUtils.get_default_profile_data(user)
        
        return {
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'name': profile.name,
            'age': profile.age,
            'gender': profile.gender,
            'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            'height': profile.height,
            'height_ft': profile.height_ft,
            'weight': profile.weight,
            'weight_unit': profile.weight_unit,
            'goal': profile.goal,
            'goals': profile.goals,
            'custom_goal': profile.custom_goal,
            'ailments': profile.ailments,
            'dietary_preferences': profile.dietary_preferences,
            'sleep_schedule': profile.sleep_schedule,
            'daily_activities': profile.daily_activities,
            'exercise_routine': profile.exercise_routine,
            'day_notes': profile.day_notes,
            'night_notes': profile.night_notes,
            'spiritual_religion': profile.spiritual_religion,
            'self_connection': profile.self_connection,
            'surroundings_connection': profile.surroundings_connection,
            'providing_others': profile.providing_others,
            'safe_groups': profile.safe_groups,
            'awe_things': profile.awe_things,
            'creative_expression': profile.creative_expression,
            'upsetting_situations': profile.upsetting_situations,
            'spirit_notes': profile.spirit_notes,
            'avatar': profile.avatar,
            'created_at': profile.created_at.isoformat() if profile.created_at else None,
            'updated_at': profile.updated_at.isoformat() if profile.updated_at else None
        }
    
    @staticmethod
    def update_profile_fields(profile: UserProfile, data: Dict[str, Any]) -> None:
        """Update profile fields from request data"""
        field_mappings = {
            'name': ('name', str, lambda x: x.strip()),
            'age': ('age', int, None),
            'gender': ('gender', str, None),
            'date_of_birth': ('date_of_birth', datetime, lambda x: datetime.strptime(x, '%Y-%m-%d').date() if x else None),
            'height': ('height', float, None),
            'height_ft': ('height_ft', float, None),
            'weight': ('weight', float, None),
            'weight_unit': ('weight_unit', str, None),
            'goal': ('goal', str, None),
            'goals': ('goals', str, None),
            'custom_goal': ('custom_goal', str, None),
            'ailments': ('ailments', str, None),
            'dietary_preferences': ('dietary_preferences', str, None),
            'sleep_schedule': ('sleep_schedule', str, None),
            'daily_activities': ('daily_activities', str, None),
            'exercise_routine': ('exercise_routine', str, None),
            'day_notes': ('day_notes', str, None),
            'night_notes': ('night_notes', str, None),
            'spiritual_religion': ('spiritual_religion', str, None),
            'self_connection': ('self_connection', str, None),
            'surroundings_connection': ('surroundings_connection', str, None),
            'providing_others': ('providing_others', str, None),
            'safe_groups': ('safe_groups', str, None),
            'awe_things': ('awe_things', str, None),
            'creative_expression': ('creative_expression', str, None),
            'upsetting_situations': ('upsetting_situations', str, None),
            'spirit_notes': ('spirit_notes', str, None),
            'avatar': ('avatar', str, None)
        }
        
        for field_name, (attr_name, field_type, processor) in field_mappings.items():
            if field_name in data:
                value = data[field_name]
                if value is not None and value != '':
                    if processor:
                        value = processor(value)
                    if value is not None:
                        setattr(profile, attr_name, value)
                        # Debug: Log height field updates
                        if field_name == 'height':
                            print(f"✅ Height field updated: {value} cm")
                elif field_name in ['date_of_birth']:  # Allow clearing date fields
                    setattr(profile, attr_name, None)
    
    @staticmethod
    def create_profile_response(success: bool, data: Optional[Dict[str, Any]] = None, 
                              message: str = '', error: str = '') -> Dict[str, Any]:
        """Create standardized profile API response"""
        response = {'success': success}
        
        if success:
            if data:
                response['data'] = data
            if message:
                response['message'] = message
        else:
            if error:
                response['error'] = error
        
        return response
    
    @staticmethod
    def validate_profile_data(data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate profile data"""
        # Validate age
        if 'age' in data and data['age']:
            try:
                age = int(data['age'])
                if age < 0 or age > 150:
                    return False, "Age must be between 0 and 150"
            except ValueError:
                return False, "Age must be a valid number"
        
        # Validate height
        if 'height' in data and data['height']:
            try:
                height = float(data['height'])
                if height < 0 or height > 300:
                    return False, "Height must be between 0 and 300 cm"
            except ValueError:
                return False, "Height must be a valid number"
        
        # Validate weight
        if 'weight' in data and data['weight']:
            try:
                weight = float(data['weight'])
                if weight < 0 or weight > 1000:
                    return False, "Weight must be between 0 and 1000"
            except ValueError:
                return False, "Weight must be a valid number"
        
        # Validate date of birth
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
                if dob > datetime.now().date():
                    return False, "Date of birth cannot be in the future"
            except ValueError:
                return False, "Date of birth must be in YYYY-MM-DD format"
        
        return True, ""


class ProfileResponseBuilder:
    """Builder class for creating profile API responses"""
    
    @staticmethod
    def success(data: Optional[Dict[str, Any]] = None, message: str = '') -> Dict[str, Any]:
        """Create success response"""
        return ProfileUtils.create_profile_response(True, data, message)
    
    @staticmethod
    def error(error: str) -> Dict[str, Any]:
        """Create error response"""
        return ProfileUtils.create_profile_response(False, error=error)
    
    @staticmethod
    def profile_data(user: User, profile: Optional[UserProfile]) -> Dict[str, Any]:
        """Create profile data response"""
        data = ProfileUtils.get_profile_data(user, profile)
        return ProfileResponseBuilder.success(data)
    
    @staticmethod
    def profile_saved() -> Dict[str, Any]:
        """Create profile saved response"""
        return ProfileResponseBuilder.success(message='Profile updated successfully!')
    
    @staticmethod
    def password_changed() -> Dict[str, Any]:
        """Create password changed response"""
        return ProfileResponseBuilder.success(message='Password changed successfully!')
    
    @staticmethod
    def user_not_found() -> Dict[str, Any]:
        """Create user not found response"""
        return ProfileResponseBuilder.error('User not found')
    
    @staticmethod
    def validation_error(message: str) -> Dict[str, Any]:
        """Create validation error response"""
        return ProfileResponseBuilder.error(message)
    
    @staticmethod
    def server_error() -> Dict[str, Any]:
        """Create server error response"""
        return ProfileResponseBuilder.error('Internal server error')


def handle_profile_operation(operation_func, *args, **kwargs):
    """Decorator-like function to handle profile operations with error handling"""
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        print(f"❌ Error in profile operation: {e}")
        db.session.rollback()
        return ProfileResponseBuilder.server_error()
