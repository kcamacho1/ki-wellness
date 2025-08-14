"""
Ki Wellness - Main Application
==============================

This is the main Flask application entry point that orchestrates
all the modular components and handles the remaining routes.

Author: Ki Wellness Team
Version: 2.0
"""

import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session, make_response
from sqlalchemy import text, inspect

# Import new modular components
from .models import db, init_db, User, UserProfile, FoodJournal, MoodEntry, PatternsCache, Review, UserAgreement, Reminder, ReminderLog, Notification, SystemSettings, TokenUsage, APICosts, UserSubscription, SessionCredits, AIUsageSession
from .utils import ValidationUtils, SecurityUtils, TimeUtils, ConversionUtils, NotificationUtils, DataQualityUtils
from .utils.database_health import init_health_monitor, log_database_health, check_database_health, safe_check_database_health
from .services import SystemService, UserService, NutritionService, AIService
from .config import create_app, limiter, oauth, google_oauth, OAUTH_AVAILABLE, STRIPE_AVAILABLE, get_stripe_config, create_admin_account, ensure_tables_exist
from .decorators import login_required, admin_required, is_admin_user, verify_user_data_access
from .routes.auth import auth_bp
from .routes.static import static_bp
from .routes.subscription import subscription_bp
from .routes.profile import profile_bp
from .routes.dashboard import dashboard_bp
from .routes.food_journal import food_journal_bp
from .routes.reminders import reminders_bp
from .routes.ai import ai_bp
from .routes.admin import admin_bp
from .routes.youtube import youtube_bp

# Create Flask app
app = create_app()

# Initialize database with Flask app
init_db(app)

# Initialize database health monitoring
health_monitor = init_health_monitor(db)

# Perform initial database health check within app context
with app.app_context():
    print("🔍 Performing initial database health check...")
    initial_health = check_database_health()
    if initial_health.get('status') == 'healthy':
        print(f"✅ Database connection healthy - Response time: {initial_health.get('response_time_ms', 'unknown')}ms")
    else:
        print(f"⚠️  Database connection issues detected: {initial_health.get('last_error', 'unknown error')}")

    # Log initial health status
    log_database_health()

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(static_bp)
app.register_blueprint(subscription_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(food_journal_bp)
app.register_blueprint(reminders_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(youtube_bp)

# Initialize Stripe
stripe_initialized = False


# ============================================================================
# HEALTH CHECK AND MONITORING ROUTES
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database health
        db_health = check_database_health()
        
        # Determine overall health
        is_healthy = db_health.get('status') == 'healthy'
        
        response = {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_health,
            'environment': {
                'flask_env': app.config.get('FLASK_ENV', 'unknown'),
                'debug_mode': app.config.get('DEBUG', False)
            }
        }
        
        status_code = 200 if is_healthy else 503
        return jsonify(response), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@app.route('/health/database')
def database_health():
    """Database-specific health check"""
    try:
        health = check_database_health()
        return jsonify(health), 200 if health.get('status') == 'healthy' else 503
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ============================================================================
# REMAINING ROUTES - TO BE MODULARIZED
# ============================================================================

# Profile Routes

@app.context_processor
def inject_functions():
    return {
        'get_current_user': UserService.get_current_user,
        'get_current_user_profile': UserService.get_current_user_profile,
        'is_admin_user': is_admin_user,
        'ADMIN_EMAIL': os.environ.get('ADMIN_EMAIL', 'admin@kiwellness.org'),
        'IS_LOCALHOST': SecurityUtils.is_localhost_environment(),
        'datetime': datetime,
        'utcnow': datetime.utcnow
    }

if __name__ == '__main__':
    # Initialize database and admin account
    with app.app_context():
        ensure_tables_exist()
        create_admin_account()
    
    app.run(debug=True, host='0.0.0.0', port=5001)
