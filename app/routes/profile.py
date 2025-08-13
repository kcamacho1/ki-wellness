"""
Ki Wellness - Profile Routes
============================

This module contains user profile management routes including
profile viewing, editing, and settings management.

Author: Ki Wellness Team
Version: 2.0
"""

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from ..models import db, User, UserProfile
from ..services import UserService
from ..utils import ValidationUtils
from ..decorators import login_required

# Create blueprint
profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html')


@profile_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('settings.html')


@profile_bp.route('/profile/save', methods=['POST'])
@login_required
def save_profile():
    """Save user profile data"""
    try:
        data = request.get_json()
        current_user = UserService.get_current_user()
        user_profile = UserService.get_current_user_profile()
        
        if not current_user or not user_profile:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Update profile fields
        if 'name' in data:
            user_profile.name = data['name'].strip()
        if 'age' in data:
            user_profile.age = int(data['age']) if data['age'] else None
        if 'gender' in data:
            user_profile.gender = data['gender']
        if 'height' in data:
            user_profile.height = float(data['height']) if data['height'] else None
        if 'weight' in data:
            user_profile.weight = float(data['weight']) if data['weight'] else None
        if 'weight_unit' in data:
            user_profile.weight_unit = data['weight_unit']
        if 'activity_level' in data:
            user_profile.activity_level = data['activity_level']
        if 'goal' in data:
            user_profile.goal = data['goal']
        if 'dietary_restrictions' in data:
            user_profile.dietary_restrictions = data['dietary_restrictions']
        if 'allergies' in data:
            user_profile.allergies = data['allergies']
        if 'medical_conditions' in data:
            user_profile.medical_conditions = data['medical_conditions']
        if 'medications' in data:
            user_profile.medications = data['medications']
        if 'avatar' in data:
            user_profile.avatar = data['avatar']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error saving profile: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to save profile'}), 500


@profile_bp.route('/profile/data')
@login_required
def get_profile_data():
    """Get user profile data"""
    try:
        current_user = UserService.get_current_user()
        user_profile = UserService.get_current_user_profile()
        
        if not current_user or not user_profile:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        profile_data = {
            'username': current_user.username,
            'email': current_user.email,
            'name': user_profile.name,
            'age': user_profile.age,
            'gender': user_profile.gender,
            'height': user_profile.height,
            'weight': user_profile.weight,
            'weight_unit': user_profile.weight_unit,
            'activity_level': user_profile.activity_level,
            'goal': user_profile.goal,
            'dietary_restrictions': user_profile.dietary_restrictions,
            'allergies': user_profile.allergies,
            'medical_conditions': user_profile.medical_conditions,
            'medications': user_profile.medications,
            'avatar': user_profile.avatar,
            'created_at': user_profile.created_at.isoformat() if user_profile.created_at else None,
            'updated_at': user_profile.updated_at.isoformat() if user_profile.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'data': profile_data
        })
        
    except Exception as e:
        print(f"❌ Error getting profile data: {e}")
        return jsonify({'success': False, 'error': 'Failed to get profile data'}), 500


@profile_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Current and new password are required'}), 400
        
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        if not ValidationUtils.validate_password_strength(new_password):
            return jsonify({'success': False, 'error': 'New password does not meet requirements'}), 400
        
        # Set new password
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error changing password: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to change password'}), 500
