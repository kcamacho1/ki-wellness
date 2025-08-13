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
from .models import db, init_db, User, UserProfile, FoodCache, FoodJournal, MoodEntry, PatternsCache, Review, UserAgreement, Reminder, ReminderLog, Notification, SystemSettings, TokenUsage, APICosts, UserSubscription, SessionCredits, AIUsageSession
from .utils import ValidationUtils, SecurityUtils, TimeUtils, ConversionUtils, NotificationUtils, DataQualityUtils
from .services import SystemService, UserService, NutritionService, AIService
from .config import create_app, limiter, oauth, google_oauth, OAUTH_AVAILABLE, STRIPE_AVAILABLE, get_stripe_config, create_admin_account, ensure_tables_exist
from .decorators import login_required, admin_required, is_admin_user, verify_user_data_access
from .routes.auth import auth_bp
from .routes.static import static_bp
from .routes.subscription import subscription_bp
from .routes.profile import profile_bp
from .routes.food_journal import food_journal_bp
from .routes.dashboard import dashboard_bp
from .routes.reminders import reminders_bp
from .routes.ai import ai_bp
from .routes.admin import admin_bp

# Create Flask app
app = create_app()

# Initialize database with Flask app
init_db(app)

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(static_bp)
app.register_blueprint(subscription_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(food_journal_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(reminders_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(admin_bp)

# Initialize Stripe
stripe_initialized = False


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
