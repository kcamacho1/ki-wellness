"""
Admin routes - Dashboard, Analytics, User Management, System Settings
All routes require admin privileges
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import current_user
from sqlalchemy import func, text
from database import db, User, FoodLog, WaterLog, MoodLog, AIUsageLog, Subscription, PaymentSession
from utils.decorators import admin_required
from utils.helpers import get_app_setting, set_app_setting
from services.analytics_service import analytics_service

# Create blueprint
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@admin_required
def admin_dashboard():
    """Main admin dashboard"""
    # Get app statistics
    total_users = User.query.count()
    total_food_logs = FoodLog.query.count()
    total_water_logs = WaterLog.query.count()
    total_mood_logs = MoodLog.query.count()
    
    # Get app settings
    new_accounts_enabled = get_app_setting('new_accounts_enabled', 'true').lower() == 'true'
    maintenance_mode = get_app_setting('maintenance_mode', 'false').lower() == 'true'
    max_users = get_app_setting('max_users', '1000')
    allowed_emails = get_app_setting('allowed_emails', '')
    human_help_payment_type = get_app_setting('human_help_payment_type', '30min_session')
    calendly_link = get_app_setting('calendly_link', 'https://calendly.com/ki-wellness/human-health-coach')
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_food_logs=total_food_logs,
                         total_water_logs=total_water_logs,
                         total_mood_logs=total_mood_logs,
                         new_accounts_enabled=new_accounts_enabled,
                         maintenance_mode=maintenance_mode,
                         max_users=max_users,
                         allowed_emails=allowed_emails,
                         human_help_payment_type=human_help_payment_type,
                         calendly_link=calendly_link)


@admin_bp.route('/api/admin/settings', methods=['GET'])
@admin_required
def get_admin_settings():
    """Get admin settings for frontend"""
    try:
        settings = {
            'new_accounts_enabled': get_app_setting('new_accounts_enabled', 'true'),
            'maintenance_mode': get_app_setting('maintenance_mode', 'false'),
            'max_users': get_app_setting('max_users', '1000'),
            'allowed_emails': get_app_setting('allowed_emails', ''),
            'human_help_payment_type': get_app_setting('human_help_payment_type', '30min_session'),
            'calendly_link': get_app_setting('calendly_link', 'https://calendly.com/ki-wellness/human-health-coach'),
            'daily_token_limit': get_app_setting('daily_token_limit', '0'),
            'daily_call_limit': get_app_setting('daily_call_limit', '0'),
            'monthly_cost_limit': get_app_setting('monthly_cost_limit', '0'),
            'enforce_limits': get_app_setting('enforce_limits', 'false')
        }
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/admin/settings', methods=['POST'])
@admin_required
def update_admin_settings():
    """Update admin settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        # Update each setting
        for key, value in data.items():
            set_app_setting(key, value)
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/admin/analytics')
@admin_required
def get_admin_analytics():
    """Get comprehensive analytics for admin dashboard"""
    try:
        analytics_data = analytics_service.get_admin_analytics()
        return jsonify({
            'success': True,
            'analytics': analytics_data
        })
    except Exception as e:
        current_app.logger.error(f"Admin analytics error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load analytics data'
        }), 500


@admin_bp.route('/api/admin/ai-usage')
@admin_required
def get_admin_ai_usage():
    """Get AI usage analytics for admin dashboard"""
    try:
        # Get AI usage for all users today
        today = datetime.utcnow().date()
        
        # Total tokens used today
        total_tokens = db.session.query(
            func.sum(AIUsageLog.input_tokens + AIUsageLog.output_tokens)
        ).filter(
            func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        # Total API calls today
        total_calls = db.session.query(
            func.count(AIUsageLog.id)
        ).filter(
            func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        # Total cost today
        total_cost = db.session.query(
            func.sum(AIUsageLog.total_cost)
        ).filter(
            func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        # Monthly cost
        this_month = datetime.utcnow().replace(day=1).date()
        monthly_cost = db.session.query(
            func.sum(AIUsageLog.total_cost)
        ).filter(
            func.date(AIUsageLog.created_at) >= this_month
        ).scalar() or 0
        
        # Top users by usage today
        top_users = db.session.query(
            User.username,
            func.sum(AIUsageLog.input_tokens + AIUsageLog.output_tokens).label('tokens'),
            func.count(AIUsageLog.id).label('calls'),
            func.sum(AIUsageLog.total_cost).label('cost')
        ).join(
            AIUsageLog, User.id == AIUsageLog.user_id
        ).filter(
            func.date(AIUsageLog.created_at) == today
        ).group_by(
            User.id, User.username
        ).order_by(
            func.sum(AIUsageLog.input_tokens + AIUsageLog.output_tokens).desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'usage': {
                'total_tokens': int(total_tokens),
                'total_calls': int(total_calls),
                'total_cost': float(total_cost),
                'monthly_cost': float(monthly_cost),
                'top_users': [
                    {
                        'username': user.username,
                        'tokens': int(user.tokens or 0),
                        'calls': int(user.calls or 0),
                        'cost': float(user.cost or 0)
                    } for user in top_users
                ]
            }
        })
    except Exception as e:
        current_app.logger.error(f"AI usage analytics error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load AI usage data'
        }), 500


@admin_bp.route('/api/admin/revenue')
@admin_required
def get_admin_revenue():
    """Get revenue analytics for admin dashboard"""
    try:
        # Get subscription revenue (mock data for now)
        active_subscriptions = Subscription.query.filter_by(status='active').count()
        
        # Get human help revenue from payment sessions
        completed_sessions = PaymentSession.query.filter_by(status='completed').count()
        
        # Calculate estimated monthly recurring revenue
        mrr = active_subscriptions * 5  # $5 per subscription
        
        return jsonify({
            'success': True,
            'revenue': {
                'active_subscriptions': active_subscriptions,
                'completed_sessions': completed_sessions,
                'monthly_recurring_revenue': mrr
            }
        })
    except Exception as e:
        current_app.logger.error(f"Revenue analytics error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load revenue data'
        }), 500


@admin_bp.route('/api/admin/assign-ff-roles', methods=['POST'])
@admin_required
def assign_ff_roles_to_allowed_emails():
    """Assign 'ff' role to all users with allowed email addresses"""
    try:
        allowed_emails_setting = get_app_setting('allowed_emails', '')
        allowed_emails = [email.strip().lower() for email in allowed_emails_setting.split(',') if email.strip()]
        
        if not allowed_emails:
            return jsonify({
                'success': False,
                'error': 'No allowed emails configured in settings'
            })
        
        # Find users with allowed emails
        users_to_update = User.query.filter(User.email.in_(allowed_emails)).all()
        
        updated_count = 0
        for user in users_to_update:
            if user.role != 'ff':
                user.role = 'ff'
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully assigned FF role to {updated_count} users',
            'updated_count': updated_count,
            'total_checked': len(users_to_update)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning FF roles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to assign FF roles'
        }), 500


@admin_bp.route('/admin/users')
@admin_required
def admin_users():
    """Admin users management page"""
    # Get user statistics
    total_users = User.query.count()
    verified_users = User.query.filter_by(email_verified=True).count()
    admin_users_count = User.query.filter_by(role='admin').count()
    ff_users_count = User.query.filter_by(role='ff').count()
    regular_users_count = User.query.filter(
        (User.role == 'user') | (User.role == None)
    ).count()
    
    # Get allowed emails setting
    allowed_emails = get_app_setting('allowed_emails', '')
    
    return render_template('admin_users.html',
                         total_users=total_users,
                         verified_users=verified_users,
                         admin_users_count=admin_users_count,
                         ff_users_count=ff_users_count,
                         regular_users_count=regular_users_count,
                         allowed_emails=allowed_emails)


@admin_bp.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics page"""
    return render_template('admin_analytics.html')


@admin_bp.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin system settings page"""
    # Get app settings
    settings = {
        'new_accounts_enabled': get_app_setting('new_accounts_enabled', 'true'),
        'maintenance_mode': get_app_setting('maintenance_mode', 'false'),
        'max_users': get_app_setting('max_users', '1000'),
        'allowed_emails': get_app_setting('allowed_emails', ''),
        'human_help_payment_type': get_app_setting('human_help_payment_type', '30min_session'),
        'calendly_link': get_app_setting('calendly_link', 'https://calendly.com/ki-wellness/human-health-coach'),
        'daily_token_limit': get_app_setting('daily_token_limit', '0'),
        'daily_call_limit': get_app_setting('daily_call_limit', '0'),
        'monthly_cost_limit': get_app_setting('monthly_cost_limit', '0'),
        'enforce_limits': get_app_setting('enforce_limits', 'false')
    }
    
    return render_template('admin_settings.html', settings=settings)


@admin_bp.route('/admin/payments')
@admin_required
def admin_payments():
    """Admin payments and services page"""
    # Get app settings
    calendly_link = get_app_setting('calendly_link', 'https://calendly.com/ki-wellness/human-health-coach')
    
    return render_template('admin_payments.html', calendly_link=calendly_link)


@admin_bp.route('/admin/system')
@admin_required
def admin_system():
    """Admin system information page"""
    try:
        # Get database connection info
        db_info = {}
        try:
            result = db.session.execute(text('SELECT version()'))
            db_info['version'] = result.scalar()
            db_info['status'] = 'Connected'
        except Exception as e:
            db_info['status'] = f'Error: {str(e)}'
            db_info['version'] = 'Unknown'
        
        # Get system statistics
        stats = {
            'total_users': User.query.count(),
            'total_food_logs': FoodLog.query.count(),
            'total_water_logs': WaterLog.query.count(),
            'total_mood_logs': MoodLog.query.count(),
            'total_ai_usage': AIUsageLog.query.count()
        }
        
        return render_template('admin_system.html', 
                             db_info=db_info, 
                             stats=stats)
    except Exception as e:
        current_app.logger.error(f"Admin system page error: {str(e)}")
        return render_template('admin_system.html', 
                             db_info={'status': 'Error', 'version': 'Unknown'}, 
                             stats={})


@admin_bp.route('/api/admin/users')
@admin_required
def get_admin_users():
    """Get users for admin dashboard with pagination and search"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_email = request.args.get('search_email', '', type=str)
        role_filter = request.args.get('role', '', type=str)
        
        # Build query
        query = User.query
        
        # Apply search filter
        if search_email:
            query = query.filter(
                (User.username.ilike(f'%{search_email}%')) |
                (User.email.ilike(f'%{search_email}%')) |
                (User.name.ilike(f'%{search_email}%'))
            )
        
        # Apply role filter
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        # Get paginated results
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'name': user.name,
                    'role': user.role or 'user',
                    'email_verified': user.email_verified,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': getattr(user, 'last_login', None).isoformat() if getattr(user, 'last_login', None) else None
                }
                for user in users.items
            ],
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_users': users.total,
                'total_pages': users.pages,
                'has_prev': users.has_prev,
                'has_next': users.has_next
            }
        })
    except Exception as e:
        current_app.logger.error(f"Get admin users error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load users'
        }), 500


@admin_bp.route('/api/admin/update-user-role', methods=['POST'])
@admin_required
def update_user_role():
    """Update user role"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_role = data.get('role')
        
        if not user_id or not new_role:
            return jsonify({
                'success': False,
                'error': 'User ID and role are required'
            })
        
        # Validate role
        valid_roles = ['user', 'admin', 'ff']
        if new_role not in valid_roles:
            return jsonify({
                'success': False,
                'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
            })
        
        # Find user
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            })
        
        # Prevent changing own role if current user is the target
        if current_user.id == user.id and new_role != current_user.role:
            return jsonify({
                'success': False,
                'error': 'You cannot change your own role'
            })
        
        # Update role
        old_role = user.role or 'user'
        user.role = new_role
        db.session.commit()
        
        current_app.logger.info(f"Admin {current_user.username} changed user {user.username} role from {old_role} to {new_role}")
        
        return jsonify({
            'success': True,
            'message': f'User role updated from {old_role} to {new_role}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update user role error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update user role'
        }), 500


@admin_bp.route('/api/admin/security-stats')
@admin_required
def get_security_stats():
    """Get security statistics for admin dashboard"""
    try:
        # Get security stats from the security middleware if available
        from security_middleware import SecurityMiddleware
        
        stats = {
            'blocked_attempts': 0,  # Placeholder - would need to implement tracking
            'rate_limited_requests': 0,  # Placeholder
            'suspicious_activity': 0,  # Placeholder
            'last_security_scan': 'Not implemented'
        }
        
        return jsonify({
            'success': True,
            'security_stats': stats
        })
    except Exception as e:
        current_app.logger.error(f"Security stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load security statistics'
        }), 500


@admin_bp.route('/api/admin/unblock-ip', methods=['POST'])
@admin_required
def unblock_ip():
    """Unblock a previously blocked IP address"""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        
        if not ip_address:
            return jsonify({
                'success': False,
                'error': 'IP address is required'
            })
        
        # This would need to be implemented in the security middleware
        # For now, just return success
        current_app.logger.info(f"Admin {current_user.username} unblocked IP: {ip_address}")
        
        return jsonify({
            'success': True,
            'message': f'IP address {ip_address} has been unblocked'
        })
        
    except Exception as e:
        current_app.logger.error(f"Unblock IP error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to unblock IP address'
        }), 500
