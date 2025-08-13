"""
Ki Wellness - Profile Routes
============================

This module contains user profile management routes including
profile viewing, editing, and settings management.
Uses modular components and utilities for reusability.

Author: Ki Wellness Team
Version: 2.0
"""

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from ..models import db, User, UserProfile
from ..services import UserService
from ..utils import ValidationUtils, ProfileUtils, ProfileResponseBuilder, handle_profile_operation
from ..decorators import login_required

# Create blueprint
profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user_profile = UserService.get_current_user_profile()
    # If no profile exists, create a default one and save it to database
    if not user_profile:
        current_user = UserService.get_current_user()
        user_profile = UserProfile(
            user_id=current_user.id,
            name=current_user.username,
            avatar='default-avatar.png',
            weight_unit='kg'
        )
        # Save the profile to database so it can be retrieved by other endpoints
        db.session.add(user_profile)
        db.session.commit()
    return render_template('profile.html', profile=user_profile)


@profile_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('settings.html')


@profile_bp.route('/profile/save', methods=['POST'])
@login_required
def save_profile():
    """Save user profile data using modular utilities"""
    def save_profile_operation():
        data = request.get_json()
        # Debug: Log height-related data
        print(f"🔍 Save profile data received: height = {data.get('height')}, height_input = {data.get('height_input')}")
        
        current_user = UserService.get_current_user()
        user_profile = UserService.get_current_user_profile()
        
        if not current_user:
            return ProfileResponseBuilder.user_not_found()
        
        # Create profile if it doesn't exist
        if not user_profile:
            user_profile = UserProfile(
                user_id=current_user.id,
                name=current_user.username,
                avatar='default-avatar.png',
                weight_unit='kg'
            )
            db.session.add(user_profile)
        
        # Validate profile data
        is_valid, error_message = ProfileUtils.validate_profile_data(data)
        if not is_valid:
            return ProfileResponseBuilder.validation_error(error_message)
        
        # Update profile fields using utility
        ProfileUtils.update_profile_fields(user_profile, data)
        
        db.session.commit()
        return ProfileResponseBuilder.profile_saved()
    
    return jsonify(handle_profile_operation(save_profile_operation))


@profile_bp.route('/profile/data')
@login_required
def get_profile_data():
    """Get user profile data using modular utilities"""
    def get_profile_data_operation():
        current_user = UserService.get_current_user()
        user_profile = UserService.get_current_user_profile()
        
        if not current_user:
            return ProfileResponseBuilder.user_not_found()
        
        return ProfileResponseBuilder.profile_data(current_user, user_profile)
    
    return jsonify(handle_profile_operation(get_profile_data_operation))


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
