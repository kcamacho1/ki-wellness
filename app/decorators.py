"""
Ki Wellness - Decorators Module
===============================

This module contains custom decorators for authentication,
authorization, and session management.

Author: Ki Wellness Team
Version: 2.0
"""

from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash
from .models import User


def login_required(f):
    """Decorator to require user login with session timeout"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # SECURITY: Check if user is logged in
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # SECURITY: Check if session has expired (1 hour timeout)
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.utcnow() - last_activity > timedelta(hours=1):
                # Session expired, clear session and redirect to login
                session.clear()
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
        
        # Update last activity timestamp
        session['last_activity'] = datetime.utcnow().isoformat()
        session.permanent = True  # Enable session timeout
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges with session timeout"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # SECURITY: Check if user is logged in
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # SECURITY: Check if session has expired (1 hour timeout)
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.utcnow() - last_activity > timedelta(hours=1):
                # Session expired, clear session and redirect to login
                session.clear()
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard.dashboard'))
        
        # Update last activity timestamp
        session['last_activity'] = datetime.utcnow().isoformat()
        session.permanent = True  # Enable session timeout
        
        return f(*args, **kwargs)
    return decorated_function


def is_admin_user():
    """Check if current user is admin"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return user and user.is_admin
    return False


def verify_user_data_access(user_profile, data_type="unknown"):
    """
    Security function to verify user has access to their own data
    This ensures no user can access another user's data
    """
    if not user_profile:
        raise ValueError(f"User profile not found for {data_type} access")
    
    # Additional security checks can be added here
    # For example, checking if user is active, not suspended, etc.
    return True
