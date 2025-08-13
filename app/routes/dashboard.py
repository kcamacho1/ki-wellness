"""
Ki Wellness - Dashboard Routes
==============================

This module contains dashboard routes for user analytics,
patterns analysis, and wellness tracking.

Author: Ki Wellness Team
Version: 2.0
"""

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from ..models import db, MoodEntry
from ..services import UserService, AIService
from ..decorators import login_required

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')


@dashboard_bp.route('/dashboard/patterns')
@login_required
def dashboard_patterns():
    """Get patterns analysis data"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check if user can use AI
        if not UserService.can_user_use_ai(current_user.id):
            return jsonify({'success': False, 'error': 'verification_required'}), 403
        
        # For now, return basic patterns data structure
        # This can be enhanced later with actual AI analysis
        patterns_data = {
            'success': True,
            'is_new_user': True,  # Set to True for now to show call-to-action
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
        
        return jsonify(patterns_data)
        
    except Exception as e:
        print(f"❌ Error getting patterns: {e}")
        return jsonify({'success': False, 'error': 'Failed to get patterns'}), 500


@dashboard_bp.route('/dashboard/patterns/refresh', methods=['POST'])
@login_required
def refresh_patterns():
    """Refresh AI patterns analysis"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check if user can use AI
        if not UserService.can_user_use_ai(current_user.id):
            return jsonify({'success': False, 'error': 'AI features not available'}), 403
        
        # Trigger AI analysis
        result = AIService.analyze_patterns_with_openai(current_user.id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Patterns refreshed successfully!',
                'patterns': result.get('patterns', {})
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Failed to refresh patterns')}), 500
        
    except Exception as e:
        print(f"❌ Error refreshing patterns: {e}")
        return jsonify({'success': False, 'error': 'Failed to refresh patterns'}), 500


@dashboard_bp.route('/dashboard/water/add', methods=['POST'])
@login_required
def add_water():
    """Add water intake"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        
        if not amount or amount <= 0:
            return jsonify({'success': False, 'error': 'Valid amount is required'}), 400
        
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Add water entry (this would be implemented based on your water tracking model)
        # For now, just return success
        return jsonify({
            'success': True,
            'message': f'Added {amount}ml of water!'
        })
        
    except Exception as e:
        print(f"❌ Error adding water: {e}")
        return jsonify({'success': False, 'error': 'Failed to add water'}), 500


@dashboard_bp.route('/dashboard/mood/add', methods=['POST'])
@login_required
def add_mood():
    """Add mood entry"""
    try:
        data = request.get_json()
        mood_score = data.get('mood_score')
        notes = data.get('notes', '').strip()
        
        if not mood_score or not isinstance(mood_score, int) or mood_score < 1 or mood_score > 10:
            return jsonify({'success': False, 'error': 'Valid mood score (1-10) is required'}), 400
        
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Create mood entry
        mood_entry = MoodEntry(
            user_id=current_user.id,
            mood_score=mood_score,
            notes=notes,
            date=datetime.utcnow().date()
        )
        
        db.session.add(mood_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mood entry added successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error adding mood: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to add mood entry'}), 500


@dashboard_bp.route('/dashboard/mood/entries')
@login_required
def get_mood_entries():
    """Get user's mood entries"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = MoodEntry.query.filter_by(user_id=current_user.id)
        
        if start_date:
            query = query.filter(MoodEntry.date >= start_date)
        if end_date:
            query = query.filter(MoodEntry.date <= end_date)
        
        entries = query.order_by(MoodEntry.date.desc(), MoodEntry.created_at.desc()).all()
        
        results = []
        for entry in entries:
            results.append({
                'id': entry.id,
                'mood_score': entry.mood_score,
                'notes': entry.notes,
                'date': entry.date.isoformat(),
                'created_at': entry.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'entries': results
        })
        
    except Exception as e:
        print(f"❌ Error getting mood entries: {e}")
        return jsonify({'success': False, 'error': 'Failed to get mood entries'}), 500
