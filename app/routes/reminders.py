"""
Ki Wellness - Reminders Routes
==============================

This module contains reminder system routes for creating,
managing, and triggering wellness reminders.

Author: Ki Wellness Team
Version: 2.0
"""

import json
from flask import Blueprint, render_template, request, jsonify, make_response
from datetime import datetime, timedelta, time
from ..models import db, Reminder, ReminderLog, Notification
from ..services import UserService
from ..decorators import login_required
from ..utils import TimeUtils

# Create blueprint
reminders_bp = Blueprint('reminders', __name__)


@reminders_bp.route('/reminders')
@login_required
def reminders():
    """Reminders page"""
    return render_template('reminders.html')


@reminders_bp.route('/api/reminders', methods=['GET'])
@login_required
def get_reminders():
    """Get user's reminders"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        reminders = Reminder.query.filter_by(user_id=current_user.id).order_by(Reminder.created_at.desc()).all()
        
        results = []
        for reminder in reminders:
            results.append({
                'id': reminder.id,
                'title': reminder.title,
                'description': reminder.description,
                'reminder_type': reminder.reminder_type,
                'frequency': reminder.frequency,
                'time_of_day': reminder.time_of_day.strftime('%H:%M') if reminder.time_of_day else None,
                'days_of_week': json.loads(reminder.days_of_week) if reminder.days_of_week else [],
                'is_active': reminder.is_active,
                'created_at': reminder.created_at.isoformat(),
                'updated_at': reminder.updated_at.isoformat() if reminder.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'reminders': results
        })
        
    except Exception as e:
        print(f"❌ Error getting reminders: {e}")
        return jsonify({'success': False, 'error': 'Failed to get reminders'}), 500


@reminders_bp.route('/api/reminders', methods=['POST'])
@login_required
def create_reminder():
    """Create a new reminder"""
    try:
        data = request.get_json()
        current_user = UserService.get_current_user()
        
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Validate required fields
        title = data.get('title', '').strip()
        reminder_type = data.get('reminder_type')
        frequency = data.get('frequency')
        
        if not title or not reminder_type or not frequency:
            return jsonify({'success': False, 'error': 'Title, type, and frequency are required'}), 400
        
        # Parse time if provided
        time_of_day = None
        if 'time_of_day' in data:
            time_parts = data['time_of_day'].split(':')
            time_of_day = time(int(time_parts[0]), int(time_parts[1]))
        
        # Create reminder
        reminder = Reminder(
            user_id=current_user.id,
            title=title,
            description=data.get('description', ''),
            reminder_type=reminder_type,
            frequency=frequency,
            time_of_day=time_of_day,
            days_of_week=json.dumps(data.get('days_of_week', [])) if data.get('days_of_week') else None,
            is_active=True
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reminder created successfully!',
            'reminder_id': reminder.id
        })
        
    except Exception as e:
        print(f"❌ Error creating reminder: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to create reminder'}), 500


@reminders_bp.route('/api/reminders/<int:reminder_id>', methods=['PUT'])
@login_required
def update_reminder(reminder_id):
    """Update a reminder"""
    try:
        data = request.get_json()
        current_user = UserService.get_current_user()
        
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Find reminder
        reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first()
        if not reminder:
            return jsonify({'success': False, 'error': 'Reminder not found'}), 404
        
        # Update fields
        if 'title' in data:
            reminder.title = data['title'].strip()
        if 'description' in data:
            reminder.description = data['description']
        if 'reminder_type' in data:
            reminder.reminder_type = data['reminder_type']
        if 'frequency' in data:
            reminder.frequency = data['frequency']
        if 'time_of_day' in data:
            time_parts = data['time_of_day'].split(':')
            reminder.time_of_day = time(int(time_parts[0]), int(time_parts[1]))
        if 'days_of_week' in data:
            reminder.days_of_week = json.dumps(data['days_of_week']) if data['days_of_week'] else None
        if 'is_active' in data:
            reminder.is_active = data['is_active']
        
        reminder.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reminder updated successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error updating reminder: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to update reminder'}), 500


@reminders_bp.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
@login_required
def delete_reminder(reminder_id):
    """Delete a reminder"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Find and delete reminder
        reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first()
        if not reminder:
            return jsonify({'success': False, 'error': 'Reminder not found'}), 404
        
        db.session.delete(reminder)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reminder deleted successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error deleting reminder: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete reminder'}), 500


@reminders_bp.route('/api/reminders/<int:reminder_id>/trigger', methods=['POST'])
@login_required
def trigger_reminder(reminder_id):
    """Manually trigger a reminder"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Find reminder
        reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first()
        if not reminder:
            return jsonify({'success': False, 'error': 'Reminder not found'}), 404
        
        # Create reminder log
        log_entry = ReminderLog(
            reminder_id=reminder.id,
            triggered_at=datetime.utcnow(),
            status='manual'
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reminder triggered successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error triggering reminder: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to trigger reminder'}), 500


@reminders_bp.route('/api/notification-preferences', methods=['GET'])
@login_required
def get_notification_preferences():
    """Get user's notification preferences"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get notification preferences
        preferences = Notification.query.filter_by(user_id=current_user.id).first()
        
        if preferences:
            return jsonify({
                'success': True,
                'preferences': {
                    'email_notifications': preferences.email_notifications,
                    'sms_notifications': preferences.sms_notifications,
                    'push_notifications': preferences.push_notifications,
                    'reminder_notifications': preferences.reminder_notifications,
                    'weekly_reports': preferences.weekly_reports
                }
            })
        else:
            return jsonify({
                'success': True,
                'preferences': {
                    'email_notifications': True,
                    'sms_notifications': False,
                    'push_notifications': True,
                    'reminder_notifications': True,
                    'weekly_reports': True
                }
            })
        
    except Exception as e:
        print(f"❌ Error getting notification preferences: {e}")
        return jsonify({'success': False, 'error': 'Failed to get notification preferences'}), 500


@reminders_bp.route('/api/notification-preferences', methods=['PUT'])
@login_required
def update_notification_preferences():
    """Update user's notification preferences"""
    try:
        data = request.get_json()
        current_user = UserService.get_current_user()
        
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get or create notification preferences
        preferences = Notification.query.filter_by(user_id=current_user.id).first()
        if not preferences:
            preferences = Notification(user_id=current_user.id)
            db.session.add(preferences)
        
        # Update preferences
        if 'email_notifications' in data:
            preferences.email_notifications = data['email_notifications']
        if 'sms_notifications' in data:
            preferences.sms_notifications = data['sms_notifications']
        if 'push_notifications' in data:
            preferences.push_notifications = data['push_notifications']
        if 'reminder_notifications' in data:
            preferences.reminder_notifications = data['reminder_notifications']
        if 'weekly_reports' in data:
            preferences.weekly_reports = data['weekly_reports']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification preferences updated successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error updating notification preferences: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to update notification preferences'}), 500


@reminders_bp.route('/api/reminders/check', methods=['POST'])
@login_required
def check_reminders():
    """Check for due reminders"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get active reminders
        active_reminders = Reminder.query.filter_by(user_id=current_user.id, is_active=True).all()
        
        due_reminders = []
        current_time = datetime.utcnow()
        current_day = current_time.strftime('%A').lower()
        
        for reminder in active_reminders:
            # Check if reminder is due based on frequency and time
            if reminder.frequency == 'daily':
                if reminder.time_of_day and current_time.time() >= reminder.time_of_day:
                    due_reminders.append({
                        'id': reminder.id,
                        'title': reminder.title,
                        'description': reminder.description,
                        'type': reminder.reminder_type
                    })
            elif reminder.frequency == 'weekly':
                days_of_week = json.loads(reminder.days_of_week) if reminder.days_of_week else []
                if current_day in days_of_week and reminder.time_of_day and current_time.time() >= reminder.time_of_day:
                    due_reminders.append({
                        'id': reminder.id,
                        'title': reminder.title,
                        'description': reminder.description,
                        'type': reminder.reminder_type
                    })
        
        return jsonify({
            'success': True,
            'due_reminders': due_reminders
        })
        
    except Exception as e:
        print(f"❌ Error checking reminders: {e}")
        return jsonify({'success': False, 'error': 'Failed to check reminders'}), 500


@reminders_bp.route('/api/reminders/export-calendar', methods=['POST'])
@login_required
def export_reminders_calendar():
    """Export reminders as ICS calendar file"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get user's reminders
        reminders = Reminder.query.filter_by(user_id=current_user.id, is_active=True).all()
        
        # Generate ICS content
        ics_content = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Ki Wellness//Reminders//EN',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH'
        ]
        
        for reminder in reminders:
            # Create calendar event for each reminder
            event_id = f"reminder_{reminder.id}"
            summary = reminder.title
            description = reminder.description or ''
            
            if reminder.frequency == 'daily':
                # Daily reminder - create recurring event
                ics_content.extend([
                    'BEGIN:VEVENT',
                    f'UID:{event_id}',
                    f'SUMMARY:{summary}',
                    f'DESCRIPTION:{description}',
                    'DTSTART:20240101T080000Z',  # Start from Jan 1, 2024
                    'RRULE:FREQ=DAILY',
                    'END:VEVENT'
                ])
            elif reminder.frequency == 'weekly':
                # Weekly reminder - create recurring event
                days_of_week = json.loads(reminder.days_of_week) if reminder.days_of_week else []
                if days_of_week:
                    byday = ','.join([day[:2].upper() for day in days_of_week])
                    ics_content.extend([
                        'BEGIN:VEVENT',
                        f'UID:{event_id}',
                        f'SUMMARY:{summary}',
                        f'DESCRIPTION:{description}',
                        'DTSTART:20240101T080000Z',  # Start from Jan 1, 2024
                        f'RRULE:FREQ=WEEKLY;BYDAY={byday}',
                        'END:VEVENT'
                    ])
        
        ics_content.append('END:VCALENDAR')
        
        # Create response
        response = make_response('\r\n'.join(ics_content))
        response.headers['Content-Type'] = 'text/calendar'
        response.headers['Content-Disposition'] = f'attachment; filename=ki_wellness_reminders_{datetime.now().strftime("%Y%m%d")}.ics'
        
        return response
        
    except Exception as e:
        print(f"❌ Error exporting reminders calendar: {e}")
        return jsonify({'success': False, 'error': 'Failed to export calendar'}), 500
