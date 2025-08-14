"""
Ki Wellness - Configuration Module
==================================

This module handles Flask application configuration, initialization,
and setup of external services like OAuth, Stripe, and rate limiting.

Author: Ki Wellness Team
Version: 2.0
"""

import os
from datetime import timedelta
from flask import Flask
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DevelopmentConfig, ProductionConfig
from .models import db, User, UserProfile, SystemSettings, APICosts
from typing import Optional, Union, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from flask_limiter import Limiter as FlaskLimiter

# Initialize Flask extensions
limiter: Optional[Union['FlaskLimiter', 'FallbackLimiter']] = None
oauth = None
google_oauth = None

# OAuth imports
try:
    from flask_oauthlib.client import OAuth
    OAUTH_AVAILABLE = True
    print("✅ Flask-OAuthlib available. OAuth features enabled.")
except ImportError as e:
    OAUTH_AVAILABLE = False
    print(f"⚠️  Flask-OAuthlib not available. OAuth features will be disabled.")
    print(f"   Error: {e}")
    print("   To enable OAuth, install: pip install Flask-OAuthlib")
except Exception as e:
    OAUTH_AVAILABLE = False
    print(f"⚠️  Flask-OAuthlib import failed. OAuth features will be disabled.")
    print(f"   Error: {e}")
    print("   This might be due to version compatibility issues.")

# Rate Limiter imports
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
    print("✅ Flask-Limiter available. Rate limiting features enabled.")
except ImportError:
    # Fallback for environments where Flask-Limiter is not available
    class FallbackLimiter:
        def __init__(self, app=None, key_func=None, default_limits=None, storage_uri=None):
            self.app = app
            self.key_func = key_func
            self.default_limits = default_limits or []
            self.storage_uri = storage_uri
        
        def limit(self, limit_string):
            def decorator(f):
                return f
            return decorator
    
    def get_remote_address() -> str:
        return "127.0.0.1"  # Default fallback
    
    # Type aliases for fallback
    Limiter = FallbackLimiter
    LIMITER_AVAILABLE = True
    print("⚠️  Flask-Limiter not available. Rate limiting features will be disabled.")

# Stripe integration
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    print("⚠️  Stripe library not available. Payment features will be disabled.")


def create_app():
    """Create and configure the Flask application"""
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
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'ki_wellness.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        print(f"🔧 Fallback database path: {db_path}")
    
    # Initialize extensions (db will be initialized in main.py)
    
    # Initialize Rate Limiter
    global limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["1000 per day", "200 per hour"],
        storage_uri="memory://"
    )
    
    # Initialize OAuth
    if OAUTH_AVAILABLE:
        global oauth, google_oauth
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
    
    return app


def get_stripe_config():
    """Get Stripe configuration based on payment testing mode"""
    from .models import SystemSettings
    
    try:
        # Check if payment testing mode is enabled
        testing_setting = SystemSettings.query.filter_by(key='payment_testing_mode').first()
        is_testing_mode = testing_setting and testing_setting.value == 'true'
        
        if is_testing_mode:
            # Use sandbox keys
            secret_key = os.environ.get('STRIPE_SANDBOX_SECRET_KEY')
            publishable_key = os.environ.get('STRIPE_SANDBOX_PUBLISHABLE_KEY')
            webhook_secret = os.environ.get('STRIPE_SANDBOX_WEBHOOK_SECRET')
            environment = 'sandbox'
        else:
            # Use live keys
            secret_key = os.environ.get('STRIPE_SECRET_KEY')
            publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
            webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
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
    
    import stripe
    stripe.api_key = config['secret_key']
    print(f"✅ Stripe initialized successfully ({config['environment']} mode)")
    return True


def create_admin_account():
    """Create the default admin account if it doesn't exist"""
    from .models import User, UserProfile
    from datetime import datetime
    
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
            
            # Try to create admin user profile with pre-filled fields, but handle gracefully if table doesn't exist
            try:
                # Parse the date of birth (11/10/1988)
                dob = datetime.strptime('11/10/1988', '%m/%d/%Y').date()
                
                admin_profile = UserProfile(
                    user_id=admin_user.id,
                    name=admin_name,
                    avatar='default-avatar.png',
                    weight_unit='lbs',  # Changed to lbs as requested
                    date_of_birth=dob,
                    weight=120.0,  # 120 lbs
                    height=168.0   # 168 cm
                )
                
                db.session.add(admin_profile)
                db.session.commit()
                print("✅ Admin profile created successfully with pre-filled fields!")
                print(f"   Name: {admin_name}")
                print(f"   Date of Birth: {dob.strftime('%m/%d/%Y')}")
                print(f"   Weight: 120 lbs")
                print(f"   Height: 168 cm")
            except Exception as e:
                print(f"⚠️  Warning: Could not create admin profile: {e}")
                # Continue without profile - not critical for admin functionality
            
            print("✅ Admin account created successfully!")
            print(f"   Username: {admin_username}")
            print(f"   Email: {admin_email}")
        else:
            print("ℹ️  Admin account already exists")
            
            # Check if admin profile exists and update with pre-filled data if needed
            admin_profile = UserProfile.query.filter_by(user_id=admin_user.id).first()
            if admin_profile:
                # Check if profile needs to be updated with pre-filled data
                needs_update = (
                    admin_profile.weight_unit != 'lbs' or
                    admin_profile.date_of_birth is None or
                    admin_profile.weight is None or
                    admin_profile.height is None
                )
                
                if needs_update:
                    print("🔄 Updating admin profile with pre-filled data...")
                    dob = datetime.strptime('11/10/1988', '%m/%d/%Y').date()
                    admin_profile.name = admin_name
                    admin_profile.avatar = 'default-avatar.png'
                    admin_profile.weight_unit = 'lbs'
                    admin_profile.date_of_birth = dob
                    admin_profile.weight = 120.0
                    admin_profile.height = 168.0
                    db.session.commit()
                    print("✅ Admin profile updated with pre-filled data!")
                    print(f"   Name: {admin_name}")
                    print(f"   Date of Birth: {dob.strftime('%m/%d/%Y')}")
                    print(f"   Weight: 120 lbs")
                    print(f"   Height: 168 cm")
                else:
                    print("ℹ️  Admin profile already has pre-filled data")
            
        # Initialize system settings
        initialize_system_settings(admin_user.id)
        
    except Exception as e:
        print(f"❌ Error creating admin account: {e}")
        db.session.rollback()


def initialize_system_settings(admin_user_id):
    """Initialize default system settings"""
    from .models import SystemSettings, APICosts
    
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
                    'description': 'Presence penalty for OpenAI API'
                },
                {
                    'key': 'frequency_penalty',
                    'value': '0.0',
                    'description': 'Frequency penalty for OpenAI API'
                },
                {
                    'key': 'top_p',
                    'value': '0.9',
                    'description': 'Top-p sampling value for OpenAI API'
                },
                {
                    'key': 'payment_testing_mode',
                    'value': 'false',
                    'description': 'Enable payment testing mode (uses sandbox keys)'
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
            
            # Initialize default API costs
            default_api_costs = [
                {
                    'model_name': 'gpt-4',
                    'input_cost_per_1k': 0.03,
                    'output_cost_per_1k': 0.06
                },
                {
                    'model_name': 'gpt-4-turbo',
                    'input_cost_per_1k': 0.01,
                    'output_cost_per_1k': 0.03
                },
                {
                    'model_name': 'gpt-3.5-turbo',
                    'input_cost_per_1k': 0.0015,
                    'output_cost_per_1k': 0.002
                }
            ]
            
            for cost in default_api_costs:
                api_cost = APICosts(
                    model_name=cost['model_name'],
                    input_cost_per_1m=cost['input_cost_per_1k'] * 1000,  # Convert to per 1M tokens
                    output_cost_per_1m=cost['output_cost_per_1k'] * 1000,  # Convert to per 1M tokens
                    updated_by=admin_user_id
                )
                db.session.add(api_cost)
            
            db.session.commit()
            print("✅ System settings initialized successfully!")
        else:
            print("ℹ️  System settings already exist")
            
    except Exception as e:
        print(f"❌ Error initializing system settings: {e}")
        db.session.rollback()


def ensure_tables_exist():
    """Ensure all database tables exist"""
    try:
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False
