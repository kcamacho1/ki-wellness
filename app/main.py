import os
import json
import requests
import csv
import io
from datetime import datetime, timedelta, time
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect
from config import DevelopmentConfig, ProductionConfig
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# OAuth imports
try:
    from flask_oauthlib.client import OAuth
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    print("⚠️  Flask-OAuthlib not available. OAuth features will be disabled.")
try:
    from flask_limiter import Limiter  # type: ignore
    from flask_limiter.util import get_remote_address  # type: ignore
except ImportError:
    # Fallback for environments where Flask-Limiter is not available
    class Limiter:
        def __init__(self, app=None, key_func=None, default_limits=None, storage_uri=None):
            self.app = app
            self.key_func = key_func
            self.default_limits = default_limits or []
            self.storage_uri = storage_uri
        
        def limit(self, limit_string):
            def decorator(f):
                return f
            return decorator
    
    def get_remote_address():
        return "127.0.0.1"  # Default fallback
import random
import hashlib
import time
import re
import uuid
import base64
import sqlite3

# Stripe integration
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    print("⚠️  Stripe library not available. Payment features will be disabled.")

app = Flask(__name__)

# Determine which configuration to use based on environment
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

# SECURITY: Configure session timeout to 1 hour (3600 seconds)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'



# Ensure database URL is properly set
if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    # Fallback to SQLite if no database URL is set
    # Use absolute path to ensure we're using the correct database file
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, 'ki_wellness.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    print(f"🔧 Fallback database path: {db_path}")

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize OAuth
if OAUTH_AVAILABLE:
    oauth = OAuth(app)
    
    # Google OAuth configuration
    google_oauth = oauth.remote_app(
        'google',
        consumer_key=os.environ.get('GOOGLE_CLIENT_ID'),
        consumer_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        request_token_params={
            'scope': 'email profile'
        },
        base_url='https://www.googleapis.com/oauth2/v1/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth'
    )
else:
    oauth = None
    google_oauth = None

# Initialize Stripe
def get_stripe_config():
    """Get Stripe configuration based on payment testing mode"""
    try:
        # Check if payment testing mode is enabled
        testing_setting = SystemSettings.query.filter_by(key='payment_testing_mode').first()
        is_testing_mode = testing_setting and testing_setting.value == 'true'
        
        if is_testing_mode:
            # Use sandbox keys
            secret_key = app.config.get('STRIPE_SANDBOX_SECRET_KEY')
            publishable_key = app.config.get('STRIPE_SANDBOX_PUBLISHABLE_KEY')
            webhook_secret = app.config.get('STRIPE_SANDBOX_WEBHOOK_SECRET')
            environment = 'sandbox'
        else:
            # Use live keys
            secret_key = app.config.get('STRIPE_SECRET_KEY')
            publishable_key = app.config.get('STRIPE_PUBLISHABLE_KEY')
            webhook_secret = app.config.get('STRIPE_WEBHOOK_SECRET')
            environment = 'live'
        
        return {
            'secret_key': secret_key,
            'publishable_key': publishable_key,
            'webhook_secret': webhook_secret,
            'environment': environment,
            'is_testing_mode': is_testing_mode
        }
    except Exception as e:
        print(f"❌ Error getting Stripe config: {e}")
        return None

def initialize_stripe():
    """Initialize Stripe with appropriate configuration"""
    if not STRIPE_AVAILABLE:
        print("⚠️  Stripe library not available. Payment features will be disabled.")
        return False
    
    config = get_stripe_config()
    if not config or not config['secret_key']:
        print("⚠️  Stripe not configured. Payment features will be disabled.")
        return False
    
    stripe.api_key = config['secret_key']
    print(f"✅ Stripe initialized successfully ({config['environment']} mode)")
    return True

# Initialize Stripe on startup (will be called after models are defined)
stripe_initialized = False

# Database initialization will be handled by the create_admin_account function
# def init_database():
#     """Initialize the database and create tables"""
#     try:
#         print("🔄 Initializing database...")
#         
#         # Create all tables
#         db.create_all()
#         print("✅ Database tables created successfully")
#         
#         # Ensure tables exist
#         ensure_tables_exist()
#         
#         # Create admin account
#         create_admin_account()
#         
#         # Initialize system settings
#         init_system_settings()
#         
#         # Initialize default API costs
#         init_default_api_costs()
#         
#         print("✅ Database initialization completed successfully!")
#         
#     except Exception as e:
#         print(f"❌ Database initialization failed: {str(e)}")
#         raise


# This function is duplicated - using the one below instead
# def init_system_settings():
#     """Initialize default system settings"""
#     try:
#         # Check if settings already exist
#         if SystemSettings.query.count() == 0:
#             print("🔄 Initializing system settings...")
#             
#             default_settings = [
#                 {
#                     'key': 'new_accounts_enabled',
#                     'value': 'true',
#                     'description': 'Allow new user registrations'
#                 },
#                 {
#                     'key': 'openai_api_enabled',
#                     'value': 'true',
#                     'description': 'Enable OpenAI API calls'
#                 },
#                 {
#                     'key': 'emergency_stop_active',
#                     'value': 'false',
#                     'description': 'Emergency stop for OpenAI API'
#                 },
#                 {
#                     'key': 'monthly_token_limit',
#                     'value': '1000000',
#                     'description': 'Monthly token usage limit'
#                 }
#             ]
#             
#             for setting in default_settings:
#                 system_setting = SystemSettings(
#                     key=setting['key'],
#                     value=setting['value'],
#                     description=setting['description'],
#                     updated_by=None
#                 )
#                 db.session.add(system_setting)
#             
#             # Initialize default API costs
#             default_api_costs = [
#                 {
#                     'model_name': 'gpt-4',
#                     'input_cost_per_1k': 0.03,
#                     'output_cost_per_1k': 0.06
#                 },
#                 {
#                     'model_name': 'gpt-4-turbo',
#                     'input_cost_per_1k': 0.01,
#                     'output_cost_per_1k': 0.03
#                 },
#                 {
#                     'model_name': 'gpt-3.5-turbo',
#                     'input_cost_per_1k': 0.0015,
#                     'output_cost_per_1k': 0.002
#                 }
#             ]
#             
#             for cost in default_api_costs:
#                 api_cost = APICosts(
#                     model_name=cost['model_name'],
#                     input_cost_per_1k=cost['input_cost_per_1k'],
#                     output_cost_per_1k=cost['output_cost_per_1k'],
#                     updated_by=None
#                 )
#                 db.session.add(api_cost)
#             
#             db.session.commit()
#             print("✅ System settings initialized successfully!")
#         else:
#             print("ℹ️  System settings already exist")
#             
#     except Exception as e:
#         print(f"❌ Error initializing system settings: {e}")
#         db.session.rollback()


# This function is duplicated - using the one below instead
# def init_default_api_costs():
#     """Initialize default OpenAI API costs (as of 2024)"""
#     try:
#         # Check if API costs already exist
#         if APICosts.query.count() == 0:
#             print("🔄 Initializing default API costs...")
#             
#             default_costs = [
#                 {
#                     'model_name': 'gpt-4',
#                     'input_cost_per_1k': 0.03,
#                     'output_cost_per_1k': 0.06
#                 },
#                 {
#                     'model_name': 'gpt-4-turbo',
#                     'input_cost_per_1k': 0.01,
#                     'output_cost_per_1k': 0.03
#                 },
#                 {
#                     'model_name': 'gpt-3.5-turbo',
#                     'input_cost_per_1k': 0.0015,
#                     'output_cost_per_1k': 0.002
#                 }
#             ]
#             
#             for cost in default_costs:
#                 new_cost = APICosts(**cost)
#                 db.session.add(new_cost)
#             
#             db.session.commit()
#             print("✅ Default API costs initialized successfully!")
#         else:
#             print("ℹ️  API costs already exist")
#             
#     except Exception as e:
#         print(f"⚠️  Warning: Could not initialize API costs: {e}")
#         db.session.rollback()


# These functions are duplicated - using the ones below instead
# def get_system_setting(key, default=None):
#     """Get a system setting value"""
#     try:
#         setting = SystemSettings.query.filter_by(key=key).first()
#         if setting:
#             if setting.value.lower() in ['true', 'false']:
#                 return setting.value.lower() == 'true'
#             return setting.value
#         return default
#     except Exception as e:
#         print(f"Error getting system setting {key}: {e}")
#         return default
# 
# 
# def set_system_setting(key, value, description=None, user_id=None):
#     """Set a system setting value"""
#     try:
#         setting = SystemSettings.query.filter_by(key=key).first()
#         if setting:
#             setting.value = str(value)
#             setting.updated_at = datetime.utcnow()
#             setting.updated_by = user_id
#         else:
#             setting = SystemSettings(
#                 key=key,
#                 value=str(value),
#                 description=description,
#                 updated_by=user_id
#             )
#             db.session.add(setting)
#         
#         db.session.commit()
#         return True
#     except Exception as e:
#         print(f"Error setting system setting {key}: {e}")
#         db.session.rollback()
#         return False
# 
# 
# def is_openai_enabled():
#     """Check if OpenAI API is enabled"""
#     return get_system_setting('openai_api_enabled', True) and not get_system_setting('emergency_stop_active', False)
# 
# 
# def is_emergency_stop_active():
#     """Check if emergency stop is active"""
#     return get_system_setting('emergency_stop_active', 'false').lower() == 'true'
# 
# 
# def are_new_accounts_enabled():
#     """Check if new account creation is enabled"""
#     return get_system_setting('new_accounts_enabled', 'true').lower() == 'true'

# Function to ensure database tables exist (called on first request if needed)
def ensure_tables_exist():
    """Ensure database tables exist, create them if they don't"""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                print("🔄 Creating database tables on first request...")
                db.create_all()
                print("✅ Database tables created successfully!")
                
                # Create admin account after tables are created
                create_admin_account()
                
                return True
            return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

# User Model for Authentication
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True, index=True)  # Phone number field - removed unique constraint for NULL values
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Account status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Verification fields
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    phone_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True, unique=True)
    phone_verification_code = db.Column(db.String(6), nullable=True)  # 6-digit SMS code
    phone_verification_expires = db.Column(db.DateTime, nullable=True)
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    push_notifications = db.Column(db.Boolean, default=True)
    
    # OAuth fields
    oauth_provider = db.Column(db.String(20), nullable=True)  # 'google', 'facebook', etc.
    oauth_id = db.Column(db.String(255), nullable=True, unique=True)  # OAuth provider's user ID
    oauth_email = db.Column(db.String(255), nullable=True)  # Email from OAuth provider
    oauth_name = db.Column(db.String(255), nullable=True)  # Name from OAuth provider
    oauth_picture = db.Column(db.String(500), nullable=True)  # Profile picture URL from OAuth provider
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# User Profile Model
class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(100), nullable=True, default='default-avatar.png')
    weight_unit = db.Column(db.String(10), nullable=True, default='kg')
    
    # Basic profile information
    date_of_birth = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    
    # Wellness goals and preferences
    goal = db.Column(db.String(100), nullable=True)  # Primary wellness goal
    goals = db.Column(db.Text, nullable=True)  # General wellness goals
    custom_goal = db.Column(db.String(200), nullable=True)  # Custom goal description
    ailments = db.Column(db.Text, nullable=True)  # Health conditions
    dietary_preferences = db.Column(db.Text, nullable=True)
    sleep_schedule = db.Column(db.String(100), nullable=True)
    
    # Physical wellness
    daily_activities = db.Column(db.Text, nullable=True)  # Work activities
    exercise_routine = db.Column(db.Text, nullable=True)
    day_notes = db.Column(db.Text, nullable=True)  # Body notes/goals
    night_notes = db.Column(db.Text, nullable=True)  # Recovery notes
    
    # Spiritual and emotional wellness
    spiritual_religion = db.Column(db.Text, nullable=True)
    self_connection = db.Column(db.Text, nullable=True)
    surroundings_connection = db.Column(db.Text, nullable=True)
    providing_others = db.Column(db.Text, nullable=True)
    safe_groups = db.Column(db.Text, nullable=True)
    awe_things = db.Column(db.Text, nullable=True)
    creative_expression = db.Column(db.Text, nullable=True)
    upsetting_situations = db.Column(db.Text, nullable=True)
    spirit_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def create_admin_account():
    """Create the default admin account if it doesn't exist"""
    try:
        # Get admin credentials from environment variables
        admin_username = os.environ.get('ADMIN_USERNAME', 'ki.wellness')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@kiwellness.org')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'InfiniteAbundance$369')
        admin_name = os.environ.get('ADMIN_NAME', 'key')
        
        # Check if admin account already exists
        admin_user = User.query.filter_by(username=admin_username).first()
        
        if not admin_user:
            print("🔄 Creating admin account...")
            
            # Create admin user
            admin_user = User(
                username=admin_username,
                email=admin_email,
                is_admin=True
            )
            admin_user.set_password(admin_password)
            
            # Add to database
            db.session.add(admin_user)
            db.session.commit()
            
            # Try to create admin user profile, but handle gracefully if table doesn't exist
            try:
                admin_profile = UserProfile(
                    user_id=admin_user.id,
                    name=admin_name,
                    avatar='default-avatar.png',
                    weight_unit='kg'
                )
                
                db.session.add(admin_profile)
                db.session.commit()
                print("✅ Admin profile created successfully!")
            except Exception as e:
                print(f"⚠️  Warning: Could not create admin profile: {e}")
                # Continue without profile - not critical for admin functionality
            
            print("✅ Admin account created successfully!")
            print(f"   Username: {admin_username}")
            print(f"   Email: {admin_email}")
            print(f"   Name: {admin_name}")
        else:
            print("ℹ️  Admin account already exists")
            
        # Initialize system settings
        initialize_system_settings(admin_user.id)
        
    except Exception as e:
        print(f"❌ Error creating admin account: {e}")
        db.session.rollback()


def initialize_system_settings(admin_user_id):
    """Initialize default system settings"""
    global stripe_initialized
    try:
        # Check if settings already exist
        if SystemSettings.query.count() == 0:
            print("🔄 Initializing system settings...")
            
            default_settings = [
                {
                    'key': 'new_accounts_enabled',
                    'value': 'true',
                    'description': 'Allow new user registrations'
                },
                {
                    'key': 'openai_api_enabled',
                    'value': 'true',
                    'description': 'Enable OpenAI API calls'
                },
                {
                    'key': 'emergency_stop_active',
                    'value': 'false',
                    'description': 'Emergency stop for OpenAI API'
                },
                {
                    'key': 'monthly_token_limit',
                    'value': '1000000',
                    'description': 'Monthly token usage limit'
                },
                {
                    'key': 'current_gpt_model',
                    'value': 'gpt-3.5-turbo',
                    'description': 'Current GPT model being used for AI analysis'
                },
                {
                    'key': 'max_input_tokens',
                    'value': '2000',
                    'description': 'Maximum input/prompt tokens per request'
                },
                {
                    'key': 'max_output_tokens',
                    'value': '1500',
                    'description': 'Maximum output/completion tokens per request'
                },
                {
                    'key': 'max_total_tokens',
                    'value': '3500',
                    'description': 'Maximum total tokens per request (input + output)'
                },
                {
                    'key': 'flexible_service_tier',
                    'value': 'true',
                    'description': 'Enable flexible service tier for cost optimization'
                },
                {
                    'key': 'presence_penalty',
                    'value': '0.0',
                    'description': 'Presence penalty for OpenAI API (0.0 = disabled)'
                },
                {
                    'key': 'frequency_penalty',
                    'value': '0.0',
                    'description': 'Frequency penalty for OpenAI API (0.0 = disabled)'
                },
                {
                    'key': 'top_p',
                    'value': '0.9',
                    'description': 'Top-p sampling for OpenAI API (0.9 = focused responses)'
                },
                {
                    'key': 'payment_testing_mode',
                    'value': 'false',
                    'description': 'Enable Stripe sandbox mode for payment testing'
                }
            ]
            
            for setting in default_settings:
                system_setting = SystemSettings(
                    key=setting['key'],
                    value=setting['value'],
                    description=setting['description'],
                    updated_by=admin_user_id
                )
                db.session.add(system_setting)
            
            # Initialize default API costs (per 1M tokens)
            default_api_costs = [
                {
                    'model_name': 'gpt-4',
                    'input_cost_per_1m': 30.0,
                    'output_cost_per_1m': 60.0
                },
                {
                    'model_name': 'gpt-4-turbo',
                    'input_cost_per_1m': 10.0,
                    'output_cost_per_1m': 30.0
                },
                {
                    'model_name': 'gpt-3.5-turbo',
                    'input_cost_per_1m': 1.5,
                    'output_cost_per_1m': 2.0
                }
            ]
            
            for cost in default_api_costs:
                api_cost = APICosts(
                    model_name=cost['model_name'],
                    input_cost_per_1m=cost['input_cost_per_1m'],
                    output_cost_per_1m=cost['output_cost_per_1m'],
                    updated_by=admin_user_id
                )
                db.session.add(api_cost)
            
            db.session.commit()
            print("✅ System settings initialized successfully!")
            
            # Initialize Stripe after database models are available
            stripe_initialized = initialize_stripe()
        else:
            print("ℹ️  System settings already exist")
            
            # Initialize Stripe even if settings already exist
            if not stripe_initialized:
                stripe_initialized = initialize_stripe()
            
    except Exception as e:
        print(f"❌ Error initializing system settings: {e}")
        db.session.rollback()


def get_system_setting(key, default=None):
    """Get a system setting value"""
    try:
        setting = SystemSettings.query.filter_by(key=key).first()
        if setting:
            # For boolean settings, convert string 'true'/'false' to boolean
            if key in ['flexible_service_tier', 'openai_api_enabled', 'emergency_stop_active', 'new_accounts_enabled']:
                if isinstance(setting.value, str):
                    return setting.value.lower() == 'true'
                elif isinstance(setting.value, bool):
                    return setting.value
                else:
                    return default
            # For numeric settings, return as string (let caller convert)
            elif key in ['presence_penalty', 'frequency_penalty', 'top_p', 'max_input_tokens', 'max_output_tokens', 'max_total_tokens']:
                return setting.value
            # For other settings, return as is
            else:
                return setting.value
        return default
    except Exception as e:
        print(f"Error getting system setting {key}: {e}")
        return default


def set_system_setting(key, value, description=None, user_id=None):
    """Set a system setting value"""
    try:
        setting = SystemSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            setting.updated_at = datetime.utcnow()
            setting.updated_by = user_id
        else:
            setting = SystemSettings(
                key=key,
                value=str(value),
                description=description,
                updated_by=user_id
            )
            db.session.add(setting)
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error setting system setting {key}: {e}")
        db.session.rollback()
        return False


def is_openai_enabled():
    """Check if OpenAI API is enabled"""
    return get_system_setting('openai_api_enabled', True) and not get_system_setting('emergency_stop_active', False)


def is_emergency_stop_active():
    """Check if emergency stop is active"""
    return get_system_setting('emergency_stop_active', False)


def are_new_accounts_enabled():
    """Check if new account creation is enabled"""
    return get_system_setting('new_accounts_enabled', True)

def get_current_gpt_model():
    """Get the current GPT model being used"""
    return get_system_setting('current_gpt_model', 'gpt-3.5-turbo')

def get_max_input_tokens():
    """Get the maximum input tokens allowed per request"""
    return int(get_system_setting('max_input_tokens', 2000))

def get_max_output_tokens():
    """Get the maximum output tokens allowed per request"""
    return int(get_system_setting('max_output_tokens', 1500))

def get_max_total_tokens():
    """Get the maximum total tokens allowed per request"""
    return int(get_system_setting('max_total_tokens', 3500))


def get_flexible_service_tier():
    """Get whether flexible service tier is enabled"""
    value = get_system_setting('flexible_service_tier', 'true')
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() == 'true'
    else:
        return True  # Default to enabled


def get_presence_penalty():
    """Get the presence penalty value for OpenAI API"""
    value = get_system_setting('presence_penalty', '0.0')
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def get_frequency_penalty():
    """Get the frequency penalty value for OpenAI API"""
    value = get_system_setting('frequency_penalty', '0.0')
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def get_top_p():
    """Get the top-p sampling value for OpenAI API"""
    value = get_system_setting('top_p', '0.9')
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.9

def is_user_verified_for_ai(user):
    """Check if user is verified for AI usage (both email and phone verified)"""
    if not user:
        return False
    return user.email_verified and user.phone_verified

def generate_verification_token():
    """Generate a secure verification token"""
    import secrets
    return secrets.token_urlsafe(32)

def generate_phone_verification_code():
    """Generate a 6-digit verification code"""
    import random
    return str(random.randint(100000, 999999))

def send_verification_email(user_email, token):
    """Send verification email (placeholder for actual email service)"""
    # In production, integrate with SendGrid, Mailgun, or similar
    verification_url = f"{request.host_url}verify-email/{token}"
    subject = "Verify Your Email - KI Wellness"
    message = f"""
    Hello!
    
    Please verify your email address by clicking the link below:
    {verification_url}
    
    If you didn't create this account, please ignore this email.
    
    Best regards,
    KI Wellness Team
    """
    
    try:
        # Placeholder for actual email sending
        print(f"📧 Verification email would be sent to {user_email}")
        print(f"📧 Subject: {subject}")
        print(f"📧 Message: {message}")
        return True
    except Exception as e:
        print(f"❌ Error sending verification email: {e}")
        return False

def send_verification_sms(phone_number, code):
    """Send verification SMS (placeholder for actual SMS service)"""
    # In production, integrate with Twilio, AWS SNS, or similar
    message = f"Your KI Wellness verification code is: {code}. Valid for 10 minutes."
    
    try:
        # Placeholder for actual SMS sending
        print(f"📱 Verification SMS would be sent to {phone_number}")
        print(f"📱 Message: {message}")
        return True
    except Exception as e:
        print(f"❌ Error sending verification SMS: {e}")
        return False


def get_user_subscription_info(user_id):
    """Get user's subscription information and session usage"""
    try:
        # Get or create subscription record
        subscription = UserSubscription.query.filter_by(user_id=user_id).first()
        if not subscription:
            # Create default subscription for new users
            subscription = UserSubscription(
                user_id=user_id,
                subscription_type='subscription',
                billing_cycle_start=datetime.utcnow()
            )
            db.session.add(subscription)
            db.session.commit()
        
        # Check if billing cycle needs to reset
        now = datetime.utcnow()
        if subscription.billing_cycle_start.month != now.month or subscription.billing_cycle_start.year != now.year:
            subscription.sessions_used_this_month = 0
            subscription.billing_cycle_start = now
            db.session.commit()
        
        # Get session credits
        credits = SessionCredits.query.filter_by(user_id=user_id).first()
        if not credits:
            credits = SessionCredits(user_id=user_id)
            db.session.add(credits)
            db.session.commit()
        
        return {
            'subscription_type': subscription.subscription_type,
            'sessions_per_month': subscription.sessions_per_month,
            'sessions_used_this_month': subscription.sessions_used_this_month,
            'sessions_remaining': subscription.sessions_per_month - subscription.sessions_used_this_month,
            'credits_remaining': credits.credits_remaining,
            'billing_cycle_start': subscription.billing_cycle_start,
            'monthly_fee': subscription.monthly_fee_usd
        }
    except Exception as e:
        print(f"❌ Error getting subscription info: {e}")
        return None


def can_user_use_ai(user_id):
    """Check if user can use AI features (has sessions or credits remaining)"""
    try:
        sub_info = get_user_subscription_info(user_id)
        if not sub_info:
            return False
        
        # Check if user has subscription sessions or credits remaining
        return (sub_info['sessions_remaining'] > 0 or sub_info['credits_remaining'] > 0)
    except Exception as e:
        print(f"❌ Error checking AI usage permission: {e}")
        return False


def record_ai_session(user_id, session_type, input_tokens, output_tokens, total_tokens, cost_usd, model_used):
    """Record an AI usage session and deduct from subscription or credits"""
    try:
        sub_info = get_user_subscription_info(user_id)
        if not sub_info:
            return False
        
        # Create usage session record
        usage_session = AIUsageSession(
            user_id=user_id,
            session_type=session_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            model_used=model_used
        )
        
        # Determine if using subscription or credits
        if sub_info['sessions_remaining'] > 0:
            # Use subscription
            usage_session.subscription_used = True
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            subscription.sessions_used_this_month += 1
        else:
            # Use credits
            usage_session.subscription_used = False
            credits = SessionCredits.query.filter_by(user_id=user_id).first()
            if credits.credits_remaining > 0:
                usage_session.credit_id = credits.id
                credits.credits_used += 1
                credits.credits_remaining -= 1
            else:
                # No credits remaining
                return False
        
        db.session.add(usage_session)
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error recording AI session: {e}")
        db.session.rollback()
        return False


def get_user_usage_summary(user_id):
    """Get comprehensive usage summary for user"""
    try:
        sub_info = get_user_subscription_info(user_id)
        if not sub_info:
            return None
        
        # Get recent AI sessions
        recent_sessions = AIUsageSession.query.filter_by(user_id=user_id)\
            .order_by(AIUsageSession.created_at.desc())\
            .limit(10).all()
        
        # Calculate total costs
        total_cost = sum(session.cost_usd for session in recent_sessions)
        
        return {
            'subscription_info': sub_info,
            'recent_sessions': [
                {
                    'type': session.session_type,
                    'tokens': session.total_tokens,
                    'cost': session.cost_usd,
                    'date': session.created_at.strftime('%Y-%m-%d %H:%M'),
                    'used_subscription': session.subscription_used
                } for session in recent_sessions
            ],
            'total_cost': total_cost,
            'can_use_ai': can_user_use_ai(user_id)
        }
    except Exception as e:
        print(f"❌ Error getting usage summary: {e}")
        return None

# Authentication decorator with session timeout
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # SECURITY: Check if user is logged in
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # SECURITY: Check if session has expired (1 hour timeout)
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.utcnow() - last_activity > timedelta(hours=1):
                # Session expired, clear session and redirect to login
                session.clear()
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('login'))
        
        # Update last activity timestamp
        session['last_activity'] = datetime.utcnow().isoformat()
        session.permanent = True  # Enable session timeout
        
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get current user
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# Make functions available to templates
def is_localhost_environment():
    """Check if running on localhost"""
    try:
        if request:
            host = request.host
            is_local = host in ['127.0.0.1:5001', 'localhost:5001', '0.0.0.0:5001']
            print(f"🔧 Host check: {host} -> localhost: {is_local}")
            return is_local
    except RuntimeError as e:
        print(f"🔧 RuntimeError in host check: {e}")
        pass
    print("🔧 No request context, assuming not localhost")
    return False



@app.context_processor
def inject_functions():
    return {
        'get_current_user': get_current_user,
        'is_admin_user': is_admin_user,
        'ADMIN_EMAIL': os.environ.get('ADMIN_EMAIL', 'admin@kiwellness.org'),
        'IS_LOCALHOST': is_localhost_environment(),
        'datetime': datetime,
        'utcnow': datetime.utcnow
    }

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

# Helper function to get current user profile
def get_current_user_profile():
    user = get_current_user()
    if user:
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            # Create a default profile if it doesn't exist
            profile = UserProfile(
                user_id=user.id,
                name=user.username,
                avatar='default-avatar.png',
                weight_unit='kg'
            )
            db.session.add(profile)
            db.session.commit()
        return profile
    return None

# Admin decorator with session timeout
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # SECURITY: Check if user is logged in
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # SECURITY: Check if session has expired (1 hour timeout)
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.utcnow() - last_activity > timedelta(hours=1):
                # Session expired, clear session and redirect to login
                session.clear()
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        
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

# Food Cache Model for storing nutritional information
class FoodCache(db.Model):
    __tablename__ = 'food_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(200), nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=True)
    serving_size = db.Column(db.Float, nullable=False)
    serving_unit = db.Column(db.String(20), nullable=False)
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    fiber = db.Column(db.Float, nullable=True)
    sugar = db.Column(db.Float, nullable=True)
    sodium = db.Column(db.Float, nullable=True)
    source = db.Column(db.String(50), nullable=False)  # 'openfoodfacts', 'usda', 'manual'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Food Journal Model for user entries
class FoodJournal(db.Model):
    __tablename__ = 'food_journal'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    food_name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    serving_size = db.Column(db.Float, nullable=False)
    serving_unit = db.Column(db.String(20), nullable=False)
    
    # Core nutritional values (displayed to user)
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    fiber = db.Column(db.Float, nullable=True)
    sugar = db.Column(db.Float, nullable=True)
    sodium = db.Column(db.Float, nullable=True)
    
    # Extended nutritional values (stored but not displayed)
    saturated_fat = db.Column(db.Float, nullable=True)
    trans_fat = db.Column(db.Float, nullable=True)
    cholesterol = db.Column(db.Float, nullable=True)
    potassium = db.Column(db.Float, nullable=True)
    calcium = db.Column(db.Float, nullable=True)
    iron = db.Column(db.Float, nullable=True)
    vitamin_a = db.Column(db.Float, nullable=True)
    vitamin_c = db.Column(db.Float, nullable=True)
    vitamin_d = db.Column(db.Float, nullable=True)
    vitamin_e = db.Column(db.Float, nullable=True)
    vitamin_k = db.Column(db.Float, nullable=True)
    vitamin_b6 = db.Column(db.Float, nullable=True)
    vitamin_b12 = db.Column(db.Float, nullable=True)
    magnesium = db.Column(db.Float, nullable=True)
    zinc = db.Column(db.Float, nullable=True)
    phosphorus = db.Column(db.Float, nullable=True)
    manganese = db.Column(db.Float, nullable=True)
    selenium = db.Column(db.Float, nullable=True)
    copper = db.Column(db.Float, nullable=True)
    thiamin = db.Column(db.Float, nullable=True)
    riboflavin = db.Column(db.Float, nullable=True)
    niacin = db.Column(db.Float, nullable=True)
    folate = db.Column(db.Float, nullable=True)
    pantothenic_acid = db.Column(db.Float, nullable=True)
    biotin = db.Column(db.Float, nullable=True)
    choline = db.Column(db.Float, nullable=True)
    betaine = db.Column(db.Float, nullable=True)
    taurine = db.Column(db.Float, nullable=True)
    caffeine = db.Column(db.Float, nullable=True)
    alcohol = db.Column(db.Float, nullable=True)
    water_content = db.Column(db.Float, nullable=True)
    ash = db.Column(db.Float, nullable=True)
    
    # Metadata
    data_source = db.Column(db.String(50), nullable=True)  # openfoodfacts, usda, common_foods_db
    barcode = db.Column(db.String(50), nullable=True)
    time_of_day = db.Column(db.String(20), nullable=True)  # breakfast, lunch, dinner, snacks
    water_amount = db.Column(db.Float, nullable=True)
    water_unit = db.Column(db.String(20), nullable=True)  # oz, liters, gallons
    mood = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    consumed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Mood Entry Model for quick mood logging
class MoodEntry(db.Model):
    __tablename__ = 'mood_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    mood = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Patterns Cache Model for storing analysis results
class PatternsCache(db.Model):
    __tablename__ = 'patterns_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    period_type = db.Column(db.String(10), nullable=False)  # '7day' or '30day'
    analysis = db.Column(db.Text, nullable=True)
    suggestions = db.Column(db.Text, nullable=True)
    summary = db.Column(db.JSON, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)  # Admin approval for public display
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4/IPv6 address for rate limiting
    user_agent = db.Column(db.Text, nullable=True)  # User agent string for monitoring
    spam_score = db.Column(db.Integer, default=0)  # Spam detection score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserAgreement(db.Model):
    __tablename__ = 'user_agreements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    privacy_policy_accepted = db.Column(db.Boolean, default=False)
    terms_of_service_accepted = db.Column(db.Boolean, default=False)
    disclaimer_accepted = db.Column(db.Boolean, default=False)
    privacy_policy_version = db.Column(db.String(20), nullable=True)
    terms_version = db.Column(db.String(20), nullable=True)
    disclaimer_version = db.Column(db.String(20), nullable=True)
    accepted_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='agreements')

class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    reminder_type = db.Column(db.String(50), nullable=False)  # water, macronutrients, mood
    frequency = db.Column(db.String(50), nullable=False)  # daily, hourly, custom
    time_of_day = db.Column(db.Time, nullable=False)
    days_of_week = db.Column(db.String(100))  # JSON string for custom days
    is_active = db.Column(db.Boolean, default=True)
    last_triggered = db.Column(db.DateTime)
    next_trigger = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='reminders')

class ReminderLog(db.Model):
    __tablename__ = 'reminder_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    action_taken = db.Column(db.String(50))  # completed, snoozed, dismissed
    response_time = db.Column(db.Integer)  # seconds from trigger to response
    
    reminder = db.relationship('Reminder', backref='logs')
    user = db.relationship('User', backref='reminder_logs')

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=True)
    notification_type = db.Column(db.String(50), nullable=False)  # email, sms, push
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, sent, failed
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')
    reminder = db.relationship('Reminder', backref='notifications')

# Timezone helper function
def get_browser_timezone_datetime(browser_timezone=None):
    """Get current datetime in browser timezone"""
    try:
        if browser_timezone:
            # Get current time in the browser's timezone
            now = datetime.utcnow()
            # Convert to the browser's timezone
            browser_tz = pytz.timezone(browser_timezone)
            utc_tz = pytz.UTC
            utc_now = utc_tz.localize(now)
            browser_now = utc_now.astimezone(browser_tz)
            # Return as naive datetime in browser timezone
            return browser_now.replace(tzinfo=None)
        else:
            # Fallback to UTC if no timezone provided
            return datetime.utcnow()
    except Exception as e:
        print(f"Error parsing browser timezone: {e}")
        return datetime.utcnow()

# API Integration Functions
def search_openfoodfacts_by_barcode(barcode):
    """Search Open Food Facts API v2 by barcode for specific product"""
    try:
        # Use the official API v2 product endpoint
        # Rate limit: 100 req/min for product queries
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}"
        
        # Set up headers with proper User-Agent as required by the API
        headers = {
            'User-Agent': 'KiWellness/1.0 (nutrition@kiwellness.org)',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # Handle rate limiting (429 status)
        if response.status_code == 429:
            print("Open Food Facts API: Rate limit reached (100 req/min for product queries)")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 1 and data.get('product'):
            product = data['product']
            return extract_nutritional_data(product, product.get('product_name', ''))
        
        return None
    except requests.exceptions.Timeout:
        print("Open Food Facts API v2 barcode search: Request timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Open Food Facts API v2 barcode search request error: {e}")
        return None
    except Exception as e:
        print(f"Open Food Facts API v2 barcode search error: {e}")
        return None

def search_openfoodfacts_api(food_name):
    """Search Open Food Facts API v2 for nutritional information with improved accuracy"""
    try:
        # Clean and improve search terms
        search_terms = clean_search_terms(food_name)
        
        # Use the official API v2 search endpoint
        # According to docs: https://openfoodfacts.github.io/openfoodfacts-server/api/
        # Rate limit: 10 req/min for search queries
        # The v2 search endpoint might be different, let's try the legacy endpoint with v2 headers
        url = f"https://world.openfoodfacts.org/cgi/search.pl"
        
        # Set up headers with proper User-Agent as required by the API
        headers = {
            'User-Agent': 'KiWellness/1.0 (nutrition@kiwellness.org)',
            'Content-Type': 'application/json'
        }
        
        # Search parameters for the legacy endpoint
        params = {
            'search_terms': search_terms,
            'search_simple': 1,
            'action': 'process',
            'json': 1,
            'page_size': 10  # Get more results to find better matches
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        # Handle rate limiting (429 status)
        if response.status_code == 429:
            print("Open Food Facts API: Rate limit reached (10 req/min for search)")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        if data.get('products') and len(data['products']) > 0:
            # Find the best match
            best_product = find_best_match(data['products'], food_name)
            if best_product:
                return extract_nutritional_data(best_product, food_name)
        
        return None
    except requests.exceptions.Timeout:
        print("Open Food Facts API v2: Request timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Open Food Facts API v2 request error: {e}")
        return None
    except Exception as e:
        print(f"Open Food Facts API v2 error: {e}")
        return None

def clean_search_terms(food_name):
    """Clean and improve search terms for better API results"""
    # Remove common words that might interfere with search
    remove_words = ['fresh', 'organic', 'raw', 'whole', 'natural']
    cleaned = food_name.lower()
    
    for word in remove_words:
        cleaned = cleaned.replace(word, '').strip()
    
    # Add common variations
    variations = {
        'apple': 'apple fruit',
        'banana': 'banana fruit', 
        'chicken': 'chicken meat',
        'rice': 'rice grain',
        'almond': 'almond nut',
        'yogurt': 'yogurt dairy',
        'spinach': 'spinach vegetable',
        'salmon': 'salmon fish',
        'quinoa': 'quinoa grain',
        'avocado': 'avocado fruit'
    }
    
    for key, value in variations.items():
        if key in cleaned:
            cleaned = value
            break
    
    return cleaned

def find_best_match(products, original_food_name):
    """Find the best matching product from search results"""
    original_lower = original_food_name.lower()
    
    # Score each product based on relevance
    scored_products = []
    
    for product in products:
        score = 0
        product_name = product.get('product_name', '').lower()
        brands = product.get('brands', '').lower()
        categories = product.get('categories_tags', [])
        
        # Exact name match gets highest score
        if original_lower in product_name:
            score += 100
        
        # Partial name match
        if any(word in product_name for word in original_lower.split()):
            score += 50
        
        # Prefer raw/unprocessed foods
        if any(tag in categories for tag in ['en:raw-foods', 'en:unprocessed-foods']):
            score += 30
        
        # Penalize heavily processed foods
        if any(tag in categories for tag in ['en:processed-foods', 'en:snacks', 'en:candies']):
            score -= 50
        
        # Penalize if it's clearly a different food (e.g., "oat bars" when searching for "apple")
        if 'bar' in product_name or 'candy' in product_name or 'snack' in product_name:
            if not any(word in original_lower for word in ['bar', 'candy', 'snack']):
                score -= 100
        
        scored_products.append((score, product))
    
    # Sort by score and return the best match
    scored_products.sort(key=lambda x: x[0], reverse=True)
    
    # Only return if the best match has a reasonable score
    if scored_products and scored_products[0][0] > 0:
        return scored_products[0][1]
    
    return None

def extract_nutritional_data(product, original_food_name):
    """Extract and validate nutritional data from product with comprehensive fields"""
    nutriments = product.get('nutriments', {})
    
    # Core nutritional values (displayed to user)
    calories = nutriments.get('energy-kcal_100g') or nutriments.get('energy_100g')
    protein = nutriments.get('proteins_100g')
    carbs = nutriments.get('carbohydrates_100g')
    fat = nutriments.get('fat_100g')
    fiber = nutriments.get('fiber_100g')
    sugar = nutriments.get('sugars_100g')
    sodium = nutriments.get('salt_100g')
    
    # Extended nutritional values (stored but not displayed)
    saturated_fat = nutriments.get('saturated-fat_100g')
    trans_fat = nutriments.get('trans-fat_100g')
    cholesterol = nutriments.get('cholesterol_100g')
    potassium = nutriments.get('potassium_100g')
    calcium = nutriments.get('calcium_100g')
    iron = nutriments.get('iron_100g')
    vitamin_a = nutriments.get('vitamin-a_100g')
    vitamin_c = nutriments.get('vitamin-c_100g')
    vitamin_d = nutriments.get('vitamin-d_100g')
    vitamin_e = nutriments.get('vitamin-e_100g')
    vitamin_k = nutriments.get('vitamin-k_100g')
    vitamin_b6 = nutriments.get('vitamin-b6_100g')
    vitamin_b12 = nutriments.get('vitamin-b12_100g')
    magnesium = nutriments.get('magnesium_100g')
    zinc = nutriments.get('zinc_100g')
    phosphorus = nutriments.get('phosphorus_100g')
    manganese = nutriments.get('manganese_100g')
    selenium = nutriments.get('selenium_100g')
    copper = nutriments.get('copper_100g')
    thiamin = nutriments.get('thiamin_100g')
    riboflavin = nutriments.get('riboflavin_100g')
    niacin = nutriments.get('niacin_100g')
    folate = nutriments.get('folate_100g')
    pantothenic_acid = nutriments.get('pantothenic-acid_100g')
    biotin = nutriments.get('biotin_100g')
    choline = nutriments.get('choline_100g')
    betaine = nutriments.get('betaine_100g')
    taurine = nutriments.get('taurine_100g')
    caffeine = nutriments.get('caffeine_100g')
    alcohol = nutriments.get('alcohol_100g')
    water_content = nutriments.get('water_100g')
    ash = nutriments.get('ash_100g')
    
    # Validate data quality
    if not calories or calories <= 0:
        return None
    
    # Check for reasonable ranges
    if calories > 900:  # Most foods don't exceed 900 cal/100g
        return None
    
    return {
        'food_name': product.get('product_name', original_food_name),
        'brand': product.get('brands', ''),
        'serving_size': 100,
        'serving_unit': 'g',
        
        # Core nutritional values (displayed to user)
        'calories': calories,
        'protein': protein,
        'carbs': carbs,
        'fat': fat,
        'fiber': fiber,
        'sugar': sugar,
        'sodium': sodium,
        
        # Extended nutritional values (stored but not displayed)
        'saturated_fat': saturated_fat,
        'trans_fat': trans_fat,
        'cholesterol': cholesterol,
        'potassium': potassium,
        'calcium': calcium,
        'iron': iron,
        'vitamin_a': vitamin_a,
        'vitamin_c': vitamin_c,
        'vitamin_d': vitamin_d,
        'vitamin_e': vitamin_e,
        'vitamin_k': vitamin_k,
        'vitamin_b6': vitamin_b6,
        'vitamin_b12': vitamin_b12,
        'magnesium': magnesium,
        'zinc': zinc,
        'phosphorus': phosphorus,
        'manganese': manganese,
        'selenium': selenium,
        'copper': copper,
        'thiamin': thiamin,
        'riboflavin': riboflavin,
        'niacin': niacin,
        'folate': folate,
        'pantothenic_acid': pantothenic_acid,
        'biotin': biotin,
        'choline': choline,
        'betaine': betaine,
        'taurine': taurine,
        'caffeine': caffeine,
        'alcohol': alcohol,
        'water_content': water_content,
        'ash': ash,
        
        'source': 'openfoodfacts'
    }

def search_usda_api(food_name):
    """Search USDA API for nutritional information"""
    try:
        # Using USDA FoodData Central API
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={os.environ.get('USDA_API_KEY')}&query={food_name}&pageSize=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('foods') and len(data['foods']) > 0:
            food = data['foods'][0]
            nutrients = {item['nutrientName']: item['value'] for item in food.get('foodNutrients', [])}
            
            return {
                'food_name': food.get('description', food_name),
                'brand': food.get('brandOwner', ''),
                'serving_size': 100,  # Default to 100g
                'serving_unit': 'g',
                'calories': nutrients.get('Energy'),
                'protein': nutrients.get('Protein'),
                'carbs': nutrients.get('Carbohydrate, by difference'),
                'fat': nutrients.get('Total lipid (fat)'),
                'fiber': nutrients.get('Fiber, total dietary'),
                'sugar': nutrients.get('Sugars, total including NLEA'),
                'sodium': nutrients.get('Sodium, Na'),
                'source': 'usda'
            }
    except Exception as e:
        print(f"USDA API error: {e}")
        return None

def convert_nutritional_data(nutrition_data, user_serving_size, user_serving_unit):
    """Convert nutritional data based on user's serving size and unit"""
    if not nutrition_data:
        return None
    
    # Convert to grams for calculation
    base_serving_size = nutrition_data['serving_size']
    base_serving_unit = nutrition_data['serving_unit']
    
    # Convert user serving to grams
    user_serving_in_grams = convert_to_grams(user_serving_size, user_serving_unit)
    base_serving_in_grams = convert_to_grams(base_serving_size, base_serving_unit)
    
    if base_serving_in_grams == 0:
        return None
    
    # Calculate conversion factor
    conversion_factor = user_serving_in_grams / base_serving_in_grams
    
    # Convert all nutritional values
    converted_data = nutrition_data.copy()
    converted_data['serving_size'] = user_serving_size
    converted_data['serving_unit'] = user_serving_unit
    
    # Core nutritional fields (displayed to user)
    core_nutritional_fields = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
    
    # Extended nutritional fields (stored but not displayed)
    extended_nutritional_fields = [
        'saturated_fat', 'trans_fat', 'cholesterol', 'potassium', 'calcium', 'iron',
        'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 'vitamin_b6', 'vitamin_b12',
        'magnesium', 'zinc', 'phosphorus', 'manganese', 'selenium', 'copper', 'thiamin',
        'riboflavin', 'niacin', 'folate', 'pantothenic_acid', 'biotin', 'choline', 'betaine',
        'taurine', 'caffeine', 'alcohol', 'water_content', 'ash'
    ]
    
    # Convert all nutritional fields
    all_nutritional_fields = core_nutritional_fields + extended_nutritional_fields
    for field in all_nutritional_fields:
        if converted_data.get(field) is not None:
            converted_data[field] = converted_data[field] * conversion_factor
    
    return converted_data

def convert_to_grams(amount, unit):
    """Convert various units to grams"""
    unit = unit.lower()
    if unit in ['g', 'gram', 'grams']:
        return amount
    elif unit in ['kg', 'kilogram', 'kilograms']:
        return amount * 1000
    elif unit in ['oz', 'ounce', 'ounces']:
        return amount * 28.35
    elif unit in ['lb', 'pound', 'pounds']:
        return amount * 453.59
    elif unit in ['ml', 'milliliter', 'milliliters']:
        return amount  # Approximate for water-based foods
    elif unit in ['l', 'liter', 'liters']:
        return amount * 1000
    elif unit in ['cup', 'cups']:
        return amount * 236.59
    elif unit in ['tbsp', 'tablespoon', 'tablespoons']:
        return amount * 14.79
    elif unit in ['tsp', 'teaspoon', 'teaspoons']:
        return amount * 4.93
    else:
        return amount  # Default to grams

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/coaching')
def coaching():
    return render_template('coaching_selection.html')


@app.route('/human-coaching')
def human_coaching():
    return render_template('coaching.html')


@app.route('/ai-coaching')
def ai_coaching():
    return render_template('ai_coaching.html')


@app.route('/coaching-selection')
def coaching_selection():
    return render_template('coaching_selection.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')


@app.route('/ai-self-health')
def ai_self_health():
    """AI Self Health informational page that leads to login"""
    return render_template('ai_self_health.html')


@app.route('/reviews')
def reviews():
    """Display all approved reviews and allow users to submit new ones"""
    # Get all approved reviews, ordered by most recent first
    approved_reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).all()
    return render_template('reviews.html', reviews=approved_reviews)


@app.route('/reviews/submit', methods=['POST'])
@limiter.limit("5 per hour")
def submit_review():
    """Submit a new review with comprehensive abuse protection"""
    try:
        data = request.get_json()
        
        # 1. HONEYPOT VALIDATION (catch automated bots)
        if not check_honeypot(data):
            return jsonify({'success': False, 'error': 'Invalid submission'})
        
        # 2. BASIC VALIDATION
        if not data.get('name') or not data.get('rating') or not data.get('content'):
            return jsonify({'success': False, 'error': 'Name, rating, and content are required'})
        
        # 3. INPUT SANITIZATION
        name = str(data['name']).strip()
        title = str(data.get('title', '')).strip()
        content = str(data['content']).strip()
        rating = int(data['rating'])
        
        # 4. LENGTH VALIDATION
        if len(name) < 2 or len(name) > 100:
            return jsonify({'success': False, 'error': 'Name must be between 2 and 100 characters'})
        
        if title and (len(title) < 3 or len(title) > 200):
            return jsonify({'success': False, 'error': 'Title must be between 3 and 200 characters'})
        
        if len(content) < 10 or len(content) > 2000:
            return jsonify({'success': False, 'error': 'Review content must be between 10 and 2000 characters'})
        
        # 5. RATING VALIDATION
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'})
        
        # 6. CONTENT FILTERING (Basic spam detection)
        spam_indicators = [
            'buy now', 'click here', 'visit website', 'http://', 'https://', 'www.',
            'free money', 'make money fast', 'earn cash', 'work from home',
            'weight loss', 'diet pills', 'viagra', 'cialis', 'casino', 'poker',
            'loan', 'credit card', 'debt relief', 'insurance quote'
        ]
        
        content_lower = content.lower()
        name_lower = name.lower()
        title_lower = title.lower()
        
        # Check for spam indicators in content
        spam_score = 0
        for indicator in spam_indicators:
            if indicator in content_lower:
                spam_score += 1
            if indicator in name_lower:
                spam_score += 2  # Higher penalty for spam in name
            if indicator in title_lower:
                spam_score += 1
        
        # Reject if too many spam indicators
        if spam_score >= 3:
            return jsonify({'success': False, 'error': 'Review content appears to be spam and cannot be submitted'})
        
        # 7. RATE LIMITING (Basic IP-based rate limiting)
        client_ip = request.remote_addr
        recent_reviews = Review.query.filter(
            Review.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        # Count reviews from this IP in the last 24 hours
        ip_review_count = 0
        for review in recent_reviews:
            # Simple IP tracking (in production, you'd want a more sophisticated approach)
            if hasattr(review, 'ip_address') and review.ip_address == client_ip:
                ip_review_count += 1
        
        if ip_review_count >= 5:  # Max 5 reviews per IP per day
            return jsonify({'success': False, 'error': 'Too many reviews submitted. Please try again tomorrow.'})
        
        # 8. reCAPTCHA VERIFICATION (if enabled)
        recaptcha_response = data.get('g-recaptcha-response')
        print(f"🔍 Reviews: reCAPTCHA response present: {bool(recaptcha_response)}")
        print(f"🔍 Reviews: Is localhost environment: {is_localhost_environment()}")
        
        if not is_localhost_environment():
            if not recaptcha_response:
                print("❌ Reviews: reCAPTCHA response missing")
                return jsonify({'success': False, 'error': 'Please complete the security verification'})
            
            # Verify reCAPTCHA token
            print(f"🔍 Reviews: Verifying reCAPTCHA response...")
            verification_result = verify_recaptcha(recaptcha_response, action='review')
            print(f"🔍 Reviews: reCAPTCHA verification result: {verification_result}")
            
            if not verification_result:
                print("❌ Reviews: reCAPTCHA verification failed")
                return jsonify({'success': False, 'error': 'Security verification failed. Please try again.'})
            
            print("✅ Reviews: reCAPTCHA verification successful")
        
        # 9. CREATE REVIEW
        new_review = Review(
            name=name,
            rating=rating,
            title=title,
            content=content,
            ip_address=client_ip,  # Store IP for rate limiting
            user_agent=request.headers.get('User-Agent', '')  # Store user agent for monitoring
        )
        
        db.session.add(new_review)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Review submitted successfully! It will be visible after approval.'
        })
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid data format provided'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Error submitting review. Please try again.'})

@app.route('/api/recaptcha-status')
def recaptcha_status():
    """API endpoint to check reCAPTCHA status"""
    # Check if running on localhost
    is_localhost = request.host in ['127.0.0.1:5001', 'localhost:5001', '0.0.0.0:5001']
    
    # Check if reCAPTCHA keys are configured
    site_key = app.config.get('RECAPTCHA_SITE_KEY')
    secret_key = app.config.get('RECAPTCHA_SECRET_KEY')
    keys_configured = bool(site_key and secret_key and site_key != 'None' and secret_key != 'None')
    
    # Determine if reCAPTCHA should be enabled
    # Only enable if not localhost AND keys are configured
    recaptcha_enabled = not is_localhost and keys_configured
    
    print(f"🔍 reCAPTCHA Status Check:")
    print(f"  - Is localhost: {is_localhost}")
    print(f"  - Keys configured: {keys_configured}")
    print(f"  - Site key present: {bool(site_key)}")
    print(f"  - Secret key present: {bool(secret_key)}")
    print(f"  - Final enabled status: {recaptcha_enabled}")
    print(f"  - Request host: {request.host}")
    print(f"  - Request URL: {request.url}")
    print(f"  - Site key value: {site_key[:10] + '...' if site_key and len(site_key) > 10 else site_key}")
    print(f"  - Secret key value: {secret_key[:10] + '...' if secret_key and len(secret_key) > 10 else secret_key}")
    
    return jsonify({
        'enabled': recaptcha_enabled,
        'is_localhost': is_localhost,
        'host': request.host,
        'keys_configured': keys_configured,
        'site_key_present': bool(site_key),
        'secret_key_present': bool(secret_key),
        'request_url': request.url
    })

@app.route('/contact', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Honeypot validation
        if not check_honeypot(request.form):
            flash('Invalid submission detected.', 'error')
            return render_template('contact.html', form_data=request.form)
        
        # Basic validation
        if not all([name, email, subject, message]):
            flash('Please fill in all required fields.', 'error')
            return render_template('contact.html', form_data=request.form)
        
        if len(name) < 2:
            flash('Name must be at least 2 characters long.', 'error')
            return render_template('contact.html', form_data=request.form)
        
        if len(message) < 10:
            flash('Message must be at least 10 characters long.', 'error')
            return render_template('contact.html', form_data=request.form)
        
        try:
            # For now, we'll just show a success message
            # In production, you would send an actual email here
            flash('Thank you for your message! We will get back to you within 24-48 hours.', 'success')
            return render_template('contact.html')
        except Exception as e:
            flash('Sorry, there was an error sending your message. Please try again or email us directly at hello@kiwellness.org', 'error')
            return render_template('contact.html', form_data=request.form)
    
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        print(f"🔍 Login attempt for username: {username}")
        print(f"🔍 Login: Request host: {request.host}")
        print(f"🔍 Login: Request URL: {request.url}")
        print(f"🔍 Login: Request method: {request.method}")
        
        if not username or not password:
            print("❌ Login: Missing username or password")
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        # reCAPTCHA validation (only if enabled)
        # Check if running on localhost
        is_localhost = request.host in ['127.0.0.1:5001', 'localhost:5001', '0.0.0.0:5001']
        
        # Check reCAPTCHA configuration
        recaptcha_site_key = app.config.get('RECAPTCHA_SITE_KEY')
        recaptcha_secret_key = app.config.get('RECAPTCHA_SECRET_KEY')
        keys_configured = bool(recaptcha_site_key and recaptcha_secret_key)
        
        recaptcha_enabled = not is_localhost and keys_configured
        
        print(f"🔍 Login: reCAPTCHA enabled: {recaptcha_enabled}")
        print(f"🔍 Login: Is localhost: {is_localhost}")
        print(f"🔍 Login: Keys configured: {keys_configured}")
        print(f"🔍 Login: reCAPTCHA response present: {bool(recaptcha_response)}")
        print(f"🔍 Login: Site key present: {bool(recaptcha_site_key)}")
        print(f"🔍 Login: Secret key present: {bool(recaptcha_secret_key)}")
        
        if recaptcha_enabled:
            if not recaptcha_response:
                print("❌ Login: reCAPTCHA response missing")
                flash('Please complete the security verification', 'error')
                return render_template('login.html')
            
            # Verify reCAPTCHA
            print(f"🔍 Login: Verifying reCAPTCHA response...")
            verification_result = verify_recaptcha(recaptcha_response, action='login')
            print(f"🔍 Login: reCAPTCHA verification result: {verification_result}")
            
            if not verification_result:
                print("❌ Login: reCAPTCHA verification failed")
                flash('Security verification failed. Please try again.', 'error')
                return render_template('login.html')
            
            print("✅ Login: reCAPTCHA verification successful")
        else:
            print("🔧 Login: reCAPTCHA disabled or not configured")
        
        # Ensure database tables exist before querying
        ensure_tables_exist()
        
        try:
            user = User.query.filter(User.username.ilike(username)).first()
            
            if user:
                print(f"🔍 Login: User found - ID: {user.id}, Admin: {user.is_admin}, Active: {user.is_active}")
                
                if user.check_password(password):
                    print(f"✅ Login: Password verification successful for user {user.id}")
                    
                    # SECURITY: Set up session with timeout
                    session['user_id'] = user.id
                    session['last_activity'] = datetime.utcnow().isoformat()
                    session.permanent = True  # Enable session timeout
                    
                    # Verify session was set
                    session_user_id = session.get('user_id')
                    print(f"🔍 Login: Session user_id set: {session_user_id}")
                    
                    flash('Login successful!', 'success')
                    
                    # Redirect based on user type
                    if user.is_admin:
                        print(f"🔍 Login: Admin user, redirecting to admin dashboard")
                        return redirect(url_for('admin_dashboard'))
                    else:
                        print(f"🔍 Login: Regular user, redirecting to dashboard")
                        return redirect(url_for('dashboard'))
                else:
                    print(f"❌ Login: Password verification failed for user {user.id}")
                    flash('Invalid username or password', 'error')
                    return render_template('login.html')
            else:
                print(f"❌ Login: User not found for username: {username}")
                flash('Invalid username or password', 'error')
                return render_template('login.html')
                
        except Exception as e:
            print(f"❌ Login database error: {e}")
            import traceback
            traceback.print_exc()
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

# Google OAuth routes
@app.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    if not OAUTH_AVAILABLE or not google_oauth:
        flash('OAuth is not available', 'error')
        return redirect(url_for('login'))
    
    # Check if new account creation is enabled
    if not are_new_accounts_enabled():
        flash('New account creation is currently disabled by administrator', 'error')
        return redirect(url_for('login'))
    
    return google_oauth.authorize(callback=url_for('google_authorized', _external=True))

@app.route('/login/google/authorized')
def google_authorized():
    """Handle Google OAuth callback"""
    if not OAUTH_AVAILABLE or not google_oauth:
        flash('OAuth is not available', 'error')
        return redirect(url_for('login'))
    
    try:
        resp = google_oauth.authorized_response()
        if resp is None or resp.get('access_token') is None:
            flash('Access denied: reason={} error={}'.format(
                request.args['error_reason'],
                request.args['error_description']
            ), 'error')
            return redirect(url_for('login'))
        
        # Get user info from Google
        access_token = resp['access_token']
        user_info = google_oauth.get('userinfo', token=(access_token, ''))
        
        if user_info.status != 200:
            flash('Failed to get user info from Google', 'error')
            return redirect(url_for('login'))
        
        google_user = user_info.data
        
        # Check if user already exists
        existing_user = User.query.filter_by(oauth_id=google_user['id']).first()
        
        if existing_user:
            # User exists, log them in
            session['user_id'] = existing_user.id
            session['last_activity'] = datetime.utcnow().isoformat()
            session.permanent = True
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # New user, create account
            # Check if new account creation is enabled
            if not are_new_accounts_enabled():
                flash('New account creation is currently disabled by administrator', 'error')
                return redirect(url_for('login'))
            
            # Create new user
            new_user = User(
                username=google_user['email'].split('@')[0],  # Use email prefix as username
                email=google_user['email'],
                oauth_provider='google',
                oauth_id=google_user['id'],
                oauth_email=google_user['email'],
                oauth_name=google_user.get('name', ''),
                oauth_picture=google_user.get('picture', ''),
                email_verified=True,  # Google emails are verified
                is_active=True
            )
            
            # Set a random password for OAuth users (they won't use it)
            import secrets
            random_password = secrets.token_urlsafe(32)
            new_user.set_password(random_password)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Create user profile
            profile = UserProfile(
                user_id=new_user.id,
                name=google_user.get('name', ''),
                avatar='default-avatar.png'
            )
            db.session.add(profile)
            db.session.commit()
            
            # Log the user in
            session['user_id'] = new_user.id
            session['last_activity'] = datetime.utcnow().isoformat()
            session.permanent = True
            
            flash('Account created and login successful!', 'success')
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        print(f"❌ Google OAuth error: {e}")
        flash('An error occurred during Google login. Please try again.', 'error')
        return redirect(url_for('login'))

def is_kiwellness_username(username):
    """
    Check if username contains 'kiwellness' in any form including special characters, numbers, and variations
    Returns True if the username contains 'kiwellness' in any form, False otherwise
    """
    import re
    
    # Convert to lowercase for case-insensitive comparison
    username_lower = username.lower()
    
    # Remove ALL special characters, spaces, and numbers for comparison
    # This catches variations like: k!wellness, k1wellness, k@wellness, etc.
    cleaned_username = re.sub(r'[^a-zA-Z]', '', username_lower)
    
    # Check if 'kiwellness' is contained in the cleaned username
    if 'kiwellness' in cleaned_username:
        return True
    
    # Check for common variations with special characters and numbers
    variations = [
        'kiwellness',
        'ki_wellness', 
        'ki-wellness',
        'ki wellness',
        'kiwellness123',
        'ki_wellness_123',
        'ki-wellness-123',
        'ki wellness 123',
        'kiwellness2024',
        'ki_wellness_2024',
        'ki-wellness-2024',
        'ki wellness 2024',
        'kiwellness2023',
        'ki_wellness_2023',
        'ki-wellness-2023',
        'ki wellness 2023',
        'kiwellness2025',
        'ki_wellness_2025',
        'ki-wellness-2025',
        'ki wellness 2025',
        # Special character variations
        'k!wellness',
        'k1wellness',
        'k@wellness',
        'k#wellness',
        'k$wellness',
        'k%wellness',
        'k^wellness',
        'k&wellness',
        'k*wellness',
        'k(wellness',
        'k)wellness',
        'k-wellness',
        'k+wellness',
        'k=wellness',
        'k[wellness',
        'k]wellness',
        'k{wellness',
        'k}wellness',
        'k|wellness',
        'k\\wellness',
        'k:wellness',
        'k;wellness',
        'k"wellness',
        'k\'wellness',
        'k<wellness',
        'k>wellness',
        'k,wellness',
        'k.wellness',
        'k?wellness',
        'k/wellness'
    ]
    
    for variation in variations:
        if variation in username_lower:
            return True
    
    # Check for patterns with special characters and numbers
    patterns = [
        r'ki\s*wellness',           # ki wellness, ki  wellness
        r'ki_wellness',             # ki_wellness
        r'ki-wellness',             # ki-wellness
        r'kiwellness',              # kiwellness
        r'k[!@#$%^&*()_+\-=\[\]{}|\\:;"\'<>,.?/0-9]*wellness',  # k followed by any special chars/numbers + wellness
        r'ki[!@#$%^&*()_+\-=\[\]{}|\\:;"\'<>,.?/0-9]*wellness', # ki followed by any special chars/numbers + wellness
        r'k[!@#$%^&*()_+\-=\[\]{}|\\:;"\'<>,.?/0-9]*i[!@#$%^&*()_+\-=\[\]{}|\\:;"\'<>,.?/0-9]*wellness'  # k + special chars + i + special chars + wellness
    ]
    
    for pattern in patterns:
        if re.search(pattern, username_lower):
            return True
    
    # Additional check: look for 'ki' followed by any characters, then 'wellness'
    # This catches cases like: k1wellness, k!wellness, k@wellness, etc.
    ki_pattern = re.search(r'k[^a-zA-Z]*i[^a-zA-Z]*wellness', username_lower)
    if ki_pattern:
        return True
    
    return False

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    if request.method == 'POST':
        # Check if new account creation is disabled
        if not are_new_accounts_enabled():
            flash('🚫 Account Creation Disabled: New account creation is currently disabled by the administrator. Please contact support for assistance.', 'error')
            return render_template('register.html')
        
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')  # Add phone number field
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        # Enhanced validation with detailed error messages
        if not username or not email or not password:
            flash('❌ Missing Information: All fields are required. Please fill in username, email, and password.', 'error')
            return render_template('register.html')
        
        # reCAPTCHA validation (only if enabled)
        is_localhost = request.host in ['127.0.0.1:5001', 'localhost:5001', '0.0.0.0:5001']
        recaptcha_enabled = not is_localhost
        
        print(f"🔍 Register: reCAPTCHA enabled: {recaptcha_enabled}")
        print(f"🔍 Register: Is localhost: {is_localhost}")
        print(f"🔍 Register: reCAPTCHA response present: {bool(recaptcha_response)}")
        
        if recaptcha_enabled:
            if not recaptcha_response:
                print("❌ Register: reCAPTCHA response missing")
                flash('🔒 Security Required: Please complete the security verification to proceed.', 'error')
                return render_template('register.html')
            
            # Verify reCAPTCHA
            print(f"🔍 Register: Verifying reCAPTCHA response...")
            verification_result = verify_recaptcha(recaptcha_response, action='register')
            print(f"🔍 Register: reCAPTCHA verification result: {verification_result}")
            
            if not verification_result:
                print("❌ Register: reCAPTCHA verification failed")
                flash('⚠️ Security Failed: Security verification failed. Please try again.', 'error')
                return render_template('register.html')
            
            print("✅ Register: reCAPTCHA verification successful")
        
        # Enhanced username validation with detailed feedback
        username_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$')
        if not username_pattern.match(username):
            flash('❌ Invalid Username Format: Username must start and end with a letter or number. Can contain letters, numbers, periods, underscores, and dashes in the middle.', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('❌ Username Too Short: Username must be at least 3 characters long.', 'error')
            return render_template('register.html')
        
        if len(username) > 30:
            flash('❌ Username Too Long: Username must be 30 characters or less.', 'error')
            return render_template('register.html')
        
        # Enhanced check for 'kiwellness' in username with detailed explanation
        if is_kiwellness_username(username):
            flash('🚫 Restricted Username: Username cannot contain "kiwellness" or similar variations (including special characters, numbers, or spacing). This is a protected brand name.', 'error')
            return render_template('register.html')
        
        # Password validation
        if len(password) < 8:
            flash('❌ Password Too Weak: Password must be at least 8 characters long for security.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('❌ Password Mismatch: Passwords do not match. Please ensure both password fields are identical.', 'error')
            return render_template('register.html')
        
        # Email format validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            flash('❌ Invalid Email Format: Please enter a valid email address.', 'error')
            return render_template('register.html')
        
        # Ensure database tables exist before querying
        ensure_tables_exist()
        
        # Check for existing username
        if User.query.filter(User.username.ilike(username)).first():
            flash('❌ Username Taken: This username is already in use. Please choose a different username.', 'error')
            return render_template('register.html')
        
        # Phone number validation (optional but if provided, must be unique)
        if phone:
            # Basic phone format validation (allows various formats)
            phone_clean = re.sub(r'[^\d+]', '', phone)
            if len(phone_clean) < 10:
                flash('❌ Invalid Phone Number: Phone number must contain at least 10 digits.', 'error')
                return render_template('register.html')
            
            # Check for existing phone number
            if User.query.filter(User.phone == phone).first():
                flash('❌ Phone Number Already Registered: This phone number is already registered. Please use a different phone number or try logging in.', 'error')
                return render_template('register.html')
        
        # Check for existing email
        if User.query.filter(User.email.ilike(email)).first():
            flash('❌ Email Already Registered: This email address is already registered. Please use a different email or try logging in.', 'error')
            return render_template('register.html')
        
        # Create new user with verification setup
        user = User(
            username=username, 
            email=email,
            phone=phone if phone else None
        )
        user.set_password(password)
        
        # Generate verification tokens
        user.email_verification_token = generate_verification_token()
        if phone:
            user.phone_verification_code = generate_phone_verification_code()
            user.phone_verification_expires = datetime.utcnow() + timedelta(minutes=10)
        
        # Set admin privileges for specific email
        if email.lower() == os.environ.get('ADMIN_EMAIL', 'admin@kiwellness.org').lower():
            user.is_admin = True
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create user profile
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()
            
            # Send verification emails/SMS
            if send_verification_email(user.email, user.email_verification_token):
                print(f"✅ Verification email sent to {user.email}")
            else:
                print(f"⚠️  Failed to send verification email to {user.email}")
            
            if phone and send_verification_sms(phone, user.phone_verification_code):
                print(f"✅ Verification SMS sent to {phone}")
            else:
                print(f"⚠️  Failed to send verification SMS to {phone}")
            
            # Store user info in session for onboarding
            session['onboarding_user_id'] = user.id
            session['onboarding_username'] = user.username
            session['onboarding_email'] = user.email
            
            flash('✅ Success! Account created successfully. Please complete your profile setup.', 'success')
            return redirect(url_for('onboarding'))
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('❌ Registration Failed: An error occurred during registration. Please try again or contact support if the problem persists.', 'error')
    
    return render_template('register.html')


@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    """Multi-step onboarding process for new users"""
    # Check if user is in onboarding process
    user_id = session.get('onboarding_user_id')
    if not user_id:
        flash('Please create an account first.', 'error')
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        step = request.form.get('step', '1')
        
        if step == '1':  # Agreement acceptance
            privacy_accepted = request.form.get('privacy_policy') == 'on'
            terms_accepted = request.form.get('terms_of_service') == 'on'
            disclaimer_accepted = request.form.get('disclaimer') == 'on'
            
            if not all([privacy_accepted, terms_accepted, disclaimer_accepted]):
                flash('You must accept all agreements to continue.', 'error')
                return render_template('onboarding.html', step=1, user_id=user_id)
            
            # Store agreements in session for next step
            session['agreements_accepted'] = True
            return render_template('onboarding.html', step=2, user_id=user_id)
            
        elif step == '2':  # Basic profile details
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            height = request.form.get('height', '').strip()
            weight = request.form.get('weight', '').strip()
            goal = request.form.get('goal', '').strip()
            custom_goal = request.form.get('customGoal', '').strip()
            
            if not name:
                flash('Name is required.', 'error')
                return render_template('onboarding.html', step=2, user_id=user_id)
            
            try:
                # Update user with phone number
                user = User.query.get(user_id)
                if user:
                    user.phone = phone
                
                # Get or create user profile
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                
                # Update profile with basic information
                profile.name = name
                profile.height = float(height) if height else None
                profile.weight = float(weight) if weight else None
                profile.goal = goal
                profile.custom_goal = custom_goal if goal == 'other' else None
                
                # Create user agreement record
                agreement = UserAgreement(
                    user_id=user_id,
                    privacy_policy_accepted=True,
                    terms_of_service_accepted=True,
                    disclaimer_accepted=True,
                    privacy_policy_version='1.0',
                    terms_version='1.0',
                    disclaimer_version='1.0',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')
                )
                
                db.session.add(agreement)
                db.session.commit()
                
                # Clear onboarding session data
                session.pop('onboarding_user_id', None)
                session.pop('onboarding_username', None)
                session.pop('onboarding_email', None)
                session.pop('agreements_accepted', None)
                
                # Log the user in
                session['user_id'] = user_id
                
                flash('Profile setup completed successfully! Welcome to Ki Wellness.', 'success')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                db.session.rollback()
                flash('Error saving profile. Please try again.', 'error')
                return render_template('onboarding.html', step=2, user_id=user_id)
    
    # GET request - show appropriate step
    step = session.get('agreements_accepted', False)
    return render_template('onboarding.html', step=1 if not step else 2, user_id=user_id)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/verify-email/<token>')
def verify_email(token):
    """Verify user email with token"""
    try:
        user = User.query.filter_by(email_verification_token=token).first()
        
        if not user:
            flash('❌ Invalid verification token. Please check your email or contact support.', 'error')
            return redirect(url_for('login'))
        
        if user.email_verified:
            flash('ℹ️ Email already verified. You can now log in.', 'info')
            return redirect(url_for('login'))
        
        # Mark email as verified
        user.email_verified = True
        user.email_verification_token = None  # Clear the token
        db.session.commit()
        
        flash('✅ Email verified successfully! You can now log in and use AI features.', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        print(f"❌ Error verifying email: {e}")
        flash('❌ Error verifying email. Please try again or contact support.', 'error')
        return redirect(url_for('login'))

@app.route('/verify-phone', methods=['GET', 'POST'])
def verify_phone():
    """Verify user phone number with SMS code"""
    if request.method == 'GET':
        return render_template('verify_phone.html')
    
    try:
        phone = request.form.get('phone')
        code = request.form.get('verification_code')
        
        if not phone or not code:
            flash('❌ Please provide both phone number and verification code.', 'error')
            return render_template('verify_phone.html')
        
        # Find user by phone number
        user = User.query.filter_by(phone=phone).first()
        
        if not user:
            flash('❌ Phone number not found. Please check your phone number or contact support.', 'error')
            return render_template('verify_phone.html')
        
        if user.phone_verified:
            flash('ℹ️ Phone number already verified. You can now log in.', 'info')
            return redirect(url_for('login'))
        
        # Check if code is valid and not expired
        if (user.phone_verification_code != code or 
            not user.phone_verification_expires or 
            user.phone_verification_expires < datetime.utcnow()):
            flash('❌ Invalid or expired verification code. Please check your SMS or request a new code.', 'error')
            return render_template('verify_phone.html')
        
        # Mark phone as verified
        user.phone_verified = True
        user.phone_verification_code = None
        user.phone_verification_expires = None
        db.session.commit()
        
        flash('✅ Phone number verified successfully! You can now log in and use AI features.', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        print(f"❌ Error verifying phone: {e}")
        flash('❌ Error verifying phone. Please try again or contact support.', 'error')
        return render_template('verify_phone.html')

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email/SMS"""
    try:
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if not email and not phone:
            flash('❌ Please provide either email or phone number.', 'error')
            return redirect(url_for('login'))
        
        user = None
        if email:
            user = User.query.filter_by(email=email).first()
        elif phone:
            user = User.query.filter_by(phone=phone).first()
        
        if not user:
            flash('❌ User not found. Please check your information or contact support.', 'error')
            return redirect(url_for('login'))
        
        # Resend email verification if needed
        if not user.email_verified:
            user.email_verification_token = generate_verification_token()
            if send_verification_email(user.email, user.email_verification_token):
                flash('📧 Verification email resent successfully!', 'success')
            else:
                flash('❌ Failed to resend verification email. Please try again or contact support.', 'error')
        
        # Resend SMS verification if needed
        if phone and not user.phone_verified:
            user.phone_verification_code = generate_phone_verification_code()
            user.phone_verification_expires = datetime.utcnow() + timedelta(minutes=10)
            if send_verification_sms(phone, user.phone_verification_code):
                flash('📱 Verification SMS resent successfully!', 'success')
            else:
                flash('❌ Failed to resend verification SMS. Please try again or contact support.', 'error')
        
        db.session.commit()
        return redirect(url_for('login'))
        
    except Exception as e:
        print(f"❌ Error resending verification: {e}")
        flash('❌ Error resending verification. Please try again or contact support.', 'error')
        return redirect(url_for('login'))

@app.route('/extend-session', methods=['POST'])
@login_required
def extend_session():
    """
    SECURITY: Extend user session by updating last activity
    - Allows users to stay logged in when they're actively using the app
    - Maintains security by requiring authentication
    """
    try:
        # Update last activity timestamp
        session['last_activity'] = datetime.utcnow().isoformat()
        session.permanent = True
        
        return jsonify({'success': True, 'message': 'Session extended'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/subscription/status')
@login_required
def subscription_status():
    """Get user's subscription status and usage information"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        usage_summary = get_user_usage_summary(current_user.id)
        if not usage_summary:
            return jsonify({'success': False, 'error': 'Unable to retrieve usage information'}), 500
        
        return jsonify({
            'success': True,
            'data': usage_summary
        })
    except Exception as e:
        print(f"❌ Error getting subscription status: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/subscription/purchase-credits', methods=['POST'])
@login_required
def purchase_session_credits():
    """Handle session credit purchase (redirect to Stripe)"""
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        if quantity < 1 or quantity > 1000:  # Increased limit for bulk purchases
            return jsonify({'success': False, 'error': 'Invalid quantity (1-1000)'}), 400
        
        # Use the new Stripe link that allows custom quantities
        # The link will handle the quantity parameter and calculate total price
        stripe_url = "https://buy.stripe.com/bJe14naFxdDVdGB9ZY3Je06"
        
        # Add user metadata to track the purchase
        current_user = get_current_user()
        if current_user:
            # Store pending purchase in database for tracking
            pending_purchase = SessionCredits(
                user_id=current_user.id,
                credits_purchased=quantity,
                credits_used=0,
                credits_remaining=0,  # Will be updated after payment
                payment_amount_usd=quantity,  # $1 per credit
                payment_status='pending',
                stripe_payment_intent_id=None  # Will be updated after payment
            )
            db.session.add(pending_purchase)
            db.session.commit()
            
            print(f"📝 Created pending purchase record: {quantity} credits for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'redirect_url': stripe_url,
            'message': f'Redirecting to purchase {quantity} session credit(s) for ${quantity:.2f}',
            'quantity': quantity,
            'total_cost': quantity
        })
    except Exception as e:
        print(f"❌ Error processing credit purchase: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_to_subscription():
    """Handle subscription upgrade (redirect to Stripe)"""
    try:
        # Redirect to Stripe checkout for $10/month subscription
        stripe_url = "https://buy.stripe.com/aFadR92917fx9qlgom3Je05"
        
        return jsonify({
            'success': True,
            'redirect_url': stripe_url,
            'message': 'Redirecting to monthly subscription for $10/month'
        })
    except Exception as e:
        print(f"❌ Error processing subscription upgrade: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/stripe/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session for session credits"""
    if not STRIPE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stripe not available'}), 503
    
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        if quantity < 1 or quantity > 1000:
            return jsonify({'success': False, 'error': 'Invalid quantity (1-1000)'}), 400
        
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get current Stripe configuration
        stripe_config = get_stripe_config()
        if not stripe_config:
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 503
        
        # Update Stripe API key if needed
        if stripe.api_key != stripe_config['secret_key']:
            stripe.api_key = stripe_config['secret_key']
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{quantity} AI Session Credit(s)',
                        'description': f'{quantity} AI-powered wellness session credit(s)',
                    },
                    'unit_amount': 100,  # $1.00 in cents
                },
                'quantity': quantity,
            }],
            mode='payment',
            success_url=request.host_url + 'subscription?success=true',
            cancel_url=request.host_url + 'subscription?canceled=true',
            metadata={
                'user_id': current_user.id,
                'type': 'session_credits',
                'quantity': quantity,
                'environment': stripe_config['environment']
            },
            customer_email=current_user.email
        )
        
        # Store pending purchase in database
        pending_purchase = SessionCredits(
            user_id=current_user.id,
            credits_purchased=quantity,
            credits_used=0,
            credits_remaining=0,
            payment_amount_usd=quantity,
            payment_status='pending',
            stripe_payment_intent_id=checkout_session.payment_intent
        )
        db.session.add(pending_purchase)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': checkout_session.id,
            'checkout_url': checkout_session.url
        })
        
    except Exception as e:
        print(f"❌ Error creating checkout session: {e}")
        return jsonify({'success': False, 'error': 'Failed to create checkout session'}), 500

@app.route('/api/stripe/create-subscription', methods=['POST'])
@login_required
def create_subscription():
    """Create a Stripe subscription for monthly plan"""
    if not STRIPE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stripe not available'}), 503
    
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get current Stripe configuration
        stripe_config = get_stripe_config()
        if not stripe_config:
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 503
        
        # Update Stripe API key if needed
        if stripe.api_key != stripe_config['secret_key']:
            stripe.api_key = stripe_config['secret_key']
        
        # Create or get Stripe customer
        customer = None
        if current_user.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(current_user.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
        
        if not customer:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session for subscription
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'recurring': {
                        'interval': 'month',
                    },
                    'product_data': {
                        'name': 'KI Wellness Monthly Subscription',
                        'description': 'Unlimited AI-powered wellness sessions',
                    },
                    'unit_amount': 1000,  # $10.00 in cents
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription?success=true',
            cancel_url=request.host_url + 'subscription?canceled=true',
            customer=customer.id,
            metadata={
                'user_id': current_user.id,
                'type': 'subscription'
            }
        )
        
        return jsonify({
            'success': True,
            'session_id': checkout_session.id,
            'checkout_url': checkout_session.url
        })
        
    except Exception as e:
        print(f"❌ Error creating subscription: {e}")
        return jsonify({'success': False, 'error': 'Failed to create subscription'}), 500

@app.route('/api/stripe/create-portal-session', methods=['POST'])
@login_required
def create_portal_session():
    """Create a Stripe customer portal session for billing management"""
    if not STRIPE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stripe not available'}), 503
    
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get current Stripe configuration
        stripe_config = get_stripe_config()
        if not stripe_config:
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 503
        
        # Update Stripe API key if needed
        if stripe.api_key != stripe_config['secret_key']:
            stripe.api_key = stripe_config['secret_key']
        
        # Get or create Stripe customer
        customer = None
        if current_user.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(current_user.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
        
        if not customer:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=request.host_url + 'settings'
        )
        
        return jsonify({
            'success': True,
            'portal_url': portal_session.url
        })
        
    except Exception as e:
        print(f"❌ Error creating portal session: {e}")
        return jsonify({'success': False, 'error': 'Failed to create portal session'}), 500


@app.route('/subscription/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events for payment confirmations"""
    try:
        # Get current Stripe configuration for webhook verification
        stripe_config = get_stripe_config()
        if not stripe_config:
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 503
        
        # Update Stripe API key if needed
        if stripe.api_key != stripe_config['secret_key']:
            stripe.api_key = stripe_config['secret_key']
        
        # Verify webhook signature in production
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        try:
            if stripe_config['webhook_secret']:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, stripe_config['webhook_secret']
                )
            else:
                # Fallback for development without webhook secret
                event = request.get_json()
        except ValueError as e:
            print(f"❌ Invalid payload: {e}")
            return jsonify({'success': False, 'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            print(f"❌ Invalid signature: {e}")
            return jsonify({'success': False, 'error': 'Invalid signature'}), 400
        
        event_type = event.get('type')
        print(f"📦 Processing Stripe webhook: {event_type}")
        
        if event_type == 'checkout.session.completed':
            # Handle successful checkout session
            session = event.get('data', {}).get('object', {})
            metadata = session.get('metadata', {})
            user_id = metadata.get('user_id')
            payment_type = metadata.get('type')
            environment = metadata.get('environment')
            
            print(f"✅ Checkout completed for user {user_id}, type: {payment_type}, environment: {environment}")
            
            if payment_type == 'session_credits' and user_id:
                # Handle session credits purchase
                quantity = int(metadata.get('quantity', 1))
                amount = session.get('amount_total', 0) / 100  # Convert from cents
                
                # Find and update the pending purchase
                pending_purchase = SessionCredits.query.filter_by(
                    user_id=user_id,
                    payment_status='pending'
                ).order_by(SessionCredits.created_at.desc()).first()
                
                if pending_purchase:
                    pending_purchase.credits_remaining = quantity
                    pending_purchase.payment_amount_usd = amount
                    pending_purchase.payment_status = 'completed'
                    pending_purchase.stripe_payment_intent_id = session.get('payment_intent')
                    
                    # Update user's total credits
                    user = User.query.get(user_id)
                    if user:
                        user.credits_remaining = (user.credits_remaining or 0) + quantity
                    
                    db.session.commit()
                    print(f"✅ Added {quantity} session credits for user {user_id}")
                else:
                    print(f"⚠️  No pending purchase found for user {user_id}")
            
            elif payment_type == 'subscription' and user_id:
                # Handle subscription creation
                subscription_id = session.get('subscription')
                customer_id = session.get('customer')
                
                # Update user subscription
                user_sub = UserSubscription.query.filter_by(user_id=user_id).first()
                if not user_sub:
                    user_sub = UserSubscription(user_id=user_id)
                    db.session.add(user_sub)
                
                user_sub.stripe_subscription_id = subscription_id
                user_sub.stripe_customer_id = customer_id
                user_sub.subscription_type = 'subscription'
                user_sub.is_active = True
                user_sub.billing_cycle_start = datetime.utcnow()
                
                db.session.commit()
                print(f"✅ Created subscription for user {user_id}")
        
        elif event_type == 'customer.subscription.created':
            # Handle subscription creation (backup)
            subscription = event.get('data', {}).get('object', {})
            customer_id = subscription.get('customer')
            metadata = subscription.get('metadata', {})
            user_id = metadata.get('user_id')
            
            if user_id:
                # Update user subscription
                user_sub = UserSubscription.query.filter_by(user_id=user_id).first()
                if not user_sub:
                    user_sub = UserSubscription(user_id=user_id)
                    db.session.add(user_sub)
                
                user_sub.stripe_subscription_id = subscription.get('id')
                user_sub.stripe_customer_id = customer_id
                user_sub.subscription_type = 'subscription'
                user_sub.is_active = True
                user_sub.billing_cycle_start = datetime.utcnow()
                
                db.session.commit()
                print(f"✅ Updated subscription for user {user_id}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"❌ Error processing Stripe webhook: {e}")
        return jsonify({'success': False, 'error': 'Webhook processing failed'}), 500

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email is required', 'error')
            return render_template('forgot_password.html')
        
        # Check if user exists
        user = User.query.filter(User.email.ilike(email)).first()
        
        if user:
            # In a real application, you would:
            # 1. Generate a secure reset token
            # 2. Store it in the database with expiration
            # 3. Send an email with the reset link
            # 4. Use a proper email service like SendGrid or AWS SES
            
            # For demo purposes, we'll just show a success message
            flash('If an account with that email exists, we have sent a password reset link.', 'success')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, we have sent a password reset link.', 'success')
        
        return render_template('forgot_password.html')
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # In a real application, you would:
    # 1. Validate the token from the database
    # 2. Check if it's expired
    # 3. Allow password reset if valid
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Both password fields are required', 'error')
            return render_template('reset_password.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('reset_password.html')
        
        # In a real application, you would:
        # 1. Update the user's password
        # 2. Invalidate the reset token
        # 3. Log the password change
        
        flash('Password has been reset successfully. You can now log in with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

@app.route('/profile')
@login_required
def profile():
    # Get user profile data
    user_profile = get_current_user_profile()
    current_user = get_current_user()
    return render_template('profile.html', profile=user_profile, current_user=current_user)

@app.route('/settings')
@login_required
def settings():
    """Settings page with verification status and billing management"""
    current_user = get_current_user()
    
    # Get usage history for the user
    usage_history = []
    try:
        # Get recent token usage for the user
        recent_usage = TokenUsage.query.filter_by(user_id=current_user.id).order_by(TokenUsage.created_at.desc()).limit(5).all()
        for usage in recent_usage:
            usage_history.append({
                'date': usage.created_at.strftime('%B %d, %Y'),
                'questions_used': usage.total_tokens
            })
    except Exception:
        pass
    
    # Get last purchase date
    last_purchase = SessionCredits.query.filter_by(
        user_id=current_user.id, 
        payment_status='completed'
    ).order_by(SessionCredits.created_at.desc()).first()
    
    last_purchase_date = last_purchase.created_at.strftime('%B %d, %Y') if last_purchase else 'Never'
    
    # Calculate total questions used
    total_questions_used = sum(usage.total_tokens for usage in TokenUsage.query.filter_by(user_id=current_user.id).all())
    
    return render_template('settings.html', 
                         current_user=current_user,
                         usage_history=usage_history,
                         last_purchase_date=last_purchase_date,
                         total_questions_used=total_questions_used)


@app.route('/subscription')
@login_required
def subscription():
    """Dedicated subscription management page"""
    return render_template('subscription.html')

@app.route('/food-journal')
@login_required
def food_journal():
    return render_template('food_journal.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard - only accessible by admin users"""
    # Get only top 5 recently active users (by last activity/updated_at)
    users = User.query.order_by(User.updated_at.desc()).limit(5).all()
    
    # Get total user count for statistics
    total_users_count = User.query.count()
    
    # Try to get user profiles, but handle gracefully if table doesn't exist
    try:
        user_profiles = UserProfile.query.all()
        users_with_profiles = len(user_profiles)
        users_without_profiles = total_users_count - len(user_profiles)
    except Exception:
        # If UserProfile table doesn't exist or has issues, default to 0
        user_profiles = []
        users_with_profiles = 0
        users_without_profiles = total_users_count
    
    # Enhanced user statistics
    user_stats = {
        'total_users': total_users_count,
        'admin_users': User.query.filter_by(is_admin=True).count(),
        'regular_users': User.query.filter_by(is_admin=False).count(),
        'users_with_profiles': users_with_profiles,
        'users_without_profiles': users_without_profiles,
        'recent_signups': User.query.filter(User.created_at >= (datetime.utcnow() - timedelta(days=7))).count()
    }
    
    # System statistics
    system_stats = {
        'total_food_entries': FoodJournal.query.count(),
        'total_mood_entries': MoodEntry.query.count(),
        'total_reminders': Reminder.query.count(),
        'active_reminders': Reminder.query.filter_by(is_active=True).count(),
        'total_reviews': Review.query.count(),
        'pending_reviews': Review.query.filter_by(is_approved=False).count(),
        'approved_reviews': Review.query.filter_by(is_approved=True).count()
    }
    
    # Get pending reviews
    pending_reviews = Review.query.filter_by(is_approved=False).order_by(Review.created_at.desc()).all()
    
    # Get recent user activity (already limited to 5 above)
    recent_users = users
    
    # Get system health data
    system_health = {
        'database_size': 'Healthy',  # Placeholder for actual DB size calculation
        'last_backup': 'Today',  # Placeholder for backup tracking
        'error_rate': '0.1%',  # Placeholder for error monitoring
        'uptime': '99.9%'  # Placeholder for uptime tracking
    }
    
    # Get current month token usage and calculate profit
    current_month = datetime.utcnow().strftime('%Y-%m')
    monthly_token_usage = TokenUsage.query.filter_by(month=current_month).all()
    total_monthly_tokens = sum(usage.total_tokens for usage in monthly_token_usage)
    total_monthly_cost = sum(usage.cost_usd for usage in monthly_token_usage)
    
    # Calculate current month profit with actual payment data
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get actual payments received this month from SessionCredits
    monthly_payments = SessionCredits.query.filter(
        SessionCredits.created_at >= current_month_start,
        SessionCredits.payment_status == 'completed'
    ).all()
    
    total_monthly_payments = sum(payment.payment_amount_usd for payment in monthly_payments)
    
    # Get subscription revenue for current month
    active_subscriptions = UserSubscription.query.filter_by(is_active=True).all()
    subscription_revenue = sum(sub.monthly_fee_usd for sub in active_subscriptions)
    
    # Total revenue = payments + subscriptions
    total_monthly_revenue = total_monthly_payments + subscription_revenue
    current_month_profit = total_monthly_revenue - total_monthly_cost
    
    # Get API costs for display
    api_costs = APICosts.query.filter_by(is_active=True).all()
    
    # Get current GPT model and its costs
    current_model = get_current_gpt_model()
    current_model_costs = next((cost for cost in api_costs if cost.model_name == current_model), None)
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         stats=user_stats, 
                         system_stats=system_stats,
                         pending_reviews=pending_reviews,
                         recent_users=recent_users,
                         system_health=system_health,
                         new_accounts_enabled=are_new_accounts_enabled(),
                         openai_enabled=is_openai_enabled(),
                         emergency_stop_active=get_system_setting('emergency_stop_active', False),
                         monthly_token_usage=monthly_token_usage,
                         total_monthly_tokens=total_monthly_tokens,
                         total_monthly_cost=total_monthly_cost,
                         current_month_profit=current_month_profit,
                         total_monthly_revenue=total_monthly_revenue,
                         total_monthly_payments=total_monthly_payments,
                         subscription_revenue=subscription_revenue,
                         api_costs=api_costs,
                         current_gpt_model=current_model,
                         current_model_costs=current_model_costs,
                         max_input_tokens=get_max_input_tokens(),
                         max_output_tokens=get_max_output_tokens(),
                         max_total_tokens=get_max_total_tokens(),
                         flexible_service_tier=get_flexible_service_tier(),
                         presence_penalty=get_presence_penalty(),
                         frequency_penalty=get_frequency_penalty(),
                         top_p=get_top_p(),
                         payment_testing_mode=get_system_setting('payment_testing_mode', False),
                         oauth_available=OAUTH_AVAILABLE,
                         google_client_id=os.environ.get('GOOGLE_CLIENT_ID'),
                         google_client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'))


@app.route('/admin/reviews/<int:review_id>/approve', methods=['POST'])
@admin_required
def approve_review(review_id):
    """Approve a review for public display"""
    try:
        review = Review.query.get_or_404(review_id)
        review.is_approved = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Review approved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error approving review: {str(e)}'})


@app.route('/admin/reviews/<int:review_id>/reject', methods=['POST'])
@admin_required
def reject_review(review_id):
    """Reject and delete a review"""
    try:
        review = Review.query.get_or_404(review_id)
        db.session.delete(review)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Review rejected and deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error rejecting review: {str(e)}'})

@app.route('/profile/save', methods=['POST'])
@login_required
def save_profile():
    """
    SECURITY: Save profile data for current user only
    - Ensures users can only modify their own profile data
    - Prevents unauthorized modification of other users' profiles
    """
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        
        # Get or create user profile
        profile = get_current_user_profile()
        if not profile:
            profile = UserProfile(user_id=get_current_user().id)
            db.session.add(profile)
        
        # SECURITY: Verify user has access to modify their profile data
        verify_user_data_access(profile, "profile_save")
        
        # Update profile fields
        profile.name = data.get('name')
        
        # Update user phone field
        user = get_current_user()
        if user:
            user.phone = data.get('phone')
        
        # Handle date_of_birth with better error handling
        try:
            if data.get('date_of_birth'):
                profile.date_of_birth = datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date()
            else:
                profile.date_of_birth = None
        except ValueError as e:
            print(f"Error parsing date_of_birth: {data.get('date_of_birth')} - {e}")
            profile.date_of_birth = None
        
        # Handle numeric fields with conversion
        try:
            profile.age = int(data.get('age')) if data.get('age') else None
        except (ValueError, TypeError):
            profile.age = None
            
        try:
            profile.weight = float(data.get('weight')) if data.get('weight') else None
        except (ValueError, TypeError):
            profile.weight = None
            
        try:
            profile.height = float(data.get('height')) if data.get('height') else None
        except (ValueError, TypeError):
            profile.height = None
        
        profile.goals = data.get('goals')
        profile.goal = data.get('goal')  # Primary wellness goal
        profile.custom_goal = data.get('custom_goal')
        profile.ailments = data.get('ailments')
        profile.daily_activities = data.get('daily_activities')
        profile.day_notes = data.get('day_notes')
        profile.sleep_schedule = data.get('sleep_schedule')
        profile.night_notes = data.get('night_notes')
        profile.dietary_preferences = data.get('dietary_preferences')
        profile.exercise_routine = data.get('exercise_routine')
        profile.spiritual_religion = data.get('spiritual_religion')
        profile.self_connection = data.get('self_connection')
        profile.surroundings_connection = data.get('surroundings_connection')
        profile.providing_others = data.get('providing_others')
        profile.safe_groups = data.get('safe_groups')
        profile.awe_things = data.get('awe_things')
        profile.creative_expression = data.get('creative_expression')
        profile.upsetting_situations = data.get('upsetting_situations')
        profile.spirit_notes = data.get('spirit_notes')
        profile.avatar = data.get('avatar', 'default-avatar.png')
        profile.weight_unit = data.get('weight_unit', 'kg')
        profile.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile saved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/profile/data')
@login_required
def get_profile_data():
    """
    SECURITY: Get profile data for current user only
    - Ensures users can only access their own profile data
    - Prevents unauthorized access to other users' personal information
    """
    try:
        profile = get_current_user_profile()
        if profile:
            user = get_current_user()
            
            # SECURITY: Verify user has access to their profile data
            verify_user_data_access(profile, "profile_data")
            
            return jsonify({
                'name': profile.name,
                'username': user.username if user else None,
                'email': user.email if user else None,
                'phone': user.phone if user else None,
                'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                'age': profile.age,
                'weight': profile.weight,
                'height': profile.height,
                'goals': profile.goals,
                'goal': profile.goal,
                'custom_goal': profile.custom_goal,
                'ailments': profile.ailments,
                'daily_activities': profile.daily_activities,
                'day_notes': profile.day_notes,
                'sleep_schedule': profile.sleep_schedule,
                'night_notes': profile.night_notes,
                'dietary_preferences': profile.dietary_preferences,
                'exercise_routine': profile.exercise_routine,
                'spiritual_religion': profile.spiritual_religion,
                'self_connection': profile.self_connection,
                'surroundings_connection': profile.surroundings_connection,
                'providing_others': profile.providing_others,
                'safe_groups': profile.safe_groups,
                'awe_things': profile.awe_things,
                'creative_expression': profile.creative_expression,
                'upsetting_situations': profile.upsetting_situations,
                'spirit_notes': profile.spirit_notes,
                'avatar': profile.avatar,
                'weight_unit': profile.weight_unit
            })
        return jsonify({})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """
    SECURITY: Change user password
    - Requires current password verification
    - Validates new password strength
    - Ensures users can only change their own password
    """
    try:
        # Get current user
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        # SECURITY: Verify user has access to change their password
        verify_user_data_access(get_current_user_profile(), "password_change")
        
        # Get request data
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate input
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'error': 'All password fields are required'})
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'})
        
        # Check if new passwords match
        if new_password != confirm_password:
            return jsonify({'success': False, 'error': 'New passwords do not match'})
        
        # Validate new password strength
        import re
        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters long'})
        
        if not re.search(r'[A-Z]', new_password):
            return jsonify({'success': False, 'error': 'Password must contain at least one uppercase letter'})
        
        if not re.search(r'[a-z]', new_password):
            return jsonify({'success': False, 'error': 'Password must contain at least one lowercase letter'})
        
        if not re.search(r'\d', new_password):
            return jsonify({'success': False, 'error': 'Password must contain at least one number'})
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            return jsonify({'success': False, 'error': 'Password must contain at least one special character'})
        
        # Check if new password is different from current
        if user.check_password(new_password):
            return jsonify({'success': False, 'error': 'New password must be different from current password'})
        
        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Food Journal Routes
@app.route('/food-journal/search', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def search_food():
    try:
        data = request.get_json()
        food_name = data.get('food_name', '').strip()
        serving_size = float(data.get('serving_size', 0))
        serving_unit = data.get('serving_unit', 'g')
        
        barcode = data.get('barcode', '').strip()
        
        if not food_name and not barcode:
            return jsonify({'success': False, 'error': 'Food name or barcode is required'})
        
        # If barcode is provided, try barcode search first
        if barcode:
            nutrition_data = search_openfoodfacts_by_barcode(barcode)
            if nutrition_data:
                # Convert for user's serving size
                converted_data = convert_nutritional_data(nutrition_data, serving_size, serving_unit)
                return jsonify({'success': True, 'data': converted_data, 'source': 'openfoodfacts_barcode'})
        
        # First check food cache
        cached_food = FoodCache.query.filter(
            FoodCache.food_name.ilike(f'%{food_name}%')
        ).first()
        
        if cached_food:
            # Convert nutritional data for user's serving size
            nutrition_data = {
                'food_name': cached_food.food_name,
                'brand': cached_food.brand,
                'serving_size': cached_food.serving_size,
                'serving_unit': cached_food.serving_unit,
                'calories': cached_food.calories,
                'protein': cached_food.protein,
                'carbs': cached_food.carbs,
                'fat': cached_food.fat,
                'fiber': cached_food.fiber,
                'sugar': cached_food.sugar,
                'sodium': cached_food.sodium,
                'source': cached_food.source
            }
            
            converted_data = convert_nutritional_data(nutrition_data, serving_size, serving_unit)
            return jsonify({'success': True, 'data': converted_data, 'source': 'cache'})
        
        # Search strategy: Common foods DB -> Open Food Facts -> USDA API
        nutrition_data = None
        source_used = None
        
        # 1. Try common foods database first (most accurate)
        nutrition_data = search_common_foods_database(food_name)
        if nutrition_data:
            source_used = 'common_foods_db'
            print(f"✅ Found in common foods DB: {food_name}")
        
        # 2. Try Open Food Facts API
        if not nutrition_data:
            nutrition_data = search_openfoodfacts_api(food_name)
            if nutrition_data:
                source_used = 'openfoodfacts'
                print(f"✅ Found in Open Food Facts: {food_name}")
        
        # 3. Try USDA API (if API key is available)
        if not nutrition_data:
            nutrition_data = search_usda_api(food_name)
            if nutrition_data:
                source_used = 'usda'
                print(f"✅ Found in USDA API: {food_name}")
        
        if nutrition_data:
            # Save to cache
            cached_food = FoodCache(
                food_name=nutrition_data['food_name'],
                brand=nutrition_data['brand'],
                serving_size=nutrition_data['serving_size'],
                serving_unit=nutrition_data['serving_unit'],
                calories=nutrition_data['calories'],
                protein=nutrition_data['protein'],
                carbs=nutrition_data['carbs'],
                fat=nutrition_data['fat'],
                fiber=nutrition_data['fiber'],
                sugar=nutrition_data['sugar'],
                sodium=nutrition_data['sodium'],
                source=nutrition_data['source']
            )
            db.session.add(cached_food)
            db.session.commit()
            
            # Convert for user's serving size
            converted_data = convert_nutritional_data(nutrition_data, serving_size, serving_unit)
            return jsonify({'success': True, 'data': converted_data, 'source': nutrition_data['source']})
        
        return jsonify({'success': False, 'error': 'Food not found in databases'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/food-journal/add', methods=['POST'])
@limiter.limit("20 per minute")
@login_required
def add_food_entry():
    try:
        data = request.get_json()
        print(f"📝 Received food entry data: {data}")
        
        # Get current user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            print("❌ User profile not found")
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        print(f"✅ User profile found: {user_profile.id}")
        
        # Handle timezone-aware datetime
        browser_timezone = data.get('browser_timezone')
        if data.get('consumed_at'):
            try:
                # Try to parse ISO format first (e.g., '2025-08-12T19:42:57.623Z')
                consumed_at = datetime.fromisoformat(data['consumed_at'].replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Fallback to old format (e.g., '2025-08-12 19:42')
                    consumed_at = datetime.strptime(data['consumed_at'], '%Y-%m-%d %H:%M')
                except ValueError:
                    # If all parsing fails, use current time
                    consumed_at = get_browser_timezone_datetime(browser_timezone) if browser_timezone else datetime.utcnow()
        else:
            consumed_at = get_browser_timezone_datetime(browser_timezone) if browser_timezone else datetime.utcnow()
        
        print(f"📅 Consumed at: {consumed_at}")
        
        # Create food journal entry with comprehensive nutritional data
        food_entry = FoodJournal(
            user_id=user_profile.id,
            food_name=data['food_name'],
            brand=data.get('brand'),
            serving_size=data['serving_size'],
            serving_unit=data['serving_unit'],
            
            # Core nutritional values (displayed to user)
            calories=data.get('calories'),
            protein=data.get('protein'),
            carbs=data.get('carbs'),
            fat=data.get('fat'),
            fiber=data.get('fiber'),
            sugar=data.get('sugar'),
            sodium=data.get('sodium'),
            
            # Extended nutritional values (stored but not displayed)
            saturated_fat=data.get('saturated_fat'),
            trans_fat=data.get('trans_fat'),
            cholesterol=data.get('cholesterol'),
            potassium=data.get('potassium'),
            calcium=data.get('calcium'),
            iron=data.get('iron'),
            vitamin_a=data.get('vitamin_a'),
            vitamin_c=data.get('vitamin_c'),
            vitamin_d=data.get('vitamin_d'),
            vitamin_e=data.get('vitamin_e'),
            vitamin_k=data.get('vitamin_k'),
            vitamin_b6=data.get('vitamin_b6'),
            vitamin_b12=data.get('vitamin_b12'),
            magnesium=data.get('magnesium'),
            zinc=data.get('zinc'),
            phosphorus=data.get('phosphorus'),
            manganese=data.get('manganese'),
            selenium=data.get('selenium'),
            copper=data.get('copper'),
            thiamin=data.get('thiamin'),
            riboflavin=data.get('riboflavin'),
            niacin=data.get('niacin'),
            folate=data.get('folate'),
            pantothenic_acid=data.get('pantothenic_acid'),
            biotin=data.get('biotin'),
            choline=data.get('choline'),
            betaine=data.get('betaine'),
            taurine=data.get('taurine'),
            caffeine=data.get('caffeine'),
            alcohol=data.get('alcohol'),
            water_content=data.get('water_content'),
            ash=data.get('ash'),
            
            # Metadata
            data_source=data.get('data_source'),
            barcode=data.get('barcode'),
            time_of_day=data.get('time_of_day'),
            water_amount=data.get('water_amount'),
            water_unit=data.get('water_unit'),
            mood=data.get('mood'),
            notes=data.get('notes'),
            consumed_at=consumed_at
        )
        
        print(f"🍽️ Created food entry object: {food_entry.food_name}")
        
        db.session.add(food_entry)
        db.session.commit()
        
        print("✅ Food entry saved successfully")
        return jsonify({'success': True, 'message': 'Food entry added successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error adding food entry: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/food-journal/entries')
@login_required
def get_food_entries():
    """
    SECURITY: Get food journal entries for current user only
    - Filters by user_id to ensure data isolation
    - Only authenticated users can access their own data
    """
    try:
        # Get current user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # SECURITY: Verify user has access to their data
        verify_user_data_access(user_profile, "food_entries")
        
        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date and end_date:
            # Parse date range
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
            
            entries = FoodJournal.query.filter(
                FoodJournal.user_id == user_profile.id,
                FoodJournal.consumed_at >= start_datetime,
                FoodJournal.consumed_at < end_datetime
            ).order_by(FoodJournal.consumed_at.desc()).all()
        else:
            # Default to last 7 days if no date range provided
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            entries = FoodJournal.query.filter(
                FoodJournal.user_id == user_profile.id,
                FoodJournal.consumed_at >= seven_days_ago
            ).order_by(FoodJournal.consumed_at.desc()).all()
        
        entries_data = []
        for entry in entries:
            entries_data.append({
                'id': entry.id,
                'food_name': entry.food_name,
                'brand': entry.brand,
                'serving_size': entry.serving_size,
                'serving_unit': entry.serving_unit,
                'calories': entry.calories,
                'protein': entry.protein,
                'carbs': entry.carbs,
                'fat': entry.fat,
                'fiber': entry.fiber,
                'sugar': entry.sugar,
                'sodium': entry.sodium,
                'time_of_day': entry.time_of_day,
                'water_amount': entry.water_amount,
                'water_unit': entry.water_unit,
                'mood': entry.mood,
                'notes': entry.notes,
                'consumed_at': entry.consumed_at.isoformat()
            })
        
        return jsonify({'success': True, 'entries': entries_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/food-journal/delete', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def delete_food_entries():
    """
    SECURITY: Delete food journal entries for current user only
    - Filters by user_id to ensure users can only delete their own data
    - Prevents unauthorized deletion of other users' data
    """
    try:
        # Get current user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # SECURITY: Verify user has access to their data
        verify_user_data_access(user_profile, "food_delete")
        
        data = request.get_json()
        entry_ids = data.get('entry_ids', [])
        
        if not entry_ids:
            return jsonify({'success': False, 'error': 'No entries selected'})
        
        # Delete selected entries (only for current user)
        FoodJournal.query.filter(
            FoodJournal.user_id == user_profile.id,
            FoodJournal.id.in_(entry_ids)
        ).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Deleted {len(entry_ids)} entries'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/food-journal/export')
@login_required
def export_food_journal():
    """
    SECURITY: Export food journal data for current user only
    - Filters by user_id to ensure users can only export their own data
    - Prevents unauthorized access to other users' data
    """
    try:
        # Get current user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # SECURITY: Verify user has access to their data
        verify_user_data_access(user_profile, "food_export")
        
        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date and end_date:
            # Parse date range
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
            
            entries = FoodJournal.query.filter(
                FoodJournal.user_id == user_profile.id,
                FoodJournal.consumed_at >= start_datetime,
                FoodJournal.consumed_at < end_datetime
            ).order_by(FoodJournal.consumed_at.desc()).all()
        else:
            # Default to last 7 days if no date range provided
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            entries = FoodJournal.query.filter(
                FoodJournal.user_id == user_profile.id,
                FoodJournal.consumed_at >= seven_days_ago
            ).order_by(FoodJournal.consumed_at.desc()).all()
        
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Time', 'Food Name', 'Brand', 'Serving Size', 'Serving Unit',
            'Meal Time', 'Water Amount', 'Water Unit',
            'Calories', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Fiber (g)', 'Sugar (g)', 'Sodium (mg)',
            'Mood', 'Notes'
        ])
        
        # Write data
        for entry in entries:
            # Format date and time in user's timezone (stored as UTC, display in local)
            consumed_date = entry.consumed_at.strftime('%Y-%m-%d')
            consumed_time = entry.consumed_at.strftime('%H:%M')
            
            writer.writerow([
                consumed_date, consumed_time, entry.food_name, entry.brand,
                entry.serving_size, entry.serving_unit, entry.time_of_day or '',
                entry.water_amount or '', entry.water_unit or '',
                entry.calories, entry.protein, entry.carbs, entry.fat, entry.fiber,
                entry.sugar, entry.sodium, entry.mood or '', entry.notes or ''
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'food_journal_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/food-journal/import', methods=['POST'])
@login_required
def import_food_journal():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Please upload a CSV file'})
        
        # Get current user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # Get field mappings if provided
        field_mappings = request.form.get('field_mappings')
        if field_mappings:
            try:
                field_mappings = json.loads(field_mappings)
            except json.JSONDecodeError:
                return jsonify({'success': False, 'error': 'Invalid field mappings format'})
        else:
            # Default field mappings for backward compatibility
            field_mappings = {
                'food_name': 'Food Name',
                'brand': 'Brand',
                'serving_size': 'Serving Size',
                'serving_unit': 'Serving Unit',
                'calories': 'Calories',
                'protein': 'Protein (g)',
                'carbs': 'Carbs (g)',
                'fat': 'Fat (g)',
                'fiber': 'Fiber (g)',
                'sugar': 'Sugar (g)',
                'sodium': 'Sodium (mg)',
                'mood': 'Mood',
                'notes': 'Notes',
                'date': 'Date',
                'time': 'Time'
            }
        
        # Read CSV file
        content = file.read().decode('utf-8')
        csv_data = csv.DictReader(io.StringIO(content))
        
        imported_count = 0
        errors = []
        
        for row in csv_data:
            try:
                # Parse date and time using field mappings
                date_str = row.get(field_mappings.get('date', 'Date'), '')
                time_str = row.get(field_mappings.get('time', 'Time'), '')
                
                if date_str and time_str:
                    # Parse as local time and convert to UTC for storage
                    local_dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
                    consumed_at = local_dt
                elif date_str:
                    # If only date is provided, assume midnight
                    local_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    consumed_at = local_dt
                else:
                    consumed_at = datetime.utcnow()
                
                # Create food entry using field mappings
                food_entry = FoodJournal(
                    user_id=user_profile.id,
                    food_name=row.get(field_mappings.get('food_name', 'Food Name'), ''),
                    brand=row.get(field_mappings.get('brand', 'Brand'), ''),
                    serving_size=float(row.get(field_mappings.get('serving_size', 'Serving Size'), 0)),
                    serving_unit=row.get(field_mappings.get('serving_unit', 'Serving Unit'), 'g'),
                    calories=float(row.get(field_mappings.get('calories', 'Calories'), 0)) if row.get(field_mappings.get('calories', 'Calories')) else None,
                    protein=float(row.get(field_mappings.get('protein', 'Protein (g)'), 0)) if row.get(field_mappings.get('protein', 'Protein (g)')) else None,
                    carbs=float(row.get(field_mappings.get('carbs', 'Carbs (g)'), 0)) if row.get(field_mappings.get('carbs', 'Carbs (g)')) else None,
                    fat=float(row.get(field_mappings.get('fat', 'Fat (g)'), 0)) if row.get(field_mappings.get('fat', 'Fat (g)')) else None,
                    fiber=float(row.get(field_mappings.get('fiber', 'Fiber (g)'), 0)) if row.get(field_mappings.get('fiber', 'Fiber (g)')) else None,
                    sugar=float(row.get(field_mappings.get('sugar', 'Sugar (g)'), 0)) if row.get(field_mappings.get('sugar', 'Sugar (g)')) else None,
                    sodium=float(row.get(field_mappings.get('sodium', 'Sodium (mg)'), 0)) if row.get(field_mappings.get('sodium', 'Sodium (mg)')) else None,
                    mood=row.get(field_mappings.get('mood', 'Mood'), ''),
                    notes=row.get(field_mappings.get('notes', 'Notes'), ''),
                    consumed_at=consumed_at
                )
                
                db.session.add(food_entry)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {imported_count + 1}: {str(e)}")
        
        # Clear patterns cache to force dashboard refresh with new data
        if imported_count > 0:
            PatternsCache.query.filter_by(user_id=user_profile.id).delete()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Imported {imported_count} entries successfully. Dashboard will refresh with new data.',
            'imported_count': imported_count,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

def analyze_patterns_with_openai(entries_data, time_period, user_profile=None):
    """Analyze food journal patterns using OpenAI API with user profile context"""
    try:
        # Check emergency stop first
        if is_emergency_stop_active():
            print("🚨 EMERGENCY STOP ACTIVE: OpenAI API calls are disabled")
            return {
                'analysis': "⚠️ AI analysis is temporarily unavailable due to emergency stop. Please try again later or contact support.",
                'suggestions': "System is in maintenance mode. Please check back later.",
                'error': 'emergency_stop_active'
            }
        
        # Check if OpenAI is enabled
        if not is_openai_enabled():
            print("🚫 OpenAI API is disabled")
            return {
                'analysis': "⚠️ AI analysis is currently disabled. Please try again later or contact support.",
                'suggestions': "System is in maintenance mode. Please check back later.",
                'error': 'openai_disabled'
            }
        
        # Check if user is verified for AI usage
        current_user = get_current_user()
        if current_user and not is_user_verified_for_ai(current_user):
            print("🔒 User not verified for AI usage")
            return {
                'analysis': "⚠️ Account Verification Required: Please verify your email and phone number before using AI features.",
                'suggestions': "Check your email and phone for verification codes, or contact support for assistance.",
                'error': 'verification_required'
            }
        
        # Check if user has AI usage permissions
        if current_user and not can_user_use_ai(current_user.id):
            print("🔒 User has no AI usage sessions or credits remaining")
            return {
                'analysis': "⚠️ AI Usage Limit Reached: You've used all your monthly sessions and have no credits remaining.",
                'suggestions': "Upgrade to monthly subscription or purchase session credits to continue using AI features.",
                'error': 'usage_limit_reached'
            }
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Prepare the data for analysis with comprehensive nutritional data
        analysis_data = {
            'total_entries': len(entries_data),
            'foods': [],
            'moods': [],
            'water_intake': [],
            'water_entries': [],
            'dashboard_water_entries': [],
            'meal_times': [],
            'nutritional_totals': {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0,
                'sugar': 0,
                'sodium': 0
            },
            'extended_nutritional_totals': {
                'saturated_fat': 0,
                'trans_fat': 0,
                'cholesterol': 0,
                'potassium': 0,
                'calcium': 0,
                'iron': 0,
                'vitamin_a': 0,
                'vitamin_c': 0,
                'vitamin_d': 0,
                'vitamin_e': 0,
                'vitamin_k': 0,
                'vitamin_b6': 0,
                'vitamin_b12': 0,
                'magnesium': 0,
                'zinc': 0,
                'phosphorus': 0,
                'manganese': 0,
                'selenium': 0,
                'copper': 0,
                'thiamin': 0,
                'riboflavin': 0,
                'niacin': 0,
                'folate': 0,
                'pantothenic_acid': 0,
                'biotin': 0,
                'choline': 0,
                'betaine': 0,
                'taurine': 0,
                'caffeine': 0,
                'alcohol': 0,
                'water_content': 0,
                'ash': 0
            },
            'nutritional_insights': {
                'micronutrient_gaps': [],
                'vitamin_deficiencies': [],
                'mineral_deficiencies': [],
                'nutrient_ratios': {},
                'data_quality': {
                    'entries_with_full_nutrition': 0,
                    'entries_with_basic_nutrition': 0,
                    'entries_with_no_nutrition': 0
                }
            }
        }
        
        for entry in entries_data:
            # Collect food data with comprehensive nutritional information
            if entry.get('food_name'):
                food_data = {
                    'name': entry['food_name'],
                    'brand': entry.get('brand'),
                    'serving_size': entry.get('serving_size'),
                    'serving_unit': entry.get('serving_unit'),
                    'time_of_day': entry.get('time_of_day'),
                    'data_source': entry.get('data_source'),
                    'barcode': entry.get('barcode')
                }
                
                # Add core nutritional data
                core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
                for nutrient in core_nutrients:
                    if entry.get(nutrient) is not None:
                        food_data[nutrient] = entry[nutrient]
                
                # Add extended nutritional data
                extended_nutrients = [
                    'saturated_fat', 'trans_fat', 'cholesterol', 'potassium', 'calcium', 'iron',
                    'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 'vitamin_b6', 'vitamin_b12',
                    'magnesium', 'zinc', 'phosphorus', 'manganese', 'selenium', 'copper', 'thiamin',
                    'riboflavin', 'niacin', 'folate', 'pantothenic_acid', 'biotin', 'choline', 'betaine',
                    'taurine', 'caffeine', 'alcohol', 'water_content', 'ash'
                ]
                for nutrient in extended_nutrients:
                    if entry.get(nutrient) is not None:
                        food_data[nutrient] = entry[nutrient]
                
                analysis_data['foods'].append(food_data)
            
            # Collect mood data
            if entry.get('mood'):
                analysis_data['moods'].append(entry['mood'])
            
            # Collect water data with enhanced categorization
            if entry.get('water_amount') and entry.get('water_unit'):
                water_oz = 0
                if entry['water_unit'] == 'oz':
                    water_oz = entry['water_amount']
                elif entry['water_unit'] == 'liters':
                    water_oz = entry['water_amount'] * 33.814
                elif entry['water_unit'] == 'gallons':
                    water_oz = entry['water_amount'] * 128
                
                analysis_data['water_intake'].append(water_oz)
                
                # Categorize water entries
                water_entry = {
                    'amount': water_oz,
                    'unit': entry['water_unit'],
                    'source': entry['food_name'],
                    'time': entry.get('consumed_at', ''),
                    'mood': entry.get('mood', ''),
                    'notes': entry.get('notes', '')
                }
                analysis_data['water_entries'].append(water_entry)
                
                # Identify dashboard water entries
                if entry['food_name'] == 'Water Intake':
                    analysis_data['dashboard_water_entries'].append(water_entry)
            
            # Collect meal time data
            if entry.get('time_of_day'):
                analysis_data['meal_times'].append(entry['time_of_day'])
            
            # Sum core nutritional data
            core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
            for nutrient in core_nutrients:
                if entry.get(nutrient) is not None:
                    analysis_data['nutritional_totals'][nutrient] += entry[nutrient]
            
            # Sum extended nutritional data
            extended_nutrients = [
                'saturated_fat', 'trans_fat', 'cholesterol', 'potassium', 'calcium', 'iron',
                'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 'vitamin_b6', 'vitamin_b12',
                'magnesium', 'zinc', 'phosphorus', 'manganese', 'selenium', 'copper', 'thiamin',
                'riboflavin', 'niacin', 'folate', 'pantothenic_acid', 'biotin', 'choline', 'betaine',
                'taurine', 'caffeine', 'alcohol', 'water_content', 'ash'
            ]
            for nutrient in extended_nutrients:
                if entry.get(nutrient) is not None:
                    analysis_data['extended_nutritional_totals'][nutrient] += entry[nutrient]
            
            # Analyze data quality
            has_core_nutrition = any(entry.get(nutrient) is not None for nutrient in core_nutrients)
            has_extended_nutrition = any(entry.get(nutrient) is not None for nutrient in extended_nutrients)
            
            if has_extended_nutrition:
                analysis_data['nutritional_insights']['data_quality']['entries_with_full_nutrition'] += 1
            elif has_core_nutrition:
                analysis_data['nutritional_insights']['data_quality']['entries_with_basic_nutrition'] += 1
            else:
                analysis_data['nutritional_insights']['data_quality']['entries_with_no_nutrition'] += 1
        
        # Prepare user profile context with personal touch
        user_name = user_profile.name if user_profile and user_profile.name else "there"
        profile_context = ""
        if user_profile:
            profile_context = f"""
        PERSONAL CONTEXT FOR {user_name.upper()}:
        - Name: {user_profile.name or 'Not specified'}
        - Age: {user_profile.age or 'Not specified'}
        - Weight: {user_profile.weight or 'Not specified'} {user_profile.weight_unit or 'kg'}
        - Height: {user_profile.height or 'Not specified'}
        - Goals: {user_profile.goals or 'Not specified'}
        - Ailments: {user_profile.ailments or 'None specified'}
        - Dietary Preferences: {user_profile.dietary_preferences or 'Not specified'}
        - Exercise Routine: {user_profile.exercise_routine or 'Not specified'}
        - Daily Activities: {user_profile.daily_activities or 'Not specified'}
        - Sleep Schedule: {user_profile.sleep_schedule or 'Not specified'}
        - Spiritual/Religion: {user_profile.spiritual_religion or 'Not specified'}
        - Self Connection: {user_profile.self_connection or 'Not specified'}
        - Surroundings Connection: {user_profile.surroundings_connection or 'Not specified'}
        - Providing Others: {user_profile.providing_others or 'Not specified'}
        - Safe Groups: {user_profile.safe_groups or 'Not specified'}
        - Awe Things: {user_profile.awe_things or 'Not specified'}
        - Creative Expression: {user_profile.creative_expression or 'Not specified'}
        - Upsetting Situations: {user_profile.upsetting_situations or 'Not specified'}
        - Spirit Notes: {user_profile.spirit_notes or 'Not specified'}
        """
        
        # Calculate water intake statistics
        total_water_oz = sum(analysis_data['water_intake']) if analysis_data['water_intake'] else 0
        avg_water_oz = total_water_oz / len(analysis_data['water_intake']) if analysis_data['water_intake'] else 0
        dashboard_water_count = len(analysis_data['dashboard_water_entries'])
        dashboard_water_oz = sum([entry['amount'] for entry in analysis_data['dashboard_water_entries']])
        
        # Create prompt for OpenAI with comprehensive nutritional data
        prompt = f"""
        You are {user_name}'s personal wellness coach. Analyze their comprehensive nutritional journal data from the past {time_period} days and speak directly to them with personalized insights.
        
        {profile_context}
        
        {user_name}'s COMPREHENSIVE NUTRITIONAL JOURNAL DATA:
        - Total entries: {analysis_data['total_entries']}
        - Foods consumed: {len(analysis_data['foods'])} different items
        - Mood entries: {len(analysis_data['moods'])} entries
        - Water intake entries: {len(analysis_data['water_intake'])} entries
        
        CORE NUTRITIONAL TOTALS:
        - Total calories: {analysis_data['nutritional_totals']['calories']:.1f}
        - Total protein: {analysis_data['nutritional_totals']['protein']:.1f}g
        - Total carbs: {analysis_data['nutritional_totals']['carbs']:.1f}g
        - Total fat: {analysis_data['nutritional_totals']['fat']:.1f}g
        - Total fiber: {analysis_data['nutritional_totals']['fiber']:.1f}g
        - Total sugar: {analysis_data['nutritional_totals']['sugar']:.1f}g
        - Total sodium: {analysis_data['nutritional_totals']['sodium']:.1f}mg
        
        EXTENDED NUTRITIONAL TOTALS (for detailed analysis):
        - Saturated fat: {analysis_data['extended_nutritional_totals']['saturated_fat']:.1f}g
        - Trans fat: {analysis_data['extended_nutritional_totals']['trans_fat']:.1f}g
        - Cholesterol: {analysis_data['extended_nutritional_totals']['cholesterol']:.1f}mg
        - Potassium: {analysis_data['extended_nutritional_totals']['potassium']:.1f}mg
        - Calcium: {analysis_data['extended_nutritional_totals']['calcium']:.1f}mg
        - Iron: {analysis_data['extended_nutritional_totals']['iron']:.1f}mg
        - Vitamin A: {analysis_data['extended_nutritional_totals']['vitamin_a']:.1f}IU
        - Vitamin C: {analysis_data['extended_nutritional_totals']['vitamin_c']:.1f}mg
        - Vitamin D: {analysis_data['extended_nutritional_totals']['vitamin_d']:.1f}IU
        - Vitamin E: {analysis_data['extended_nutritional_totals']['vitamin_e']:.1f}mg
        - Vitamin K: {analysis_data['extended_nutritional_totals']['vitamin_k']:.1f}mcg
        - Vitamin B6: {analysis_data['extended_nutritional_totals']['vitamin_b6']:.1f}mg
        - Vitamin B12: {analysis_data['extended_nutritional_totals']['vitamin_b12']:.1f}mcg
        - Magnesium: {analysis_data['extended_nutritional_totals']['magnesium']:.1f}mg
        - Zinc: {analysis_data['extended_nutritional_totals']['zinc']:.1f}mg
        - Phosphorus: {analysis_data['extended_nutritional_totals']['phosphorus']:.1f}mg
        - Manganese: {analysis_data['extended_nutritional_totals']['manganese']:.1f}mg
        - Selenium: {analysis_data['extended_nutritional_totals']['selenium']:.1f}mcg
        - Copper: {analysis_data['extended_nutritional_totals']['copper']:.1f}mg
        - Thiamin (B1): {analysis_data['extended_nutritional_totals']['thiamin']:.1f}mg
        - Riboflavin (B2): {analysis_data['extended_nutritional_totals']['riboflavin']:.1f}mg
        - Niacin (B3): {analysis_data['extended_nutritional_totals']['niacin']:.1f}mg
        - Folate (B9): {analysis_data['extended_nutritional_totals']['folate']:.1f}mcg
        - Pantothenic Acid (B5): {analysis_data['extended_nutritional_totals']['pantothenic_acid']:.1f}mg
        - Biotin (B7): {analysis_data['extended_nutritional_totals']['biotin']:.1f}mcg
        - Choline: {analysis_data['extended_nutritional_totals']['choline']:.1f}mg
        - Betaine: {analysis_data['extended_nutritional_totals']['betaine']:.1f}mg
        - Taurine: {analysis_data['extended_nutritional_totals']['taurine']:.1f}mg
        - Caffeine: {analysis_data['extended_nutritional_totals']['caffeine']:.1f}mg
        - Alcohol: {analysis_data['extended_nutritional_totals']['alcohol']:.1f}g
        - Water content: {analysis_data['extended_nutritional_totals']['water_content']:.1f}g
        - Ash: {analysis_data['extended_nutritional_totals']['ash']:.1f}g
        
        DATA QUALITY ANALYSIS:
        - Entries with full nutritional data: {analysis_data['nutritional_insights']['data_quality']['entries_with_full_nutrition']}
        - Entries with basic nutritional data: {analysis_data['nutritional_insights']['data_quality']['entries_with_basic_nutrition']}
        - Entries with no nutritional data: {analysis_data['nutritional_insights']['data_quality']['entries_with_no_nutrition']}
        
        HYDRATION ANALYSIS:
        - Total water intake: {total_water_oz:.1f} oz
        - Average water per entry: {avg_water_oz:.1f} oz
        - Dashboard water entries: {dashboard_water_count} (total: {dashboard_water_oz} oz)
        - Other water sources: {len(analysis_data['water_entries']) - dashboard_water_count} entries
        - Water entry details: {analysis_data['water_entries']}
        
        DETAILED FOOD DATA (with comprehensive nutritional profiles):
        - Foods: {analysis_data['foods']}
        - Moods: {analysis_data['moods']}
        - Water intake (oz): {analysis_data['water_intake']}
        - Meal times: {analysis_data['meal_times']}
        
        Speak directly to {user_name} and provide TWO separate responses in HTML format:
        
        1. PATTERNS ANALYSIS (separated into Mind, Body, and Spirit sections with specific data insights):
        - Analyze {user_name}'s specific data patterns and provide concrete insights
        - Reference exact numbers, percentages, and trends from their journal data
        - Connect patterns to their specific profile goals and lifestyle
        - Include specific data points like calorie ranges, mood frequencies, water intake patterns
        - Identify correlations between different data points (e.g., mood and food choices)
        - Analyze micronutrient patterns and potential deficiencies using the extended nutritional data
        - Consider vitamin and mineral intake patterns for comprehensive health insights
        - Evaluate data quality and completeness of nutritional information
        
        2. ACTIONABLE SUGGESTIONS (with tailored links based on profile goals):
        - Provide 3-4 specific, actionable recommendations based on their data patterns
        - Include relevant links to resources that align with their profile goals
        - Suggest specific foods, exercises, or practices based on their dietary preferences and exercise routine
        - Recommend tools, apps, or resources that fit their lifestyle and goals
        - Focus on immediate, implementable actions they can take today
        
        Format your response exactly like this:
        PATTERNS:
        <div class="patterns-analysis">
            <div class="mind-section">
                <h3><span class="section-icon">🧠</span> Mind</h3>
                <div class="section-content">
                    [Analyze {user_name}'s mental patterns with specific data: mood distribution (e.g., "You logged 3 happy moods vs 1 stressed"), stress indicators, emotional eating patterns, and cognitive wellness. Reference exact mood entries and their timing.]
                </div>
            </div>
            
            <div class="body-section">
                <h3><span class="section-icon">💪</span> Body</h3>
                <div class="section-content">
                    [Analyze {user_name}'s physical patterns with specific data: calorie ranges (e.g., "Your daily average is 1,200-1,800 calories"), macronutrient ratios, hydration consistency, and energy patterns. Reference exact nutritional data and water intake patterns. Include micronutrient analysis using the comprehensive vitamin and mineral data, identifying potential deficiencies or excesses in vitamins A, C, D, E, K, B-complex, calcium, iron, magnesium, zinc, and other essential nutrients. Consider the quality of nutritional data available.]
                </div>
            </div>
            
            <div class="spirit-section">
                <h3><span class="section-icon">✨</span> Spirit</h3>
                <div class="section-content">
                    [Analyze {user_name}'s spiritual patterns with specific data: mindfulness indicators, life balance metrics, spiritual practice consistency, and overall wellness alignment. Reference their spiritual profile data and life satisfaction indicators.]
                </div>
            </div>
        </div>
        
        SUGGESTIONS:
        <div class="suggestions-content">
        <ul>
        <li><span class="highlight">[Specific Category]:</span> [Actionable suggestion with specific details] <a href="[relevant resource link]" target="_blank" class="suggestion-link">[Resource Name]</a></li>
        <li><span class="highlight">[Specific Category]:</span> [Actionable suggestion with specific details] <a href="[relevant resource link]" target="_blank" class="suggestion-link">[Resource Name]</a></li>
        <li><span class="highlight">[Specific Category]:</span> [Actionable suggestion with specific details] <a href="[relevant resource link]" target="_blank" class="suggestion-link">[Resource Name]</a></li>
        <li><span class="highlight">[Specific Category]:</span> [Actionable suggestion with specific details] <a href="[relevant resource link]" target="_blank" class="suggestion-link">[Resource Name]</a></li>
        </ul>
        </div>
        
        For the patterns sections:
        - Include specific numbers and percentages from their data
        - Reference exact mood entries, calorie counts, and water intake
        - Identify patterns like "You tend to eat more when stressed" or "Your hydration peaks at 2pm"
        - Connect patterns to their specific goals (weight management, muscle building, stress reduction, etc.)
        - Use encouraging language while being data-driven
        
        For the suggestions:
        - Include specific resource links (apps, websites, tools) relevant to their goals
        - Suggest exact foods, exercises, or practices based on their profile
        - Provide immediate, actionable steps they can take today
        - Tailor recommendations to their dietary preferences, exercise routine, and spiritual practices
        
        Use HTML tags like <strong>, <em>, <span class="highlight">, etc. to make the content visually appealing. Speak directly to {user_name} using "you" and "your" throughout. Keep it encouraging, practical, and specifically tailored to {user_name}'s unique situation. Make it feel like a personal conversation with their wellness coach.
        """
        
        # Get current token limits from system settings
        max_input_tokens = get_max_input_tokens()
        max_output_tokens = get_max_output_tokens()
        max_total_tokens = get_max_total_tokens()
        
        # Calculate estimated input tokens (rough approximation)
        estimated_input_tokens = len(prompt) + len(f"You are {user_name}'s personal wellness coach. Speak directly to them using their name and 'you'/'your' throughout. Be encouraging, supportive, and provide actionable insights tailored specifically to their unique situation. Make it feel like a personal conversation.") + 100  # Buffer for system overhead
        
        # Ensure we don't exceed total token limit
        if estimated_input_tokens > max_total_tokens:
            # Truncate prompt if necessary
            max_prompt_length = max_total_tokens - 200  # Leave room for system message
            prompt = prompt[:max_prompt_length] + "..."
            estimated_input_tokens = max_prompt_length + 200
        
        # Calculate max output tokens based on remaining budget
        available_output_tokens = min(max_output_tokens, max_total_tokens - estimated_input_tokens)
        
        # Call OpenAI API with flexible service tier configuration
        response = client.chat.completions.create(
            model=get_current_gpt_model(),
            messages=[
                {"role": "system", "content": f"You are {user_name}'s personal wellness coach. Speak directly to them using their name and 'you'/'your' throughout. Be encouraging, supportive, and provide actionable insights tailored specifically to their unique situation. Make it feel like a personal conversation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=available_output_tokens,
            temperature=0.7,
            # Flexible service tier options for better cost control
            presence_penalty=get_presence_penalty(),
            frequency_penalty=get_frequency_penalty(),
            top_p=get_top_p(),
            logprobs=None,  # Disable for cost savings
            top_logprobs=None  # Disable for cost savings
        )
        
        # Extract token usage information with error handling
        try:
            if hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'prompt_tokens', 0)
                output_tokens = getattr(response.usage, 'completion_tokens', 0)
                total_tokens = getattr(response.usage, 'total_tokens', 0)
            else:
                # Fallback if usage information is not available
                input_tokens = estimated_input_tokens
                output_tokens = len(full_response.split()) * 1.3  # Rough estimate
                total_tokens = input_tokens + output_tokens
                print(f"⚠️ OpenAI API usage info not available, using estimates: input={input_tokens}, output={output_tokens}")
        except Exception as e:
            print(f"⚠️ Error extracting token usage: {e}, using estimates")
            input_tokens = estimated_input_tokens
            output_tokens = len(full_response.split()) * 1.3  # Rough estimate
            total_tokens = input_tokens + output_tokens
        
        # Track token usage for analytics
        try:
            current_month = datetime.utcnow().strftime('%Y-%m')
            current_user = get_current_user()
            
            if not current_user:
                print("⚠️ No current user found for token tracking")
                return
            
            # Get or create token usage record for current month
            token_usage = TokenUsage.query.filter_by(
                user_id=current_user.id,
                month=current_month
            ).first()
            
            if not token_usage:
                token_usage = TokenUsage(
                    user_id=current_user.id,
                    month=current_month,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    model_used=get_current_gpt_model()
                )
                db.session.add(token_usage)
                print(f"📊 Created new token usage record for user {current_user.id} in {current_month}")
            
            # Update token counts
            token_usage.input_tokens += input_tokens
            token_usage.output_tokens += output_tokens
            token_usage.total_tokens += total_tokens
            
            # Calculate cost based on current model pricing
            api_costs = APICosts.query.filter_by(
                model_name=get_current_gpt_model(),
                is_active=True
            ).first()
            
            if api_costs:
                input_cost = (input_tokens / 1000000) * api_costs.input_cost_per_1m
                output_cost = (output_tokens / 1000000) * api_costs.output_cost_per_1m
                total_cost = input_cost + output_cost
                token_usage.cost_usd += total_cost
                print(f"💰 Token cost calculated: input=${input_cost:.6f}, output=${output_cost:.6f}, total=${total_cost:.6f}")
            else:
                print(f"⚠️ No API costs found for model {get_current_gpt_model()}")
            
            db.session.commit()
            print(f"✅ Token usage tracked: input={input_tokens}, output={output_tokens}, total={total_tokens}")
            
            # Record AI usage session for subscription/credit tracking
            try:
                if current_user:
                    record_ai_session(
                        user_id=current_user.id,
                        session_type='patterns_analysis',
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        cost_usd=total_cost if 'total_cost' in locals() else 0.0,
                        model_used=get_current_gpt_model()
                    )
                    print(f"✅ AI session recorded for user {current_user.id}")
            except Exception as e:
                print(f"⚠️ Error recording AI session: {e}")
            
        except Exception as e:
            # Log error but don't fail the main function
            print(f"❌ Error tracking token usage: {e}")
            if 'db' in locals() and hasattr(db, 'session'):
                db.session.rollback()
        
        # Parse the response to separate patterns and suggestions
        full_response = response.choices[0].message.content
        analysis = ""
        suggestions = ""
        
        # Split the response into patterns and suggestions
        if "PATTERNS:" in full_response and "SUGGESTIONS:" in full_response:
            parts = full_response.split("SUGGESTIONS:")
            if len(parts) == 2:
                analysis = parts[0].replace("PATTERNS:", "").strip()
                suggestions = parts[1].strip()
        else:
            # Fallback if format is not as expected
            analysis = f'<div class="patterns-analysis"><div class="mind-section"><h3><span class="section-icon">🧠</span> Mind Patterns</h3><div class="section-content"><p>{full_response}</p></div></div></div>'
            suggestions = '<div class="suggestions-content"><p>No specific suggestions available at this time.</p></div>'
        
        # Get current timestamp for creation date
        current_time = datetime.utcnow()
        
        return {
            'success': True,
            'analysis': analysis,
            'suggestions': suggestions,
            'created_at': current_time.isoformat(),
            'summary': {
                'total_entries': analysis_data['total_entries'],
                'total_calories': analysis_data['nutritional_totals']['calories'],
                'total_protein': analysis_data['nutritional_totals']['protein'],
                'total_carbs': analysis_data['nutritional_totals']['carbs'],
                'total_fat': analysis_data['nutritional_totals']['fat'],
                'avg_water': sum(analysis_data['water_intake']) / len(analysis_data['water_intake']) if analysis_data['water_intake'] else 0
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Error analyzing patterns: {str(e)}"
        }

@app.route('/dashboard/patterns')
@login_required
def get_patterns_analysis():
    """Get patterns analysis for the past 7 and 30 days with caching"""
    try:
        # Get user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # Check if user has any food entries
        food_entries_count = FoodJournal.query.filter_by(user_id=user_profile.id).count()
        mood_entries_count = MoodEntry.query.filter_by(user_id=user_profile.id).count()
        
        # If user has no data, return call-to-action
        if food_entries_count == 0 and mood_entries_count == 0:
            return jsonify({
                'success': True,
                'is_new_user': True,
                'message': 'Welcome to KI Wellness! Start tracking your wellness journey to get personalized AI analysis.',
                'call_to_action': {
                    'title': 'Get Started with Wellness Tracking',
                    'description': 'Add your first food entry or update your profile to receive personalized AI insights.',
                    'actions': [
                        {
                            'text': 'Add Food Entry',
                            'url': '/food-journal',
                            'icon': '🍽️',
                            'description': 'Log your meals and snacks'
                        },
                        {
                            'text': 'Update Profile',
                            'url': '/profile',
                            'icon': '👤',
                            'description': 'Share your wellness goals and preferences'
                        }
                    ]
                }
            })
        
        # Check if user has very little data (less than 3 entries)
        total_entries = food_entries_count + mood_entries_count
        if total_entries < 3:
            return jsonify({
                'success': True,
                'is_new_user': False,
                'needs_more_data': True,
                'message': 'Great start! Add more entries to get better AI analysis.',
                'call_to_action': {
                    'title': 'Keep Building Your Wellness Profile',
                    'description': f'You have {total_entries} entries. Add more food and mood entries for personalized insights.',
                    'actions': [
                        {
                            'text': 'Add More Food',
                            'url': '/food-journal',
                            'icon': '🍽️',
                            'description': 'Log more meals and snacks'
                        },
                        {
                            'text': 'Track Your Mood',
                            'url': '/dashboard',
                            'icon': '😊',
                            'description': 'Record how you\'re feeling'
                        }
                    ]
                }
            })
        
        # Check if we need to update cached results (use timezone-aware date)
        today = datetime.utcnow().date()
        current_weekday = today.weekday()  # Monday = 0
        
        # Calculate the last Monday
        days_since_monday = current_weekday
        last_monday = today - timedelta(days=days_since_monday)
        
        # Check 7-day cache (update if no analysis since last Monday)
        seven_day_cache = PatternsCache.query.filter_by(
            user_id=user_profile.id, 
            period_type='7day'
        ).first()
        
        should_update_7day = True
        if seven_day_cache:
            last_updated = seven_day_cache.last_updated.date()
            # Check if analysis was run since last Monday
            should_update_7day = last_updated < last_monday
        
        # Calculate date ranges
        seven_days_ago = today - timedelta(days=7)
        
        # Process 7-day analysis
        seven_day_result = None
        if should_update_7day:
            # Get food journal entries for past 7 days
            seven_day_entries = FoodJournal.query.filter(
                FoodJournal.user_id == user_profile.id,
                FoodJournal.consumed_at >= seven_days_ago
            ).order_by(FoodJournal.consumed_at.desc()).all()
            
            # Get mood entries for past 7 days
            seven_day_mood_entries = MoodEntry.query.filter(
                MoodEntry.user_id == user_profile.id,
                MoodEntry.logged_at >= seven_days_ago
            ).order_by(MoodEntry.logged_at.desc()).all()
            
            # Convert to JSON for analysis
            seven_day_data = []
            for entry in seven_day_entries:
                seven_day_data.append({
                    'food_name': entry.food_name,
                    'serving_size': entry.serving_size,
                    'serving_unit': entry.serving_unit,
                    'calories': entry.calories,
                    'protein': entry.protein,
                    'carbs': entry.carbs,
                    'fat': entry.fat,
                    'time_of_day': entry.time_of_day,
                    'water_amount': entry.water_amount,
                    'water_unit': entry.water_unit,
                    'mood': entry.mood,
                    'notes': entry.notes,
                    'consumed_at': entry.consumed_at.isoformat()
                })
            
            # Add mood entries as special entries
            for mood_entry in seven_day_mood_entries:
                seven_day_data.append({
                    'food_name': 'Mood Entry',
                    'serving_size': 1,
                    'serving_unit': 'entry',
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'time_of_day': 'mood',
                    'water_amount': 0,
                    'water_unit': 'oz',
                    'mood': mood_entry.mood,
                    'notes': mood_entry.notes,
                    'consumed_at': mood_entry.logged_at.isoformat()
                })
            
            # Analyze patterns
            seven_day_result = analyze_patterns_with_openai(seven_day_data, "7", user_profile)
            
            # Cache the result
            if seven_day_result['success']:
                # Get browser timezone from request if available
                browser_timezone = request.args.get('browser_timezone')
                
                # Store the analysis time in UTC but also store the timezone info
                if browser_timezone:
                    # Get current time in browser timezone
                    now = datetime.utcnow()
                    browser_tz = pytz.timezone(browser_timezone)
                    utc_tz = pytz.UTC
                    utc_now = utc_tz.localize(now)
                    browser_now = utc_now.astimezone(browser_tz)
                    # Store the browser timezone info in the summary
                    seven_day_result['summary']['browser_timezone'] = browser_timezone
                    seven_day_result['summary']['analysis_time_browser'] = browser_now.isoformat()
                    analysis_time = datetime.utcnow()  # Store UTC in database
                else:
                    analysis_time = datetime.utcnow()
                
                if seven_day_cache:
                    seven_day_cache.analysis = seven_day_result['analysis']
                    seven_day_cache.suggestions = seven_day_result['suggestions']
                    seven_day_cache.summary = seven_day_result['summary']
                    seven_day_cache.last_updated = analysis_time
                else:
                    new_cache = PatternsCache(
                        user_id=user_profile.id,
                        period_type='7day',
                        analysis=seven_day_result['analysis'],
                        suggestions=seven_day_result['suggestions'],
                        summary=seven_day_result['summary'],
                        last_updated=analysis_time
                    )
                    db.session.add(new_cache)
                db.session.commit()
        else:
            # Use cached result
            seven_day_result = {
                'success': True,
                'analysis': seven_day_cache.analysis,
                'suggestions': seven_day_cache.suggestions,
                'summary': seven_day_cache.summary,
                'last_updated': seven_day_cache.last_updated.isoformat()
            }
        
        return jsonify({
            'success': True,
            'seven_day': seven_day_result,
            'cache_info': {
                'seven_day_updated': not should_update_7day
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard/patterns/refresh', methods=['POST'])
@login_required
def refresh_patterns_analysis():
    """Force refresh of patterns analysis by clearing cache"""
    try:
        # Get user profile
        user_profile = UserProfile.query.first()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # Clear existing cache
        PatternsCache.query.filter_by(user_id=user_profile.id).delete()
        db.session.commit()
        
        # Redirect to the main patterns endpoint
        return jsonify({'success': True, 'message': 'Cache cleared, analysis will be regenerated'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard/water/add', methods=['POST'])
@login_required
def add_water_intake():
    """Add 8 oz of water intake for the current day"""
    try:
        # Get current user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # Get browser timezone if provided
        data = request.get_json() or {}
        browser_timezone = data.get('browser_timezone')
        consumed_at = get_browser_timezone_datetime(browser_timezone) if browser_timezone else datetime.utcnow()
        
        # Create a water intake entry
        water_entry = FoodJournal(
            user_id=user_profile.id,
            food_name='Water Intake',
            serving_size=8.0,
            serving_unit='oz',
            calories=0,
            protein=0,
            carbs=0,
            fat=0,
            water_amount=8.0,
            water_unit='oz',
            mood='😊 Hydrated',
            notes='Quick water intake from dashboard',
            consumed_at=consumed_at
        )
        
        db.session.add(water_entry)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '8 oz of water added successfully',
            'water_amount': 8.0
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard/mood/add', methods=['POST'])
@login_required
def add_mood_entry():
    """Add a quick mood entry for the current day"""
    try:
        # Get current user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # Get request data
        data = request.get_json() or {}
        mood = data.get('mood', '😊 Good')
        notes = data.get('notes', 'Quick mood entry from dashboard')
        browser_timezone = data.get('browser_timezone')
        logged_at = get_browser_timezone_datetime(browser_timezone) if browser_timezone else datetime.utcnow()
        
        # Create a mood entry
        mood_entry = MoodEntry(
            user_id=user_profile.id,
            mood=mood,
            notes=notes,
            logged_at=logged_at
        )
        
        db.session.add(mood_entry)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Mood "{mood}" added successfully',
            'mood': mood
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard/mood/entries')
@login_required
def get_mood_entries():
    """
    SECURITY: Get mood entries for current user only
    - Filters by user_id to ensure data isolation
    - Only authenticated users can access their own mood data
    """
    try:
        # Get current user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # SECURITY: Verify user has access to their data
        verify_user_data_access(user_profile, "mood_entries")
        
        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date and end_date:
            # Parse date range
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
            
            entries = MoodEntry.query.filter(
                MoodEntry.user_id == user_profile.id,
                MoodEntry.logged_at >= start_datetime,
                MoodEntry.logged_at < end_datetime
            ).order_by(MoodEntry.logged_at.desc()).all()
        else:
            # Default to today if no date range provided
            today = datetime.utcnow().date()
            start_datetime = datetime.combine(today, datetime.min.time())
            end_datetime = datetime.combine(today, datetime.max.time())
            
            entries = MoodEntry.query.filter(
                MoodEntry.user_id == user_profile.id,
                MoodEntry.logged_at >= start_datetime,
                MoodEntry.logged_at < end_datetime
            ).order_by(MoodEntry.logged_at.desc()).all()
        
        entries_data = []
        for entry in entries:
            entries_data.append({
                'id': entry.id,
                'mood': entry.mood,
                'notes': entry.notes,
                'logged_at': entry.logged_at.isoformat()
            })
        
        return jsonify({'success': True, 'entries': entries_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/avatars/<filename>')
def serve_avatar(filename):
    return app.send_static_file(f'public/avatars/{filename}')

def verify_recaptcha(response, action='submit'):
    """
    Verify Google reCAPTCHA v2 checkbox response with enhanced error handling and logging
    """
    # Check if running on localhost
    is_localhost = False
    if request:
        is_localhost = request.host in ['127.0.0.1:5001', 'localhost:5001', '0.0.0.0:5001']
    
    # If reCAPTCHA is disabled or running on localhost, return True
    if not app.config.get('RECAPTCHA_ENABLED', True) or is_localhost:
        if is_localhost:
            print("🔧 Localhost detected: Bypassing reCAPTCHA verification")
        else:
            print("🔧 reCAPTCHA disabled in configuration")
        return True
    
    # If no response provided, log and return False
    if not response:
        print("❌ reCAPTCHA verification failed: No response provided")
        return False
    
    # Log the response for debugging (truncated for security)
    response_preview = response[:20] + "..." if len(response) > 20 else response
    print(f"🔍 reCAPTCHA verification: Processing response: {response_preview}")
    
    try:
        # Make a request to Google's reCAPTCHA verification endpoint
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        data = {
            'secret': app.config['RECAPTCHA_SECRET_KEY'],
            'response': response,
            'remoteip': request.remote_addr if request else None
        }
        
        print(f"🔍 reCAPTCHA verification: Sending request to {verify_url}")
        print(f"🔍 reCAPTCHA verification: Secret key present: {bool(app.config.get('RECAPTCHA_SECRET_KEY'))}")
        print(f"🔍 reCAPTCHA verification: Action: {action}")
        
        result = requests.post(verify_url, data=data, timeout=10)
        print(f"🔍 reCAPTCHA verification: HTTP response status: {result.status_code}")
        
        if result.status_code != 200:
            print(f"❌ reCAPTCHA verification failed: HTTP {result.status_code}")
            return False
        
        result_json = result.json()
        print(f"🔍 reCAPTCHA verification: Response JSON: {result_json}")
        
        # Check if the verification was successful
        success = result_json.get('success', False)
        if success:
            print(f"✅ reCAPTCHA verification successful")
            return True
        else:
            error_codes = result_json.get('error-codes', ['Unknown error'])
            print(f"❌ reCAPTCHA verification failed: {error_codes}")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ reCAPTCHA verification failed: Request timeout")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ reCAPTCHA verification failed: Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ reCAPTCHA verification failed: Unexpected error: {e}")
        # In development, if there's an error, allow the request to proceed
        if app.config.get('DEBUG', False):
            print("🔧 Development mode: Allowing request to proceed despite error")
            return True
        return False


def check_honeypot(data):
    """
    Check if honeypot field was filled (indicates bot)
    """
    # Check for honeypot field (should be empty if human)
    honeypot_fields = ['website', 'phone_number', 'company', 'subject']
    
    for field in honeypot_fields:
        if data.get(field) and data.get(field).strip():
            print(f"🚫 Bot detected: Honeypot field '{field}' was filled")
            return False
    
    return True

# Reminder Management Routes
@app.route('/reminders')
@login_required
def reminders():
    user_id = session.get('user_id')
    user_reminders = Reminder.query.filter_by(user_id=user_id, is_active=True).order_by(Reminder.next_trigger).all()
    return render_template('reminders.html', reminders=user_reminders)

@app.route('/api/reminders', methods=['GET'])
@login_required
def get_reminders():
    user_id = session.get('user_id')
    reminders = Reminder.query.filter_by(user_id=user_id, is_active=True).all()
    
    reminder_list = []
    for reminder in reminders:
        reminder_data = {
            'id': reminder.id,
            'title': reminder.title,
            'description': reminder.description,
            'type': reminder.reminder_type,
            'frequency': reminder.frequency,
            'time_of_day': reminder.time_of_day.strftime('%H:%M') if reminder.time_of_day else None,
            'days_of_week': json.loads(reminder.days_of_week) if reminder.days_of_week else [],
            'is_active': reminder.is_active,
            'next_trigger': reminder.next_trigger.isoformat() if reminder.next_trigger else None
        }
        reminder_list.append(reminder_data)
    
    return jsonify(reminder_list)

@app.route('/api/reminders', methods=['POST'])
@login_required
def create_reminder():
    user_id = session.get('user_id')
    data = request.get_json()
    
    try:
        # Parse time
        time_parts = data['time_of_day'].split(':')
        time_of_day = time(int(time_parts[0]), int(time_parts[1]))
        
        # Handle days of week
        days_of_week = json.dumps(data.get('days_of_week', [])) if data.get('days_of_week') else None
        
        # Calculate next trigger
        next_trigger = calculate_next_trigger(
            time_of_day, 
            data['frequency'], 
            data.get('days_of_week', [])
        )
        
        reminder = Reminder(
            user_id=user_id,
            title=data['title'],
            description=data.get('description', ''),
            reminder_type=data['type'],
            frequency=data['frequency'],
            time_of_day=time_of_day,
            days_of_week=days_of_week,
            next_trigger=next_trigger
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({'success': True, 'id': reminder.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/reminders/<int:reminder_id>', methods=['PUT'])
@login_required
def update_reminder(reminder_id):
    user_id = session.get('user_id')
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    
    if not reminder:
        return jsonify({'success': False, 'error': 'Reminder not found'}), 404
    
    try:
        data = request.get_json()
        
        if 'title' in data:
            reminder.title = data['title']
        if 'description' in data:
            reminder.description = data['description']
        if 'time_of_day' in data:
            time_parts = data['time_of_day'].split(':')
            reminder.time_of_day = time(int(time_parts[0]), int(time_parts[1]))
        if 'frequency' in data:
            reminder.frequency = data['frequency']
        if 'days_of_week' in data:
            reminder.days_of_week = json.dumps(data['days_of_week']) if data['days_of_week'] else None
        if 'is_active' in data:
            reminder.is_active = data['is_active']
        
        # Recalculate next trigger
        reminder.next_trigger = calculate_next_trigger(
            reminder.time_of_day,
            reminder.frequency,
            json.loads(reminder.days_of_week) if reminder.days_of_week else []
        )
        
        reminder.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
@login_required
def delete_reminder(reminder_id):
    user_id = session.get('user_id')
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    
    if not reminder:
        return jsonify({'success': False, 'error': 'Reminder not found'}), 404
    
    try:
        db.session.delete(reminder)
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/reminders/<int:reminder_id>/trigger', methods=['POST'])
@login_required
def trigger_reminder(reminder_id):
    user_id = session.get('user_id')
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    
    if not reminder:
        return jsonify({'success': False, 'error': 'Reminder not found'}), 404
    
    try:
        data = request.get_json()
        action = data.get('action', 'completed')
        
        # Log the reminder trigger
        log = ReminderLog(
            reminder_id=reminder.id,
            user_id=user_id,
            action_taken=action,
            response_time=data.get('response_time')
        )
        db.session.add(log)
        
        # Update reminder
        reminder.last_triggered = datetime.utcnow()
        reminder.next_trigger = calculate_next_trigger(
            reminder.time_of_day,
            reminder.frequency,
            json.loads(reminder.days_of_week) if reminder.days_of_week else []
        )
        
        db.session.commit()
        
        return jsonify({'success': True, 'next_trigger': reminder.next_trigger.isoformat()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/notification-preferences', methods=['GET'])
@login_required
def get_notification_preferences():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'preferences': {
            'email_notifications': user.email_notifications,
            'sms_notifications': user.sms_notifications,
            'push_notifications': user.push_notifications
        }
    })

@app.route('/api/notification-preferences', methods=['PUT'])
@login_required
def update_notification_preferences():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    try:
        data = request.get_json()
        
        if 'email_notifications' in data:
            user.email_notifications = data['email_notifications']
        if 'sms_notifications' in data:
            user.sms_notifications = data['sms_notifications']
        if 'push_notifications' in data:
            user.push_notifications = data['push_notifications']
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/reminders/check', methods=['POST'])
@login_required
def check_reminders():
    """Check for due reminders and send notifications"""
    user_id = session.get('user_id')
    
    try:
        # Get all active reminders for the user
        reminders = Reminder.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).filter(
            Reminder.next_trigger <= datetime.utcnow()
        ).all()
        
        triggered_count = 0
        
        for reminder in reminders:
            # Send notifications
            if send_reminder_notifications(reminder):
                triggered_count += 1
                
                # Update reminder
                reminder.last_triggered = datetime.utcnow()
                reminder.next_trigger = calculate_next_trigger(
                    reminder.time_of_day,
                    reminder.frequency,
                    json.loads(reminder.days_of_week) if reminder.days_of_week else []
                )
        
        if triggered_count > 0:
            db.session.commit()
        
        return jsonify({
            'success': True, 
            'triggered_count': triggered_count,
            'message': f'Processed {triggered_count} reminders'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/reminders/export-calendar', methods=['POST'])
@login_required
def export_reminders_to_calendar():
    """Export reminders to calendar format (ICS)"""
    user_id = session.get('user_id')
    data = request.get_json()
    reminder_ids = data.get('reminder_ids', [])
    
    try:
        if not reminder_ids:
            reminders = Reminder.query.filter_by(user_id=user_id, is_active=True).all()
        else:
            reminders = Reminder.query.filter(
                Reminder.id.in_(reminder_ids),
                Reminder.user_id == user_id
            ).all()
        
        # Generate ICS content
        ics_content = generate_ics_calendar(reminders)
        
        # Return as downloadable file
        response = make_response(ics_content)
        response.headers['Content-Type'] = 'text/calendar'
        response.headers['Content-Disposition'] = 'attachment; filename=ki_wellness_reminders.ics'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def generate_ics_calendar(reminders):
    """Generate ICS calendar content for reminders"""
    ics_content = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Ki Wellness//Reminders//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH'
    ]
    
    for reminder in reminders:
        # Calculate next few occurrences
        occurrences = calculate_reminder_occurrences(reminder, count=10)
        
        for i, occurrence in enumerate(occurrences):
            event_id = f"reminder_{reminder.id}_{i}"
            start_time = occurrence.strftime('%Y%m%dT%H%M%SZ')
            end_time = (occurrence + timedelta(minutes=15)).strftime('%Y%m%dT%H%M%SZ')
            
            ics_content.extend([
                'BEGIN:VEVENT',
                f'UID:{event_id}',
                f'DTSTART:{start_time}',
                f'DTEND:{end_time}',
                f'SUMMARY:{reminder.title}',
                f'DESCRIPTION:{reminder.description or "Wellness reminder"}',
                f'CATEGORIES:{reminder.reminder_type}',
                'END:VEVENT'
            ])
    
    ics_content.append('END:VCALENDAR')
    return '\r\n'.join(ics_content)

def calculate_reminder_occurrences(reminder, count=10):
    """Calculate next N occurrences of a reminder"""
    occurrences = []
    current_time = datetime.utcnow()
    
    for i in range(count):
        if i == 0:
            # First occurrence
            occurrence = calculate_next_trigger(
                reminder.time_of_day,
                reminder.frequency,
                json.loads(reminder.days_of_week) if reminder.days_of_week else []
            )
        else:
            # Subsequent occurrences
            if reminder.frequency == 'daily':
                occurrence = occurrence + timedelta(days=1)
            elif reminder.frequency == 'hourly':
                occurrence = occurrence + timedelta(hours=1)
            elif reminder.frequency == 'custom':
                # Find next occurrence in custom schedule
                occurrence = calculate_next_trigger(
                    reminder.time_of_day,
                    reminder.frequency,
                    json.loads(reminder.days_of_week) if reminder.days_of_week else []
                )
                # Move forward by weeks
                occurrence += timedelta(weeks=i)
        
        occurrences.append(occurrence)
    
    return occurrences

# Notification Configuration
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'smtp_username': os.getenv('SMTP_USERNAME', ''),
    'smtp_password': os.getenv('SMTP_PASSWORD', ''),
    'from_email': os.getenv('FROM_EMAIL', 'noreply@kiwellness.org')
}

SMS_CONFIG = {
    'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID', ''),
    'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN', ''),
    'twilio_phone_number': os.getenv('TWILIO_PHONE_NUMBER', '')
}

# Notification Functions
def send_email_notification(user_email, subject, message):
    """Send email notification"""
    try:
        if not EMAIL_CONFIG['smtp_username'] or not EMAIL_CONFIG['smtp_password']:
            print("⚠️ Email configuration not set up")
            return False
            
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['from_email']
        msg['To'] = user_email
        msg['Subject'] = subject
        
        body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #10B981, #059669); padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Ki Wellness</h1>
                </div>
                <div style="padding: 20px; background-color: #f9fafb;">
                    {message}
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 12px;">
                        This is an automated reminder from Ki Wellness. 
                        You can manage your notification preferences in your profile settings.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['smtp_username'], EMAIL_CONFIG['smtp_password'])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['from_email'], user_email, text)
        server.quit()
        
        print(f"✅ Email sent to {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

def send_sms_notification(phone_number, message):
    """Send SMS notification using Twilio"""
    try:
        if not SMS_CONFIG['twilio_account_sid'] or not SMS_CONFIG['twilio_auth_token']:
            print("⚠️ SMS configuration not set up")
            return False
            
        url = f"https://api.twilio.com/2010-04-01/Accounts/{SMS_CONFIG['twilio_account_sid']}/Messages.json"
        
        data = {
            'From': SMS_CONFIG['twilio_phone_number'],
            'To': phone_number,
            'Body': message
        }
        
        response = requests.post(
            url,
            data=data,
            auth=(SMS_CONFIG['twilio_account_sid'], SMS_CONFIG['twilio_auth_token'])
        )
        
        if response.status_code == 201:
            print(f"✅ SMS sent to {phone_number}")
            return True
        else:
            print(f"❌ SMS sending failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SMS sending failed: {e}")
        return False

def send_push_notification(user_id, title, message):
    """Send push notification (placeholder for future implementation)"""
    try:
        # This would integrate with a push notification service like Firebase
        # For now, we'll just log it
        print(f"📱 Push notification for user {user_id}: {title} - {message}")
        return True
    except Exception as e:
        print(f"❌ Push notification failed: {e}")
        return False

def send_reminder_notifications(reminder):
    """Send notifications for a reminder based on user preferences"""
    try:
        user = User.query.get(reminder.user_id)
        if not user:
            return False
            
        # Create notification record
        notification = Notification(
            user_id=user.id,
            reminder_id=reminder.id,
            notification_type='email',  # Will be updated based on what's sent
            title=reminder.title,
            message=reminder.description or f"Time for your {reminder.reminder_type} reminder!"
        )
        
        success = False
        
        # Send email notification if enabled
        if user.email_notifications and user.email:
            if send_email_notification(user.email, reminder.title, 
                                    f"<h2>{reminder.title}</h2><p>{reminder.description or 'Time for your wellness reminder!'}</p>"):
                notification.notification_type = 'email'
                notification.status = 'sent'
                notification.sent_at = datetime.utcnow()
                success = True
        
        # Send SMS notification if enabled
        if user.sms_notifications and user.phone:
            sms_message = f"Ki Wellness: {reminder.title}\n{reminder.description or 'Time for your wellness reminder!'}"
            if send_sms_notification(user.phone, sms_message):
                # Create separate notification record for SMS
                sms_notification = Notification(
                    user_id=user.id,
                    reminder_id=reminder.id,
                    notification_type='sms',
                    title=reminder.title,
                    message=sms_message,
                    status='sent',
                    sent_at=datetime.utcnow()
                )
                db.session.add(sms_notification)
                success = True
        
        # Send push notification if enabled
        if user.push_notifications:
            if send_push_notification(user.id, reminder.title, 
                                   reminder.description or f"Time for your {reminder.reminder_type} reminder!"):
                # Create separate notification record for push
                push_notification = Notification(
                    user_id=user.id,
                    reminder_id=reminder.id,
                    notification_type='push',
                    title=reminder.title,
                    message=reminder.description or f"Time for your {reminder.reminder_type} reminder!",
                    status='sent',
                    sent_at=datetime.utcnow()
                )
                db.session.add(push_notification)
                success = True
        
        # Save notification records
        if success:
            db.session.add(notification)
            db.session.commit()
        
        return success
        
    except Exception as e:
        print(f"❌ Error sending reminder notifications: {e}")
        db.session.rollback()
        return False

# Helper function to calculate next trigger time
def calculate_next_trigger(time_of_day, frequency, days_of_week=None):
    now = datetime.utcnow()
    today = now.date()
    
    if frequency == 'daily':
        # Set to today at the specified time
        next_trigger = datetime.combine(today, time_of_day)
        # If time has passed today, set to tomorrow
        if next_trigger <= now:
            next_trigger += timedelta(days=1)
        return next_trigger
    
    elif frequency == 'hourly':
        # Set to next hour at the specified minute
        next_trigger = now.replace(minute=time_of_day.minute, second=0, microsecond=0)
        if next_trigger <= now:
            next_trigger += timedelta(hours=1)
        return next_trigger
    
    elif frequency == 'custom' and days_of_week:
        # Find next occurrence on specified days
        current_weekday = now.weekday()
        days_ahead = 0
        
        for i in range(7):
            check_day = (current_weekday + i) % 7
            if check_day in days_of_week:
                days_ahead = i
                break
        
        next_trigger = datetime.combine(today + timedelta(days=days_ahead), time_of_day)
        if next_trigger <= now:
            # Move to next week
            next_trigger += timedelta(days=7)
        return next_trigger
    
    # Default to daily
    next_trigger = datetime.combine(today, time_of_day)
    if next_trigger <= now:
        next_trigger += timedelta(days=1)
    return next_trigger

@app.route('/admin/users/<int:user_id>/suspend', methods=['POST'])
@admin_required
def suspend_user(user_id):
    """Suspend a user account"""
    try:
        user = User.query.get_or_404(user_id)
        if user.is_admin:
            return jsonify({'success': False, 'error': 'Cannot suspend admin users'})
        
        # Add suspended field if it doesn't exist (you may need to add this to your User model)
        # For now, we'll use a simple approach
        user.is_active = False  # Assuming you have an is_active field
        db.session.commit()
        return jsonify({'success': True, 'message': f'User {user.username} suspended successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error suspending user: {str(e)}'})


@app.route('/admin/users/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    """Activate a suspended user account"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = True  # Assuming you have an is_active field
        db.session.commit()
        return jsonify({'success': True, 'message': f'User {user.username} activated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error activating user: {str(e)}'})


@app.route('/admin/users/<int:user_id>/promote', methods=['POST'])
@admin_required
def promote_to_admin(user_id):
    """Promote a user to admin"""
    try:
        user = User.query.get_or_404(user_id)
        if user.is_admin:
            return jsonify({'success': False, 'error': 'User is already an admin'})
        
        user.is_admin = True
        db.session.commit()
        return jsonify({'success': True, 'message': f'User {user.username} promoted to admin successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error promoting user: {str(e)}'})


@app.route('/admin/users/<int:user_id>/demote', methods=['POST'])
@admin_required
def demote_admin(user_id):
    """Demote an admin to regular user"""
    try:
        user = User.query.get_or_404(user_id)
        if not user.is_admin:
            return jsonify({'success': False, 'error': 'User is not an admin'})
        
        # Prevent demoting the last admin
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            return jsonify({'success': False, 'error': 'Cannot demote the last admin user'})
        
        user.is_admin = False
        db.session.commit()
        return jsonify({'success': True, 'message': f'User {user.username} demoted from admin successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error demoting user: {str(e)}'})


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user account and all associated data"""
    try:
        user = User.query.get_or_404(user_id)
        if user.is_admin:
            return jsonify({'success': False, 'error': 'Cannot delete admin users'})
        
        # Delete associated data (cascade should handle most of this)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': f'User {user.username} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error deleting user: {str(e)}'})


@app.route('/admin/system/health')
@admin_required
def system_health():
    """Get system health information"""
    try:
        # Basic system health checks
        health_data = {
            'database': 'Connected',
            'timestamp': datetime.utcnow().isoformat(),
            'user_count': User.query.count(),
            'active_sessions': 0,  # Placeholder for session tracking
            'memory_usage': 'Normal',  # Placeholder for memory monitoring
            'disk_space': 'Adequate'  # Placeholder for disk monitoring
        }
        return jsonify(health_data)
    except Exception as e:
        return jsonify({'error': f'Error checking system health: {str(e)}'}), 500


@app.route('/admin/system/settings', methods=['GET', 'POST'])
@admin_required
def system_settings():
    """Manage system settings"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            setting_key = data.get('key')
            setting_value = data.get('value')
            description = data.get('description')
            
            if set_system_setting(setting_key, setting_value, description, get_current_user().id):
                return jsonify({'success': True, 'message': f'Setting {setting_key} updated successfully'})
            else:
                return jsonify({'success': False, 'error': 'Failed to update setting'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error updating setting: {str(e)}'})
    
    # GET request - return all settings
    try:
        settings = SystemSettings.query.all()
        settings_data = []
        for setting in settings:
            settings_data.append({
                'key': setting.key,
                'value': setting.value,
                'description': setting.description,
                'updated_at': setting.updated_at.isoformat() if setting.updated_at else None
            })
        return jsonify({'success': True, 'settings': settings_data})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error retrieving settings: {str(e)}'})


@app.route('/admin/system/emergency-stop', methods=['POST'])
@admin_required
def emergency_stop():
    """Emergency stop for OpenAI API"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'enable' or 'disable'
        
        if action == 'enable':
            set_system_setting('emergency_stop_active', 'true', 'Emergency stop activated', get_current_user().id)
            return jsonify({'success': True, 'message': 'Emergency stop ACTIVATED - OpenAI API calls are now disabled'})
        elif action == 'disable':
            set_system_setting('emergency_stop_active', 'false', 'Emergency stop deactivated', get_current_user().id)
            return jsonify({'success': True, 'message': 'Emergency stop DEACTIVATED - OpenAI API calls are now enabled'})
        else:
            return jsonify({'success': False, 'error': 'Invalid action. Use "enable" or "disable"'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error updating emergency stop: {str(e)}'})


@app.route('/admin/system/update-gpt-model', methods=['POST'])
@admin_required
def update_gpt_model():
    """Update the current GPT model being used"""
    try:
        data = request.get_json()
        new_model = data.get('model')
        
        if not new_model:
            return jsonify({'success': False, 'error': 'Model name is required'})
        
        # Update the system setting
        set_system_setting('current_gpt_model', new_model, f'GPT model updated to {new_model}', get_current_user().id if get_current_user() else None)
        
        return jsonify({'success': True, 'message': f'GPT model updated to {new_model}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error updating GPT model: {str(e)}'})


@app.route('/admin/system/update-token-limit', methods=['POST'])
@admin_required
def update_token_limit():
    """Update token usage limits"""
    try:
        data = request.get_json()
        limit_type = data.get('limit_type')
        new_value = data.get('new_value')
        
        if not limit_type or not new_value:
            return jsonify({'success': False, 'error': 'Limit type and new value are required'})
        
        # Validate the limit type
        valid_types = ['max_input_tokens', 'max_output_tokens', 'max_total_tokens']
        if limit_type not in valid_types:
            return jsonify({'success': False, 'error': 'Invalid limit type'})
        
        # Validate the new value
        if limit_type == 'max_input_tokens' and (new_value < 300 or new_value > 2000):
            return jsonify({'success': False, 'error': 'Input tokens must be between 300 and 2000'})
        elif limit_type == 'max_output_tokens' and (new_value < 300 or new_value > 1500):
            return jsonify({'success': False, 'error': 'Output tokens must be between 300 and 1500'})
        elif limit_type == 'max_total_tokens' and (new_value < 600 or new_value > 3500):
            return jsonify({'success': False, 'error': 'Total tokens must be between 600 and 3500'})
        
        # Update the system setting
        set_system_setting(limit_type, str(new_value), f'{limit_type.replace("_", " ").title()} updated to {new_value}', get_current_user().id if get_current_user() else None)
        
        return jsonify({'success': True, 'message': f'{limit_type.replace("_", " ").title()} updated to {new_value}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error updating token limit: {str(e)}'})


@app.route('/admin/system/toggle-account-creation', methods=['POST'])
@admin_required
def toggle_account_creation():
    """Toggle new account creation on/off"""
    try:
        current_status = are_new_accounts_enabled()
        new_status = not current_status
        
        if set_system_setting('new_accounts_enabled', str(new_status).lower(), 
                             f'Account creation {"enabled" if new_status else "disabled"} by admin', 
                             get_current_user().id):
            action = "enabled" if new_status else "disabled"
            return jsonify({
                'success': True, 
                'message': f'New account creation has been {action}',
                'new_status': new_status
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update setting'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error toggling account creation: {str(e)}'})


@app.route('/admin/system/update-flexible-tier', methods=['POST'])
@admin_required
def update_flexible_tier():
    """Update flexible service tier settings"""
    try:
        data = request.get_json()
        setting_type = data.get('setting_type')
        new_value = data.get('new_value')
        
        if not setting_type or new_value is None:
            return jsonify({'success': False, 'error': 'Setting type and new value are required'})
        
        # Validate the setting type
        valid_types = ['flexible_service_tier', 'presence_penalty', 'frequency_penalty', 'top_p']
        if setting_type not in valid_types:
            return jsonify({'success': False, 'error': 'Invalid setting type'})
        
        # Validate the new value based on type
        if setting_type == 'flexible_service_tier':
            if not isinstance(new_value, bool):
                return jsonify({'success': False, 'error': 'Flexible service tier must be true or false'})
        elif setting_type in ['presence_penalty', 'frequency_penalty']:
            if not isinstance(new_value, (int, float)) or new_value < -2.0 or new_value > 2.0:
                return jsonify({'success': False, 'error': 'Penalty values must be between -2.0 and 2.0'})
        elif setting_type == 'top_p':
            if not isinstance(new_value, (int, float)) or new_value < 0.0 or new_value > 1.0:
                return jsonify({'success': False, 'error': 'Top-p value must be between 0.0 and 1.0'})
        
        # Update the system setting
        set_system_setting(setting_type, str(new_value), f'{setting_type.replace("_", " ").title()} updated to {new_value}', get_current_user().id if get_current_user() else None)
        
        return jsonify({'success': True, 'message': f'{setting_type.replace("_", " ").title()} updated to {new_value}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error updating flexible tier setting: {str(e)}'})


@app.route('/admin/system/toggle-payment-testing', methods=['POST'])
@admin_required
def toggle_payment_testing():
    """Toggle payment testing mode (sandbox vs live)"""
    try:
        data = request.get_json()
        enable_testing = data.get('enable_testing', False)
        
        # Update the system setting
        set_system_setting(
            'payment_testing_mode', 
            str(enable_testing).lower(), 
            f'Payment testing mode {"enabled" if enable_testing else "disabled"}', 
            get_current_user().id if get_current_user() else None
        )
        
        # Reinitialize Stripe with new configuration
        global stripe_initialized
        stripe_initialized = initialize_stripe()
        
        return jsonify({
            'success': True, 
            'message': f'Payment testing mode {"enabled" if enable_testing else "disabled"}',
            'testing_mode': enable_testing
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error toggling payment testing mode: {str(e)}'})


@app.route('/admin/users/search')
@admin_required
def search_users():
    """Search users by email or phone number with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 5  # Max 5 users per page
        search_query = request.args.get('search', '').strip()
        
        # Build query
        query = User.query
        
        if search_query:
            # Search by email or phone
            query = query.filter(
                db.or_(
                    User.email.ilike(f'%{search_query}%'),
                    User.phone.ilike(f'%{search_query}%')
                )
            )
        
        # Paginate results
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        users_data = []
        for user in pagination.items:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'is_admin': user.is_admin,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            users_data.append(user_data)
        
        return jsonify({
            'success': True,
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error searching users: {str(e)}'})


@app.route('/admin/accounting/token-usage')
@admin_required
def token_usage_analytics():
    """Get token usage analytics by month"""
    try:
        month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
        
        # Get token usage for the month
        token_usage = TokenUsage.query.filter_by(month=month).all()
        
        # Calculate totals
        total_tokens = sum(usage.tokens_used for usage in token_usage)
        total_cost = sum(usage.cost_usd for usage in token_usage)
        
        # Get user breakdown
        user_breakdown = []
        for usage in token_usage:
            user = User.query.get(usage.user_id)
            if user:
                user_breakdown.append({
                    'user_id': usage.user_id,
                    'username': user.username,
                    'email': user.email,
                    'tokens_used': usage.tokens_used,
                    'cost_usd': usage.cost_usd,
                    'model_used': usage.model_used
                })
        
        return jsonify({
            'success': True,
            'month': month,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'user_breakdown': user_breakdown
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error retrieving token usage: {str(e)}'})


@app.route('/admin/accounting/profit-loss')
@admin_required
def profit_loss_analytics():
    """Get profit and loss analytics"""
    try:
        month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
        
        # Get token usage costs
        token_usage = TokenUsage.query.filter_by(month=month).all()
        total_api_costs = sum(usage.cost_usd for usage in token_usage)
        
        # Get payment data (placeholder - you'll need to implement this based on your payment system)
        # For now, we'll use a placeholder value
        total_payments = 0  # This should come from your payment processing system
        
        # Calculate profit/loss
        profit_loss = total_payments - total_api_costs
        
        # Get user-level breakdown
        user_breakdown = []
        for usage in token_usage:
            user = User.query.get(usage.user_id)
            if user:
                user_breakdown.append({
                    'user_id': usage.user_id,
                    'username': user.username,
                    'email': user.email,
                    'tokens_used': usage.tokens_used,
                    'api_cost': usage.cost_usd,
                    'user_payment': 0,  # This should come from your payment system
                    'user_profit_loss': 0 - usage.cost_usd  # Negative because it's a cost
                })
        
        return jsonify({
            'success': True,
            'month': month,
            'total_api_costs': total_api_costs,
            'total_payments': total_payments,
            'profit_loss': profit_loss,
            'user_breakdown': user_breakdown
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error retrieving profit/loss data: {str(e)}'})


@app.route('/admin/accounting/api-costs', methods=['GET', 'POST'])
@admin_required
def manage_api_costs():
    """Manage API costs for different models"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            model_name = data.get('model_name')
            input_cost = data.get('input_cost_per_1k')
            output_cost = data.get('output_cost_per_1k')
            
            # Update or create API cost
            api_cost = APICosts.query.filter_by(model_name=model_name).first()
            if api_cost:
                api_cost.input_cost_per_1k = input_cost
                api_cost.output_cost_per_1k = output_cost
                api_cost.updated_at = datetime.utcnow()
                api_cost.updated_by = get_current_user().id
            else:
                api_cost = APICosts(
                    model_name=model_name,
                    input_cost_per_1k=input_cost,
                    output_cost_per_1k=output_cost,
                    updated_by=get_current_user().id
                )
                db.session.add(api_cost)
            
            db.session.commit()
            return jsonify({'success': True, 'message': f'API costs for {model_name} updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Error updating API costs: {str(e)}'})
    
    # GET request - return all API costs
    try:
        api_costs = APICosts.query.filter_by(is_active=True).all()
        costs_data = []
        for cost in api_costs:
            costs_data.append({
                'id': cost.id,
                'model_name': cost.model_name,
                'input_cost_per_1k': cost.input_cost_per_1k,
                'output_cost_per_1k': cost.output_cost_per_1k,
                'updated_at': cost.updated_at.isoformat() if cost.updated_at else None
            })
        return jsonify({'success': True, 'api_costs': costs_data})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error retrieving API costs: {str(e)}'})








class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    user = db.relationship('User', backref='system_settings')


class TokenUsage(db.Model):
    __tablename__ = 'token_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM format
    input_tokens = db.Column(db.Integer, default=0)  # Prompt/input tokens
    output_tokens = db.Column(db.Integer, default=0)  # Completion/output tokens
    total_tokens = db.Column(db.Integer, default=0)  # Total tokens (input + output)
    cost_usd = db.Column(db.Float, default=0.0)
    model_used = db.Column(db.String(50), nullable=True)  # gpt-4, gpt-3.5-turbo, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='token_usage')


class APICosts(db.Model):
    __tablename__ = 'api_costs'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), nullable=False)
    input_cost_per_1m = db.Column(db.Float, nullable=False)  # Cost per 1M input tokens
    output_cost_per_1m = db.Column(db.Float, nullable=False)  # Cost per 1M output tokens
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    user = db.relationship('User', backref='api_costs')


class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    subscription_type = db.Column(db.String(20), nullable=False, default='subscription')  # 'subscription' or 'pay_as_you_go'
    stripe_subscription_id = db.Column(db.String(100), nullable=True)  # Stripe subscription ID
    stripe_customer_id = db.Column(db.String(100), nullable=True)  # Stripe customer ID
    monthly_fee_usd = db.Column(db.Float, default=10.0)  # Monthly subscription fee
    sessions_per_month = db.Column(db.Integer, default=600)  # Monthly session allowance
    sessions_used_this_month = db.Column(db.Integer, default=0)  # Sessions used in current month
    billing_cycle_start = db.Column(db.DateTime, default=datetime.utcnow)  # When billing cycle starts
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='subscription')


class SessionCredits(db.Model):
    __tablename__ = 'session_credits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    credits_purchased = db.Column(db.Integer, default=0)  # Total credits purchased
    credits_used = db.Column(db.Integer, default=0)  # Total credits used
    credits_remaining = db.Column(db.Integer, default=0)  # Remaining credits
    stripe_payment_intent_id = db.Column(db.String(100), nullable=True)  # Stripe payment intent ID
    payment_amount_usd = db.Column(db.Float, default=0.0)  # Amount paid for credits
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='session_credits')


class AIUsageSession(db.Model):
    __tablename__ = 'ai_usage_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_type = db.Column(db.String(50), nullable=False)  # 'patterns_analysis', 'ai_chat', etc.
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    cost_usd = db.Column(db.Float, default=0.0)
    model_used = db.Column(db.String(50), nullable=True)
    subscription_used = db.Column(db.Boolean, default=True)  # True if used subscription, False if used credit
    credit_id = db.Column(db.Integer, db.ForeignKey('session_credits.id'), nullable=True)  # If credit was used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='ai_sessions')
    credit = db.relationship('SessionCredits', backref='usage_sessions')

# Fallback nutritional database for common foods (per 100g)
COMMON_FOODS_DATABASE = {
    'apple': {
        'food_name': 'Apple, raw',
        'calories': 52,
        'protein': 0.3,
        'carbs': 14,
        'fat': 0.2,
        'fiber': 2.4,
        'sugar': 10.4,
        'sodium': 1,
        'source': 'common_foods_db'
    },
    'banana': {
        'food_name': 'Banana, raw',
        'calories': 89,
        'protein': 1.1,
        'carbs': 23,
        'fat': 0.3,
        'fiber': 2.6,
        'sugar': 12.2,
        'sodium': 1,
        'source': 'common_foods_db'
    },
    'chicken breast': {
        'food_name': 'Chicken breast, cooked',
        'calories': 165,
        'protein': 31,
        'carbs': 0,
        'fat': 3.6,
        'fiber': 0,
        'sugar': 0,
        'sodium': 74,
        'source': 'common_foods_db'
    },
    'brown rice': {
        'food_name': 'Brown rice, cooked',
        'calories': 111,
        'protein': 2.6,
        'carbs': 23,
        'fat': 0.9,
        'fiber': 1.8,
        'sugar': 0.4,
        'sodium': 5,
        'source': 'common_foods_db'
    },
    'almonds': {
        'food_name': 'Almonds, raw',
        'calories': 579,
        'protein': 21.2,
        'carbs': 21.7,
        'fat': 49.9,
        'fiber': 12.5,
        'sugar': 4.4,
        'sodium': 1,
        'source': 'common_foods_db'
    },
    'yogurt': {
        'food_name': 'Greek yogurt, plain',
        'calories': 59,
        'protein': 10,
        'carbs': 3.6,
        'fat': 0.4,
        'fiber': 0,
        'sugar': 3.2,
        'sodium': 36,
        'source': 'common_foods_db'
    },
    'spinach': {
        'food_name': 'Spinach, raw',
        'calories': 23,
        'protein': 2.9,
        'carbs': 3.6,
        'fat': 0.4,
        'fiber': 2.2,
        'sugar': 0.4,
        'sodium': 79,
        'source': 'common_foods_db'
    },
    'salmon': {
        'food_name': 'Salmon, cooked',
        'calories': 208,
        'protein': 25,
        'carbs': 0,
        'fat': 12,
        'fiber': 0,
        'sugar': 0,
        'sodium': 59,
        'source': 'common_foods_db'
    },
    'quinoa': {
        'food_name': 'Quinoa, cooked',
        'calories': 120,
        'protein': 4.4,
        'carbs': 22,
        'fat': 1.9,
        'fiber': 2.8,
        'sugar': 0.9,
        'sodium': 7,
        'source': 'common_foods_db'
    },
    'avocado': {
        'food_name': 'Avocado, raw',
        'calories': 160,
        'protein': 2,
        'carbs': 9,
        'fat': 15,
        'fiber': 7,
        'sugar': 0.7,
        'sodium': 7,
        'source': 'common_foods_db'
    },
    'broccoli': {
        'food_name': 'Broccoli, raw',
        'calories': 34,
        'protein': 2.8,
        'carbs': 7,
        'fat': 0.4,
        'fiber': 2.6,
        'sugar': 1.5,
        'sodium': 33,
        'source': 'common_foods_db'
    },
    'sweet potato': {
        'food_name': 'Sweet potato, cooked',
        'calories': 86,
        'protein': 1.6,
        'carbs': 20,
        'fat': 0.1,
        'fiber': 3,
        'sugar': 4.2,
        'sodium': 41,
        'source': 'common_foods_db'
    },
    'oats': {
        'food_name': 'Oats, raw',
        'calories': 389,
        'protein': 17,
        'carbs': 66,
        'fat': 7,
        'fiber': 10,
        'sugar': 1,
        'sodium': 2,
        'source': 'common_foods_db'
    },
    'eggs': {
        'food_name': 'Eggs, whole, raw',
        'calories': 155,
        'protein': 13,
        'carbs': 1.1,
        'fat': 11,
        'fiber': 0,
        'sugar': 1.1,
        'sodium': 124,
        'source': 'common_foods_db'
    },
    'milk': {
        'food_name': 'Milk, whole',
        'calories': 61,
        'protein': 3.2,
        'carbs': 4.8,
        'fat': 3.3,
        'fiber': 0,
        'sugar': 4.8,
        'sodium': 43,
        'source': 'common_foods_db'
    }
}

def search_common_foods_database(food_name):
    """Search the local common foods database"""
    food_lower = food_name.lower().strip()
    
    # Direct match
    if food_lower in COMMON_FOODS_DATABASE:
        data = COMMON_FOODS_DATABASE[food_lower].copy()
        data['serving_size'] = 100
        data['serving_unit'] = 'g'
        return data
    
    # Partial match
    for key, data in COMMON_FOODS_DATABASE.items():
        if key in food_lower or food_lower in key:
            data_copy = data.copy()
            data_copy['serving_size'] = 100
            data_copy['serving_unit'] = 'g'
            return data_copy
    
    # Word-based matching
    food_words = set(food_lower.split())
    best_match = None
    best_score = 0
    
    for key, data in COMMON_FOODS_DATABASE.items():
        key_words = set(key.split())
        common_words = food_words.intersection(key_words)
        score = len(common_words)
        
        if score > best_score:
            best_score = score
            best_match = data
    
    if best_score >= 1:  # At least one word matches
        data_copy = best_match.copy()
        data_copy['serving_size'] = 100
        data_copy['serving_unit'] = 'g'
        return data_copy
    
    return None

if __name__ == '__main__':
    app.run(debug=True)



