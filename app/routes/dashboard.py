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
from ..models import db, MoodEntry, FoodJournal
from ..services import UserService, AIService
from ..decorators import login_required
from ..utils.dashboard_utils import (
    DashboardDataService, DashboardStatsService, DashboardDateService,
    DashboardResponseService, DashboardValidationService, DashboardCacheService,
    DashboardAnalyticsService
)

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
            return DashboardResponseService.error_response('User not found', 404)
        
        # Check if user can use AI
        if not DashboardDataService.can_user_use_ai(current_user.id):
            return DashboardResponseService.verification_required_response()
        
        # Get browser timezone
        browser_timezone = DashboardDataService.get_browser_timezone()
        
        # For now, return basic patterns data structure
        # This can be enhanced later with actual AI analysis
        patterns_data = DashboardResponseService.new_user_response()
        
        return jsonify(patterns_data)
        
    except Exception as e:
        print(f"❌ Error getting patterns: {e}")
        return DashboardResponseService.error_response('Failed to get patterns', 500)


@dashboard_bp.route('/dashboard/patterns/refresh', methods=['POST'])
@login_required
def refresh_patterns():
    """Refresh AI patterns analysis"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return DashboardResponseService.error_response('User not found', 404)
        
        # Check if user can use AI
        if not DashboardDataService.can_user_use_ai(current_user.id):
            return DashboardResponseService.error_response('AI features not available', 403)
        
        # Trigger AI analysis
        result = AIService.analyze_patterns_with_openai(current_user.id)
        
        if result['success']:
            return jsonify(DashboardResponseService.success_response(
                data=result.get('patterns', {}),
                message='Patterns refreshed successfully!'
            ))
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Failed to refresh patterns')}), 500
        
    except Exception as e:
        print(f"❌ Error refreshing patterns: {e}")
        return jsonify({'success': False, 'error': 'Failed to refresh patterns'}), 500


@dashboard_bp.route('/dashboard/water/add', methods=['POST'])
@login_required
def add_water():
    """Add water intake as food journal entry"""
    try:
        data = request.get_json()
        browser_timezone = data.get('browser_timezone', 'UTC')
        
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Parse target date from request or use current time
        target_date = data.get('target_date')
        if target_date:
            try:
                consumed_at = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            except ValueError:
                consumed_at = datetime.utcnow()
        else:
            consumed_at = datetime.utcnow()
        
        # Create water entry as a food journal entry
        water_entry = FoodJournal(
            user_id=current_user.id,
            food_name="Water",
            brand="",
            serving_size=8,
            serving_unit="oz",
            calories=0,
            protein=0,
            carbs=0,
            fat=0,
            fiber=0,
            sugar=0,
            sodium=0,
            time_of_day="snack",
            consumed_at=consumed_at,
            mood=None,
            notes="Quick add water intake"
        )
        
        db.session.add(water_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Added 8 oz of water!',
            'entry': {
                'id': water_entry.id,
                'food_name': water_entry.food_name,
                'serving_size': water_entry.serving_size,
                'serving_unit': water_entry.serving_unit,
                'calories': water_entry.calories,
                'consumed_at': water_entry.consumed_at.isoformat()
            }
        })
        
    except Exception as e:
        print(f"❌ Error adding water: {e}")
        db.session.rollback()
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
        
        # Parse target date from request or use current time
        target_date = data.get('target_date')
        if target_date:
            try:
                logged_at = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            except ValueError:
                logged_at = datetime.utcnow()
        else:
            logged_at = datetime.utcnow()
        
        # Create mood entry
        mood_entry = MoodEntry(
            user_id=current_user.id,
            mood=mood_score,
            notes=notes,
            logged_at=logged_at
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
            query = query.filter(MoodEntry.logged_at >= start_date)
        if end_date:
            query = query.filter(MoodEntry.logged_at <= end_date + ' 23:59:59')
        
        entries = query.order_by(MoodEntry.logged_at.desc(), MoodEntry.created_at.desc()).all()
        
        results = []
        for entry in entries:
            results.append({
                'id': entry.id,
                'mood': entry.mood,
                'notes': entry.notes,
                'logged_at': entry.logged_at.isoformat(),
                'created_at': entry.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'entries': results
        })
        
    except Exception as e:
        print(f"❌ Error getting mood entries: {e}")
        return jsonify({'success': False, 'error': 'Failed to get mood entries'}), 500
