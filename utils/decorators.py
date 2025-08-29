"""
Decorators for authentication and authorization
"""
from functools import wraps
from flask import jsonify, redirect, url_for
from flask_login import current_user


def premium_required(f):
    """Decorator to require premium subscription or special role access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Admin and ff users always have access
        if current_user.has_premium_access():
            return f(*args, **kwargs)
        
        # Regular users need active premium subscription
        return jsonify({
            'success': False, 
            'error': 'Premium subscription required',
            'requires_upgrade': True,
            'message': 'You need a premium subscription to access this feature. Upgrade now for just $5/month!'
        }), 403
    
    return decorated_function


def admin_required(f):
    """Decorator to require admin role access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.can_access_admin_dashboard():
            return jsonify({
                'success': False, 
                'error': 'Admin access required',
                'message': 'You do not have permission to access this feature.'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function
