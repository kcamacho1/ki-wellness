import os
import requests
import json
import uuid
import re
import secrets
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, session
import mimetypes
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import sqlite3

# Import psycopg only for production (PostgreSQL)
# This is optional and won't break development with SQLite
# OpenRouter import for AI chat
from services.openrouter_client import get_openrouter_client, generate_ai_response
# Stripe import removed - using Calendly and donation links instead
from services.food_data import BASIC_FOODS, COMMON_FOODS_DB
from services.health_resources import get_relevant_resources, format_resources_for_prompt

# Import database and models
from database import db, User, FoodLog, WaterLog, MoodLog, Note, Recipe, RecipeIngredient, RecipeInstruction, Subscription, AIUsageLog

# Import recipe API
from apis.recipe_api import recipe_bp

# Import Stripe client
from services.stripe_client import get_stripe_client

# Import analytics service
from services.analytics_service import analytics_service

# Import security modules
from security_middleware import SecurityMiddleware, rate_limit, sanitize_input
from database_security import validate_user_input, sanitize_user_input, create_safe_query
# reCAPTCHA removed - using Cloudflare bot protection instead

def premium_required(f):
    """Decorator to require premium subscription or special role access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
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
            return redirect(url_for('login'))
        
        if not current_user.can_access_admin_dashboard():
            return jsonify({
                'success': False, 
                'error': 'Admin access required',
                'message': 'You do not have permission to access this feature.'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Fix MIME types for static files
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

# Session configuration - Auto-logout after 24 hours of inactivity
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Keep HttpOnly for security
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# reCAPTCHA removed - using Cloudflare bot protection instead

# Database configuration - Multi-driver approach
db_url = os.getenv('DATABASE_URL')
is_production = bool(db_url and 'postgresql' in db_url)

if is_production:
    # Production - PostgreSQL with driver detection
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    # Try to use the best available driver
    try:
        import psycopg2
        print("✅ Using psycopg2 (maximum compatibility)")
        # Use standard postgresql:// URL - SQLAlchemy will auto-detect
    except ImportError:
        try:
            import psycopg
            print("✅ Using psycopg3 (Python 3.13+ compatible)")
            # Force psycopg dialect
            if '+psycopg' not in db_url:
                db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        except ImportError:
            print("⚠️ No PostgreSQL driver found - falling back to SQLite")
            db_url = None
            is_production = False
    
    if is_production:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {
                'connect_timeout': 10
            }
        }
        print("🚀 Running in PRODUCTION mode with PostgreSQL")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ki_wellness.db'
        print("🛠️ Falling back to DEVELOPMENT mode with SQLite")
else:
    # Development - SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ki_wellness.db'
    print("🛠️ Running in DEVELOPMENT mode with SQLite")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/profile_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database with app
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize security middleware
security_middleware = SecurityMiddleware(app)
security_middleware.init_app(app)

# API Configuration
OPENFOODFACTS_API = "https://world.openfoodfacts.org/cgi/search.pl"
USDA_API_KEY = os.getenv('USDA_API_KEY')
USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"

# Stripe Configuration removed - using Calendly and donation links instead

# Food data imported from food_data.py

# Database models are now imported from database.py

class AIAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    analysis_data = db.Column(db.Text, nullable=False)  # JSON string of analysis
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaymentSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be null for non-logged in users
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    payment_type = db.Column(db.String(50), nullable=False)  # '30min_session' or 'donation'
    stripe_payment_intent_id = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed, cancelled
    calendly_link_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='payment_sessions')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def check_session_expiry():
    """Check if user session has expired and auto-logout if necessary"""
    if current_user.is_authenticated:
        # Only check for session expiry, don't force logout on every request
        # Flask-Login and Flask sessions handle the expiry automatically
        
        # Update last activity time for session tracking
        session['last_activity'] = datetime.utcnow().isoformat()
        session.permanent = True
        session.modified = True

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(file, user_id):
    """Save uploaded profile image and return the filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(filepath)
        return f"uploads/profile_images/{filename}"
    return None

def delete_profile_image(filename):
    """Delete profile image file"""
    if filename:
        try:
            filepath = os.path.join('static', filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            print(f"Error deleting profile image: {e}")
    return False

def get_profile_image_url(profile_image_path):
    """Get profile image URL with fallback to default image"""
    if not profile_image_path:
        return url_for('static', filename='assets/avatars/default-avatar.png')

def get_available_avatars():
    """Get list of available avatar options"""
    avatars = [
        {'id': 'default', 'name': 'Default', 'path': 'assets/avatars/default-avatar.png'},
        {'id': 'man1', 'name': 'Man 1', 'path': 'assets/avatars/man1.png'},
        {'id': 'man2', 'name': 'Man 2', 'path': 'assets/avatars/man2.png'},
        {'id': 'man3', 'name': 'Man 3', 'path': 'assets/avatars/man3.png'},
        {'id': 'man4', 'name': 'Man 4', 'path': 'assets/avatars/man4.png'},
        {'id': 'man5', 'name': 'Man 5', 'path': 'assets/avatars/man5.png'},
        {'id': 'girl1', 'name': 'Woman 1', 'path': 'assets/avatars/girl1.png'},
        {'id': 'girl2', 'name': 'Woman 2', 'path': 'assets/avatars/girl2.png'},
        {'id': 'girl3', 'name': 'Woman 3', 'path': 'assets/avatars/girl3.png'},
        {'id': 'girl4', 'name': 'Woman 4', 'path': 'assets/avatars/girl4.png'},
        {'id': 'girl5', 'name': 'Woman 5', 'path': 'assets/avatars/girl5.png'}
    ]
    return avatars

    
    # Check if the profile image file exists
    filepath = os.path.join('static', profile_image_path)
    if os.path.exists(filepath):
        return url_for('static', filename=profile_image_path)
    else:
        # Return default image if the specified image doesn't exist
        return url_for('static', filename='assets/avatars/default-avatar.png')


def create_admin_user():
    """Create admin user if it doesn't exist"""
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')
    admin_email = os.getenv('ADMIN_EMAIL')
    
    if admin_username and admin_password and admin_email:
        admin_user = User.query.filter_by(username=admin_username).first()
        if not admin_user:
            admin_user = User(
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                name="Admin User",
                is_admin=True,
                # Auto-agreement for admin account
                agreed_to_terms=True,
                agreed_to_privacy=True,
                agreed_to_disclaimer=True,
                agreements_date=datetime.utcnow()
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Admin user '{admin_username}' created successfully with auto-agreement")
        else:
            # Update existing admin user with agreements if not already set
            if not admin_user.agreed_to_terms:
                admin_user.agreed_to_terms = True
                admin_user.agreed_to_privacy = True
                admin_user.agreed_to_disclaimer = True
                admin_user.agreements_date = datetime.utcnow()
                db.session.commit()
                print(f"✅ Admin user '{admin_username}' updated with auto-agreement")

def initialize_app_settings():
    """Initialize default app settings"""
    settings = [
        ('new_accounts_enabled', 'true', 'Enable or disable new user account creation'),
        ('maintenance_mode', 'false', 'Enable maintenance mode for the application'),
        ('max_users', '1000', 'Maximum number of users allowed in the system'),
        ('allowed_emails', '', 'Comma-separated list of email addresses allowed to register even when disabled'),
        ('human_help_payment_type', '30min_session', 'Payment type for human help: 30min_session or donation'),
        ('calendly_link', 'https://calendly.com/ki-wellness/human-health-coach', 'Calendly link for scheduling appointments')
    ]
    
    for key, value, description in settings:
        setting = AppSettings.query.filter_by(key=key).first()
        if not setting:
            setting = AppSettings(key=key, value=value, description=description)
            db.session.add(setting)
    
    db.session.commit()

def get_app_setting(key, default=None):
    """Get an app setting value"""
    setting = AppSettings.query.filter_by(key=key).first()
    return setting.value if setting else default

def check_ai_usage_limits(user_id):
    """Check if user has exceeded AI usage limits (PER-USER limits, globally configured)"""
    if not get_app_setting('enforce_limits', 'false').lower() == 'true':
        return True, None  # Limits not enforced
    
    today = datetime.utcnow().date()
    this_month = datetime.utcnow().replace(day=1).date()
    
    # Check PER-USER daily token limit (configured globally, applied per user)
    daily_token_limit = int(get_app_setting('daily_token_limit', '0'))
    if daily_token_limit > 0:
        today_tokens = db.session.query(
            db.func.sum(AIUsageLog.input_tokens + AIUsageLog.output_tokens)
        ).filter(
            AIUsageLog.user_id == user_id,
            db.func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        if today_tokens >= daily_token_limit:
            return False, f"Daily token limit ({daily_token_limit}) exceeded. You used: {today_tokens}"
    
    # Check PER-USER daily call limit (configured globally, applied per user)
    daily_call_limit = int(get_app_setting('daily_call_limit', '0'))
    if daily_call_limit > 0:
        today_calls = db.session.query(
            db.func.count(AIUsageLog.id)
        ).filter(
            AIUsageLog.user_id == user_id,
            db.func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        if today_calls >= daily_call_limit:
            return False, f"Daily call limit ({daily_call_limit}) exceeded. You made: {today_calls} calls"
    
    # Check PER-USER monthly cost limit (configured globally, applied per user)
    monthly_cost_limit = float(get_app_setting('monthly_cost_limit', '0'))
    if monthly_cost_limit > 0:
        month_cost = db.session.query(
            db.func.sum(AIUsageLog.total_cost)
        ).filter(
            AIUsageLog.user_id == user_id,
            db.func.date(AIUsageLog.created_at) >= this_month
        ).scalar() or 0
        
        if month_cost >= monthly_cost_limit:
            return False, f"Monthly cost limit (${monthly_cost_limit:.4f}) exceeded. Your cost: ${month_cost:.4f}"
    
    return True, None  # All limits passed

def set_app_setting(key, value):
    """Set an app setting value"""
    # Convert boolean values to lowercase strings for consistency
    if isinstance(value, bool):
        value = str(value).lower()
    elif isinstance(value, str) and value.lower() in ['true', 'false']:
        value = value.lower()
    
    setting = AppSettings.query.filter_by(key=key).first()
    if setting:
        setting.value = value
        setting.updated_at = datetime.utcnow()
    else:
        setting = AppSettings(key=key, value=value)
        db.session.add(setting)
    
    db.session.commit()
    return setting

def search_usda_api(query):
    """Search USDA FoodData Central API"""
    if not USDA_API_KEY:
        return []
    
    try:
        url = f"{USDA_API_BASE}/foods/search"
        params = {
            'api_key': USDA_API_KEY,
            'query': query,
            'pageSize': 3,  # Reduced for speed
            'dataType': 'Foundation',
            'sortBy': 'dataType.keyword',
            'sortOrder': 'asc'
        }
        
        response = requests.get(url, params=params, timeout=3)  # Reduced timeout
        response.raise_for_status()
        data = response.json()
        
        results = []
        for food in data.get('foods', []):
            # Extract nutrition data
            nutrients = {}
            for nutrient in food.get('foodNutrients', []):
                nutrient_id = nutrient.get('nutrientId')
                value = nutrient.get('value', 0)
                
                # Map USDA nutrient IDs to our fields
                if nutrient_id == 1008:  # Calories
                    nutrients['calories'] = value
                elif nutrient_id == 1003:  # Protein
                    nutrients['protein'] = value
                elif nutrient_id == 205:   # Carbohydrates
                    nutrients['carbs'] = value
                elif nutrient_id == 204:   # Total Fat
                    nutrients['fat'] = value
                elif nutrient_id == 291:   # Fiber
                    nutrients['fiber'] = value
                elif nutrient_id == 269:   # Sugars
                    nutrients['sugar'] = value
                elif nutrient_id == 307:   # Sodium
                    nutrients['sodium'] = value
            
            results.append({
                'name': food.get('description', 'Unknown Food'),
                'brand': 'USDA Foundation',
                'calories': nutrients.get('calories', 0),
                'protein': nutrients.get('protein', 0),
                'carbs': nutrients.get('carbs', 0),
                'fat': nutrients.get('fat', 0),
                'fiber': nutrients.get('fiber', 0),
                'sugar': nutrients.get('sugar', 0),
                'sodium': nutrients.get('sodium', 0),
                'source': 'usda'
            })
        
        return results[:3]  # Return top 3 results
    except Exception as e:
        print(f"USDA API error: {e}")
        return []

def search_openfoodfacts_api(query):
    """Search Open Food Facts API"""
    try:
        # Create search terms for better results
        search_terms = [query]
        
        # Add variations for common foods (limited for speed)
        query_lower = query.lower()
        if 'coconut' in query_lower:
            search_terms.extend(['coconut milk', 'coconut cream'])
        elif 'milk' in query_lower:
            search_terms.extend(['almond milk', 'soy milk'])
        elif 'chicken' in query_lower:
            search_terms.extend(['chicken breast'])
        elif 'rice' in query_lower:
            search_terms.extend(['brown rice', 'white rice'])
        elif 'olive' in query_lower and 'oil' in query_lower:
            search_terms.extend(['olive oil extra virgin', 'olive oil pure'])
        elif 'oil' in query_lower:
            search_terms.extend(['cooking oil', 'vegetable oil'])
        
        all_results = []
        for search_term in search_terms[:2]:  # Limit to 2 search terms for speed
            params = {
                'search_terms': search_term,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 8  # Reduced for speed
            }
            
            response = requests.get(OPENFOODFACTS_API, params=params, timeout=3)  # Reduced timeout
            response.raise_for_status()
            data = response.json()
            
            for product in data.get('products', []):
                # Skip products without nutrition data
                if not product.get('nutriments'):
                    continue
                
                nutriments = product['nutriments']
                
                # Skip products with very low nutrition data
                if (nutriments.get('energy-kcal_100g', 0) < 10 and 
                    nutriments.get('proteins_100g', 0) < 1 and 
                    nutriments.get('carbohydrates_100g', 0) < 1 and 
                    nutriments.get('fat_100g', 0) < 1):
                    continue
                
                result = {
                    'name': product.get('product_name', 'Unknown Product'),
                    'brand': product.get('brands', 'Unknown Brand'),
                    'calories': nutriments.get('energy-kcal_100g', 0),
                    'protein': nutriments.get('proteins_100g', 0),
                    'carbs': nutriments.get('carbohydrates_100g', 0),
                    'fat': nutriments.get('fat_100g', 0),
                    'fiber': nutriments.get('fiber_100g', 0),
                    'sugar': nutriments.get('sugars_100g', 0),
                    'sodium': nutriments.get('sodium_100g', 0),
                    'source': 'openfoodfacts'
                }
                
                # Filter out highly processed products for basic foods
                product_name = result['name'].lower()
                exclude_terms = ['broth', 'soup', 'juice', 'sauce', 'candy', 'chips', 'cookies', 'cake', 'ice cream']
                
                # Don't exclude oils and fats
                if 'oil' in query_lower or 'butter' in query_lower or 'ghee' in query_lower:
                    pass  # Allow oils and fats through
                elif any(exclude in product_name for exclude in exclude_terms):
                    continue
                
                all_results.append(result)
        
        # Remove duplicates and sort by relevance
        unique_results = []
        seen_names = set()
        for result in all_results:
            if result['name'] not in seen_names:
                unique_results.append(result)
                seen_names.add(result['name'])
        
        return unique_results[:6]  # Return up to 6 results for speed
    except Exception as e:
        print(f"Open Food Facts API error: {e}")
        return []

# Routes
# Static files are handled automatically by Flask with MIME types configured above

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=50, window=60)  # Increased limit for development
def login():
    if request.method == 'POST':
        # Validate and sanitize inputs
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Input validation
        if not validate_user_input(username, max_length=50):
            flash('Invalid username format', 'error')
            return render_template('login.html')
            
        if not validate_user_input(password, max_length=100):
            flash('Invalid password format', 'error')
            return render_template('login.html')
        
        # Sanitize inputs
        username = sanitize_user_input(username, max_length=50)
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            # Check if email is verified
            if not user.email_verified:
                flash('Please verify your email address before logging in. Check your inbox for the verification link.', 'warning')
                return render_template('login.html')
            
            login_user(user, remember=True)  # Enable remember me functionality
            session.permanent = True  # Make session permanent for timeout tracking
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=300)  # Limit registration attempts
def register():
    # Check if new account creation is enabled
    new_accounts_enabled = get_app_setting('new_accounts_enabled', 'true').lower() == 'true'
    allowed_emails = get_app_setting('allowed_emails', '').split(',')
    allowed_emails = [email.strip().lower() for email in allowed_emails if email.strip()]
    
    # Always show the registration form, but pass registration status to template
    registration_disabled = not new_accounts_enabled
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        
        # Check if registration is disabled and email is not in allowed list
        if not new_accounts_enabled and email not in allowed_emails:
            flash('New account registration is currently disabled. Your email address is not on the allowed list. Please contact the administrator.', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
    
    if request.method == 'POST':
        # Validate and sanitize all inputs
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        
        # Input validation
        if not validate_user_input(username, max_length=50):
            flash('Invalid username format', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
            
        if not validate_user_input(email, max_length=120):
            flash('Invalid email format', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
            
        if not validate_user_input(name, max_length=100):
            flash('Invalid name format', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
            
        if not validate_user_input(password, max_length=100):
            flash('Invalid password format', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
        
        # Sanitize inputs
        username = sanitize_user_input(username, max_length=50)
        email = sanitize_user_input(email, max_length=120)
        name = sanitize_user_input(name, max_length=100)
        
        # Validate password strength
        is_valid_password, password_error = validate_password_strength(password)
        if not is_valid_password:
            flash(password_error, 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
        
        # Validate agreements
        agree_terms = request.form.get('agree_terms') == 'on'
        agree_privacy = request.form.get('agree_privacy') == 'on'
        agree_disclaimer = request.form.get('agree_disclaimer') == 'on'
        
        # Check if all agreements are accepted
        if not agree_terms:
            flash('You must agree to the Terms of Service', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
        
        if not agree_privacy:
            flash('You must agree to the Privacy Policy', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
        
        if not agree_disclaimer:
            flash('You must acknowledge the Medical Disclaimer', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
        
        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        # Create new user with email verification required
        user = User(
            username=username,
            email=email,
            name=name,
            password_hash=generate_password_hash(password),
            agreed_to_terms=True,
            agreed_to_privacy=True,
            agreed_to_disclaimer=True,
            agreements_date=datetime.utcnow(),
            email_verified=False,
            email_verification_token=verification_token,
            email_verification_expires=verification_expires,
            email_verification_sent_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        try:
            from services.email_service import EmailService
            email_service = EmailService()
            email_sent = email_service.send_email_verification(
                to_email=email,
                verification_token=verification_token,
                username=name
            )
            
            if email_sent:
                flash('Registration successful! Please check your email and click the verification link before logging in.', 'success')
            else:
                flash('Registration successful, but we couldn\'t send the verification email. Please contact support.', 'warning')
                
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            flash('Registration successful, but we couldn\'t send the verification email. Please contact support.', 'warning')
        
        return redirect(url_for('login'))
    
    return render_template('register.html', 
                         registration_disabled=registration_disabled, 
                         allowed_emails=allowed_emails,
)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/extend-session')
@login_required
def extend_session():
    """Extend user session by updating session expiry"""
    if current_user.is_authenticated:
        session.permanent = True
        session.modified = True
        return jsonify({'success': True, 'message': 'Session extended'})
    return jsonify({'success': False, 'message': 'User not authenticated'}), 401

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot_password.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                # Generate reset token
                reset_token = str(uuid.uuid4())
                reset_expires = datetime.now() + timedelta(hours=24)
                
                # Update user with reset token
                user.reset_token = reset_token
                user.reset_token_expires = reset_expires
                db.session.commit()
                
                # Send password reset email
                from services.email_service import EmailService
                email_service = EmailService()
                
                if email_service.send_password_reset_email(email, reset_token, user.name):
                    flash('Password reset link has been sent to your email address.', 'success')
                else:
                    flash('There was an error sending the reset email. Please try again or contact support.', 'error')
                    
            except Exception as e:
                print(f"Error in forgot password: {e}")
                flash('There was an error processing your request. Please try again.', 'error')
        else:
            # Don't reveal whether email exists or not for security
            flash('If your email address exists in our system, you will receive a password reset link.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    # Find user by reset token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now():
        flash('Invalid or expired reset link. Please request a new password reset.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('reset_password.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')
        
        # Validate password strength
        if not validate_password_strength(password):
            flash('Password does not meet security requirements.', 'error')
            return render_template('reset_password.html')
        
        try:
            # Update password and clear reset token
            user.password = generate_password_hash(password)
            user.reset_token = None
            user.reset_token_expires = None
            db.session.commit()
            
            flash('Your password has been successfully reset. You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Error resetting password: {e}")
            flash('There was an error resetting your password. Please try again.', 'error')
    
    return render_template('reset_password.html')

# Email Verification Route
@app.route('/verify-email/<token>')
def verify_email(token):
    """Handle email verification with token"""
    # Find user by verification token
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash('Invalid verification link. Please contact support if you continue to have issues.', 'error')
        return redirect(url_for('login'))
    
    # Check if token has expired
    if user.email_verification_expires and user.email_verification_expires < datetime.utcnow():
        flash('Verification link has expired. Please contact support to resend a new verification email.', 'error')
        return redirect(url_for('login'))
    
    # Check if already verified
    if user.email_verified:
        flash('Your email is already verified! You can log in now.', 'info')
        return redirect(url_for('login'))
    
    # Verify the email
    try:
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        db.session.commit()
        
        flash('🎉 Email verified successfully! You can now log in to your account.', 'success')
        logger.info(f"Email verified for user: {user.username}")
        
    except Exception as e:
        logger.error(f"Error verifying email for user {user.username}: {str(e)}")
        db.session.rollback()
        flash('There was an error verifying your email. Please try again or contact support.', 'error')
    
    return redirect(url_for('login'))

# Resend verification email route
@app.route('/resend-verification', methods=['POST'])
@rate_limit(max_requests=3, window=300)  # Limit resend attempts
def resend_verification():
    """Resend email verification"""
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        flash('Please provide your email address.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Don't reveal if email exists for security
        flash('If an account with that email exists and is unverified, a new verification email has been sent.', 'info')
        return redirect(url_for('login'))
    
    if user.email_verified:
        flash('Your email is already verified! You can log in now.', 'info')
        return redirect(url_for('login'))
    
    # Generate new verification token
    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    try:
        # Update user with new token
        user.email_verification_token = verification_token
        user.email_verification_expires = verification_expires
        user.email_verification_sent_at = datetime.utcnow()
        db.session.commit()
        
        # Send verification email
        from services.email_service import EmailService
        email_service = EmailService()
        email_sent = email_service.send_email_verification(
            to_email=email,
            verification_token=verification_token,
            username=user.name
        )
        
        if email_sent:
            flash('A new verification email has been sent. Please check your inbox.', 'success')
        else:
            flash('There was an error sending the verification email. Please try again later.', 'error')
            
    except Exception as e:
        logger.error(f"Failed to resend verification email to {email}: {str(e)}")
        db.session.rollback()
        flash('There was an error sending the verification email. Please try again later.', 'error')
    
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')



@app.route('/ai-coach')
@login_required
def ai_coach():
    # Check if user has premium access or is admin
    if current_user.is_admin:
        return render_template('ai_coach.html')
    
    subscription = Subscription.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).first()
    
    if not subscription or not subscription.is_premium:
        # Redirect to profile page with upgrade prompt
        flash('You need a premium subscription to access the AI Health Coach. Upgrade now for just $5/month!', 'info')
        return redirect(url_for('profile'))
    
    # Check AI usage limits
    limits_ok, limit_message = check_ai_usage_limits(current_user.id)
    if not limits_ok:
        flash(f'AI usage limit exceeded: {limit_message}. Please try again tomorrow or contact support.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('ai_coach.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    
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

@app.route('/api/admin/settings', methods=['GET'])
@admin_required
def get_admin_settings():
    """Get admin settings for frontend"""
    try:
        settings = {
            'daily_token_limit': get_app_setting('daily_token_limit', '0'),
            'daily_call_limit': get_app_setting('daily_call_limit', '0'),
            'monthly_cost_limit': get_app_setting('monthly_cost_limit', '0'),
            'enforce_limits': get_app_setting('enforce_limits', 'false'),
            'new_accounts_enabled': get_app_setting('new_accounts_enabled', 'true'),
            'maintenance_mode': get_app_setting('maintenance_mode', 'false'),
            'max_users': get_app_setting('max_users', '1000')
        }
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/settings', methods=['POST'])
@admin_required
def update_admin_settings():
    
    try:
        data = request.get_json()
        setting_key = data.get('key')
        setting_value = data.get('value')
        
        if setting_key and setting_value is not None:
            set_app_setting(setting_key, str(setting_value))
            return jsonify({'success': True, 'message': 'Setting updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/analytics')
@admin_required
def get_admin_analytics():
    """Get comprehensive analytics for admin dashboard"""
    
    try:
        # Get analytics for the last 12 months
        analytics = analytics_service.get_monthly_analytics(months_back=12)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        print(f"❌ Error getting admin analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/ai-usage')
@admin_required
def get_admin_ai_usage():
    """Get AI usage analytics for admin dashboard"""
    
    try:
        # Get AI usage for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        ai_usage = analytics_service.get_ai_usage_summary(start_date, end_date)
        
        return jsonify({
            'success': True,
            'ai_usage': ai_usage
        })
        
    except Exception as e:
        print(f"❌ Error getting AI usage analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-usage/current-user')
@login_required
def get_current_user_ai_usage():
    """Get current user's AI usage statistics"""
    try:
        today = datetime.utcnow().date()
        this_month = datetime.utcnow().replace(day=1).date()
        
        # Get today's usage
        today_usage = db.session.query(
            db.func.sum(AIUsageLog.input_tokens + AIUsageLog.output_tokens).label('total_tokens'),
            db.func.count(AIUsageLog.id).label('total_calls'),
            db.func.sum(AIUsageLog.total_cost).label('total_cost')
        ).filter(
            AIUsageLog.user_id == current_user.id,
            db.func.date(AIUsageLog.created_at) == today
        ).first()
        
        # Get this month's usage
        month_usage = db.session.query(
            db.func.sum(AIUsageLog.total_cost).label('total_cost')
        ).filter(
            AIUsageLog.user_id == current_user.id,
            db.func.date(AIUsageLog.created_at) >= this_month
        ).first()
        
        # Get limits
        daily_token_limit = int(get_app_setting('daily_token_limit', '0'))
        daily_call_limit = int(get_app_setting('daily_call_limit', '0'))
        monthly_cost_limit = float(get_app_setting('monthly_cost_limit', '0'))
        
        return jsonify({
            'success': True,
            'usage': {
                'today': {
                    'tokens': int(today_usage.total_tokens) if today_usage.total_tokens else 0,
                    'calls': int(today_usage.total_calls) if today_usage.total_calls else 0,
                    'cost': float(today_usage.total_cost) if today_usage.total_cost else 0.0
                },
                'month': {
                    'cost': float(month_usage.total_cost) if month_usage.total_cost else 0.0
                }
            },
            'limits': {
                'daily_tokens': daily_token_limit,
                'daily_calls': daily_call_limit,
                'monthly_cost': monthly_cost_limit
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting user AI usage: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/revenue')
@admin_required
def get_admin_revenue():
    """Get revenue analytics for admin dashboard"""
    
    try:
        # Get revenue for the last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        revenue = analytics_service.get_revenue_summary(start_date, end_date)
        
        return jsonify({
            'success': True,
            'revenue': revenue
        })
        
    except Exception as e:
        print(f"❌ Error getting revenue analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/assign-ff-roles', methods=['POST'])
@admin_required
def assign_ff_roles_to_allowed_emails():
    """Assign 'ff' role to all users with allowed email addresses"""
    try:
        # Get allowed emails from app settings
        allowed_emails_setting = get_app_setting('allowed_emails', '')
        if not allowed_emails_setting:
            return jsonify({'success': False, 'error': 'No allowed emails configured'}), 400
        
        # Parse comma-separated emails
        allowed_emails = [email.strip().lower() for email in allowed_emails_setting.split(',') if email.strip()]
        if not allowed_emails:
            return jsonify({'success': False, 'error': 'No valid email addresses found in allowed emails'}), 400
        
        # Find and update users with allowed email addresses
        updated_count = 0
        already_ff_count = 0
        
        for email in allowed_emails:
            user = User.query.filter(User.email.ilike(email)).first()
            if user:
                if user.role != 'ff':
                    user.role = 'ff'
                    updated_count += 1
                else:
                    already_ff_count += 1
        
        # Commit changes
        db.session.commit()
        
        # Prepare response message
        if updated_count > 0:
            message = f"Successfully assigned 'ff' role to {updated_count} user(s). {already_ff_count} user(s) already had 'ff' role."
        else:
            message = f"All {already_ff_count} user(s) already have 'ff' role."
        
        return jsonify({
            'success': True, 
            'message': message,
            'updated_count': updated_count,
            'already_ff_count': already_ff_count
        })
        
    except Exception as e:
        print(f"❌ Error assigning FF roles: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin users management page"""
    # Get user statistics
    total_users = User.query.count()
    admin_users_count = User.query.filter_by(is_admin=True).count()
    ff_users_count = User.query.filter_by(role='ff').count()
    regular_users_count = User.query.filter_by(role='user').count()
    
    # Get app settings
    allowed_emails = get_app_setting('allowed_emails', '')
    
    return render_template('admin_users.html',
                         total_users=total_users,
                         admin_users_count=admin_users_count,
                         ff_users_count=ff_users_count,
                         regular_users_count=regular_users_count,
                         allowed_emails=allowed_emails)

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics page"""
    return render_template('admin_analytics.html')

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin system settings page"""
    # Get app settings
    new_accounts_enabled = get_app_setting('new_accounts_enabled', 'true').lower() == 'true'
    maintenance_mode = get_app_setting('maintenance_mode', 'false').lower() == 'true'
    max_users = get_app_setting('max_users', '1000')
    
    # Get AI limit settings
    daily_token_limit = get_app_setting('daily_token_limit', '0')
    daily_call_limit = get_app_setting('daily_call_limit', '0')
    monthly_cost_limit = get_app_setting('monthly_cost_limit', '0')
    enforce_limits = get_app_setting('enforce_limits', 'false').lower() == 'true'
    
    # Get today's AI usage statistics
    today = datetime.utcnow().date()
    today_usage = db.session.query(
        db.func.sum(AIUsageLog.input_tokens + AIUsageLog.output_tokens).label('total_tokens'),
        db.func.count(AIUsageLog.id).label('total_calls'),
        db.func.sum(AIUsageLog.total_cost).label('total_cost')
    ).filter(
        db.func.date(AIUsageLog.created_at) == today
    ).first()
    
    today_total_tokens = int(today_usage.total_tokens) if today_usage.total_tokens else 0
    today_total_calls = int(today_usage.total_calls) if today_usage.total_calls else 0
    today_total_cost = float(today_usage.total_cost) if today_usage.total_cost else 0.0
    
    return render_template('admin_settings.html',
                         new_accounts_enabled=new_accounts_enabled,
                         maintenance_mode=maintenance_mode,
                         max_users=max_users,
                         daily_token_limit=daily_token_limit,
                         daily_call_limit=daily_call_limit,
                         monthly_cost_limit=monthly_cost_limit,
                         enforce_limits=enforce_limits,
                         today_total_tokens=today_total_tokens,
                         today_total_calls=today_total_calls,
                         today_total_cost=today_total_cost)

@app.route('/admin/payments')
@admin_required
def admin_payments():
    """Admin payments and services page"""
    # Get app settings
    human_help_payment_type = get_app_setting('human_help_payment_type', '30min_session')
    calendly_link = get_app_setting('calendly_link', 'https://calendly.com/ki-wellness/human-health-coach')
    
    return render_template('admin_payments.html',
                         human_help_payment_type=human_help_payment_type,
                         calendly_link=calendly_link)

@app.route('/admin/system')
@admin_required
def admin_system():
    """Admin system information page"""
    try:
        # Get system information
        import psutil
        import platform
        
        # CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # System info
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': cpu_percent,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'memory_percent': memory.percent,
            'disk_total': disk.total,
            'disk_used': disk.used,
            'disk_percent': disk.percent
        }
        
        # Get security statistics
        security_stats = {
            'blocked_ips': len(security_middleware.bot_signatures['blocked_ips']),
            'suspicious_ips': len(security_middleware.bot_signatures['suspicious_ips']),
            'cloudflare_protection': True,  # Using Cloudflare bot protection
            'rate_limit_violations': sum(1 for ip_data in security_middleware.rate_limit_db.values() 
                                       if len(ip_data['requests']) > 50)
        }
        
        return render_template('admin_system.html', system_info=system_info, security_stats=security_stats)
        
    except ImportError:
        # psutil not available
        system_info = {
            'error': 'System monitoring not available (psutil not installed)'
        }
        security_stats = {
            'blocked_ips': len(security_middleware.bot_signatures['blocked_ips']),
            'suspicious_ips': len(security_middleware.bot_signatures['suspicious_ips']),
            'cloudflare_protection': True,  # Using Cloudflare bot protection
            'rate_limit_violations': 0
        }
        return render_template('admin_system.html', system_info=system_info, security_stats=security_stats)
    except Exception as e:
        print(f"❌ Error getting system info: {e}")
        return render_template('admin_system.html', system_info={'error': str(e)}, security_stats={})

@app.route('/api/admin/users')
@admin_required
def get_admin_users():
    """Get users for admin dashboard with pagination and search"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)  # Show 5 users per page
        search_email = request.args.get('search_email', '').strip()
        
        # Build query
        query = User.query
        
        # Apply search filter if provided
        if search_email:
            query = query.filter(User.email.ilike(f'%{search_email}%'))
        
        # Get total count for pagination
        total_users = query.count()
        
        # Apply pagination
        users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'profile_image_url': get_profile_image_url(user.profile_image) if user.profile_image else None
            })
        
        # Calculate pagination info
        total_pages = (total_users + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return jsonify({
            'success': True,
            'users': users_data,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_users': total_users,
                'total_pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/update-user-role', methods=['POST'])
@admin_required
def update_user_role():
    """Update user role"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        role = data.get('role')
        
        if not user_id or not role:
            return jsonify({'success': False, 'error': 'User ID and role are required'}), 400
        
        if role not in ['admin', 'user', 'ff']:
            return jsonify({'success': False, 'error': 'Invalid role. Must be admin, user, or ff'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.role = role
        
        # If setting admin role, also set is_admin to true
        if role == 'admin':
            user.is_admin = True
        elif role != 'admin' and user.is_admin:
            # Only remove admin status if explicitly changing to non-admin role
            user.is_admin = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Updated user {user.username} to role: {role}'
        })
        
    except Exception as e:
        print(f"❌ Error updating user role: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/security-stats')
@admin_required
def get_security_stats():
    """Get security statistics for admin dashboard"""
    try:
        # Get security statistics
        security_stats = {
            'blocked_ips': list(security_middleware.bot_signatures['blocked_ips']),
            'suspicious_ips': list(security_middleware.bot_signatures['suspicious_ips']),
            'cloudflare_protection': True,  # Using Cloudflare bot protection
            'rate_limit_data': {
                ip: {
                    'requests_count': len(data['requests']),
                    'last_request': data['last_request']
                }
                for ip, data in security_middleware.rate_limit_db.items()
            }
        }
        
        return jsonify({
            'success': True,
            'security_stats': security_stats
        })
        
    except Exception as e:
        print(f"❌ Error getting security stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/unblock-ip', methods=['POST'])
@admin_required
def unblock_ip():
    """Unblock a previously blocked IP address"""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'IP address is required'}), 400
        
        # Remove from blocked IPs
        with security_middleware.lock:
            if ip_address in security_middleware.bot_signatures['blocked_ips']:
                security_middleware.bot_signatures['blocked_ips'].remove(ip_address)
                
        # Also remove from rate limit tracking
        if ip_address in security_middleware.rate_limit_db:
            del security_middleware.rate_limit_db[ip_address]
        
        return jsonify({
            'success': True,
            'message': f'IP address {ip_address} has been unblocked'
        })
        
    except Exception as e:
        print(f"❌ Error unblocking IP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# OpenRouter model configuration
OPENROUTER_MODEL = "@preset/ki-wellness"  # Use custom preset
FINE_TUNED_MODEL = "ki-wellness-mistral"  # Custom fine-tuned model

@app.route('/api/user-data-for-analysis')
@login_required
def get_user_data_for_analysis():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Start and end dates required'})
        
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get user profile
        user_profile = {
            'name': current_user.name,
            'age': current_user.age,
            'weight': current_user.weight,
            'height': current_user.height,
            'health_goals': current_user.health_goals,
            'ailments_concerns': current_user.ailments_concerns
        }
        
        # Get food logs
        food_logs = FoodLog.query.filter(
            FoodLog.user_id == current_user.id,
            FoodLog.date >= start_date,
            FoodLog.date <= end_date
        ).all()
        
        # Get water logs
        water_logs = WaterLog.query.filter(
            WaterLog.user_id == current_user.id,
            WaterLog.date >= start_date,
            WaterLog.date <= end_date
        ).all()
        
        # Get mood logs
        mood_logs = MoodLog.query.filter(
            MoodLog.user_id == current_user.id,
            MoodLog.date >= start_date,
            MoodLog.date <= end_date
        ).all()
        
        # Get notes
        notes = Note.query.filter(
            Note.user_id == current_user.id,
            Note.date >= start_date,
            Note.date <= end_date
        ).all()
        
        return jsonify({
            'success': True,
            'data': {
                'profile': user_profile,
                'food_logs': [{
                    'name': log.name,
                    'brand': log.brand,
                    'calories': log.calories,
                    'protein': log.protein,
                    'carbs': log.carbs,
                    'fat': log.fat,
                    'time_of_day': log.time_of_day,
                    'date': log.date.isoformat(),
                    'quantity': log.quantity
                } for log in food_logs],
                'water_logs': [{
                    'amount': log.amount,
                    'date': log.date.isoformat()
                } for log in water_logs],
                'mood_logs': [{
                    'mood': log.mood,
                    'date': log.date.isoformat()
                } for log in mood_logs],
                'notes': [{
                    'content': log.content,
                    'date': log.date.isoformat()
                } for log in notes]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get-stored-analysis')
@login_required
def get_stored_analysis():
    """Get stored analysis for the current user"""
    try:
        # Get stored analysis from database
        analysis_record = AIAnalysis.query.filter_by(user_id=current_user.id).first()
        
        if analysis_record:
            analysis_data = json.loads(analysis_record.analysis_data)
            updated_at = analysis_record.updated_at
            return jsonify({
                'success': True, 
                'analysis': analysis_data,
                'updated_at': updated_at.isoformat() if updated_at else None
            })
        else:
            # No stored analysis, generate fallback
            fallback_analysis = {
                "patterns": [
                    {"title": "Getting Started", "description": "Welcome to your AI Health Coach! Start logging your food, water, and mood to get personalized insights."}
                ],
                "suggestions": [
                    {"title": "Complete Your Profile", "description": "Add your health goals to your profile to get personalized suggestions."}
                ]
            }
            return jsonify({
                'success': True, 
                'analysis': fallback_analysis,
                'updated_at': None
            })
            
    except Exception as e:
        print(f"Error getting stored analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-ai-analysis', methods=['POST'])
@premium_required
def generate_ai_analysis():
    """Generate fresh analysis (for manual refresh)"""
    try:
        data = request.get_json()
        user_data = data.get('user_data')
        
        if not user_data:
            return jsonify({'success': False, 'error': 'No user data provided'})
        
        # Prepare comprehensive data for AI analysis
        profile = user_data.get('profile', {})
        food_logs = user_data.get('food_logs', [])
        water_logs = user_data.get('water_logs', [])
        mood_logs = user_data.get('mood_logs', [])
        notes = user_data.get('notes', [])
        
        # Calculate totals and averages
        total_calories = sum(log.get('calories', 0) for log in food_logs)
        avg_calories = total_calories / len(food_logs) if food_logs else 0
        total_water = sum(log.get('amount', 0) for log in water_logs)
        avg_water = total_water / len(water_logs) if water_logs else 0
        avg_mood = sum(log.get('mood', 3) for log in mood_logs) / len(mood_logs) if mood_logs else 3
        
        # Group food by time of day and get top foods
        food_by_time = {}
        for log in food_logs:
            time_of_day = log.get('time_of_day', 'snack')
            if time_of_day not in food_by_time:
                food_by_time[time_of_day] = []
            food_by_time[time_of_day].append(log)
        
        # Get most recent and frequent foods (limit to prevent token overflow)
        recent_foods = food_logs[-3:] if len(food_logs) > 3 else food_logs
        recent_notes = notes[-2:] if len(notes) > 2 else notes
        
        # Build recent activity strings safely to avoid deep f-string nesting
        recent_foods_list = [f"{log.get('name', 'Unknown')} ({log.get('time_of_day', 'snack')})" for log in recent_foods]
        recent_moods_list = [log.get('mood') for log in mood_logs[-2:]]
        recent_notes_list = [
            (note.get('content', '')[:80] + '...') if len(note.get('content', '') or '') > 80 else (note.get('content', '') or '')
            for note in recent_notes
        ]

        analysis_template = (
            """
        Health Coach Analysis - concise, evidence-based, grounded in local knowledge.

        USER: {user_name} | Age: {user_age} | Goals: {user_goals} | Health Concerns: {user_ailments}

        DATA SUMMARY (last 30 days):
        - Food: {food_count} entries, ~{avg_cal:.0f} kcal/day
        - Water: {water_count} entries, ~{avg_water:.1f} cups/day
        - Mood: {mood_count} entries, ~{avg_mood:.1f}/5
        - Notes: {notes_count} entries

        RECENT ACTIVITY:
        - Food (most recent): {recent_foods}
        - Mood (most recent): {recent_moods}
        - Notes (snippets): {recent_notes}

        TASK:
        - Find specific, data-backed patterns connecting mood & notes to food & water intake (e.g., low water -> lower mood next day, high sugar late at night -> poorer mood).
        - Provide short explanations for likely reasons behind how the user is feeling based on these links.
        - Create 2-3 actionable, personalized suggestions to try this week.
        - Ground suggestions in resources the model was trained on (nutrition, hydration, behavior change). Include brief source citations.

        OUTPUT STRICT JSON ONLY:
        {{
          "patterns": [
            {{"title": "Pattern Title", "description": "Brief description of the data-backed link (mood vs. notes, food, water)."}}
          ],
          "suggestions": [
            {{
              "title": "Suggestion Title",
              "description": "Brief, actionable advice tailored to the user's situation.",
              "sources": [
                {{"title": "Short Source Name", "url": "https://example.com"}}
              ]
            }}
          ]
        }}
        """
        )

        analysis_prompt = analysis_template.format(
            user_name=profile.get('name', 'User'),
            user_age=profile.get('age', 'N/A'),
            user_goals=profile.get('health_goals', 'Not specified'),
            user_ailments=profile.get('ailments_concerns', 'Not specified'),
            food_count=len(food_logs),
            avg_cal=avg_calories,
            water_count=len(water_logs),
            avg_water=avg_water,
            mood_count=len(mood_logs),
            avg_mood=avg_mood,
            notes_count=len(notes),
            recent_foods=json.dumps(recent_foods_list),
            recent_moods=json.dumps(recent_moods_list),
            recent_notes=json.dumps(recent_notes_list),
        )
        
        # Use OpenRouter for AI analysis
        try:
            client = get_openrouter_client()
            ai_response = client.generate_response(
                prompt=analysis_prompt,
                model=OPENROUTER_MODEL,
                max_tokens=800
            )
        except Exception as e:
            print(f"OpenRouter error: {e}")
            # Fallback response
            ai_response = json.dumps({
                "patterns": [
                    {"title": "Data Analysis", "description": "We're analyzing your wellness patterns. Keep logging to get more personalized insights!"}
                ],
                "suggestions": [
                    {"title": "Complete Your Profile", "description": "Add your health goals to your profile to get personalized suggestions."}
                ]
            })
        
        # Parse the JSON response
        try:
            analysis = json.loads(ai_response)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a fallback response
            analysis = {
                "patterns": [
                    {"title": "Data Analysis", "description": "We're analyzing your wellness patterns. Keep logging to get more personalized insights!"}
                ],
                "suggestions": [
                    {"title": "Complete Your Profile", "description": "Add your health goals to your profile to get personalized suggestions."}
                ]
            }
        
        # Save analysis to database
        try:
            # Check if user already has an analysis record
            existing_analysis = AIAnalysis.query.filter_by(user_id=current_user.id).first()
            
            if existing_analysis:
                # Update existing analysis
                existing_analysis.analysis_data = json.dumps(analysis)
                existing_analysis.updated_at = datetime.utcnow()
            else:
                # Create new analysis record
                new_analysis = AIAnalysis(
                    user_id=current_user.id,
                    analysis_data=json.dumps(analysis)
                )
                db.session.add(new_analysis)
            
            db.session.commit()
            print(f"✅ AI analysis saved for user {current_user.id}")
            
        except Exception as save_error:
            print(f"❌ Error saving analysis to database: {save_error}")
            # Continue even if save fails - analysis is still returned to user
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        print(f"AI Analysis Error: {str(e)}")  # Add debugging
        return jsonify({'success': False, 'error': str(e)})

def enhanced_ai_response(question: str, user_data: dict = None) -> str:
    """Generate enhanced AI response using OpenRouter API"""
    try:
        # Check if user has premium access (this function is called from other contexts)
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            if not current_user.has_premium_access():
                return "This feature requires a premium subscription. Upgrade now to access AI-powered wellness insights!"
        
        client = get_openrouter_client()
        return client.generate_response(
            prompt=question,
            model=OPENROUTER_MODEL,
            max_tokens=500
        )
    except Exception as e:
        print(f"❌ Error generating enhanced response: {e}")
        return "I apologize, but I encountered an error while processing your request."

@app.route('/api/test-openrouter')
@login_required
def test_openrouter():
    try:
        client = get_openrouter_client()
        response = client.generate_response(
            prompt="Say 'Hello, AI is working!'",
            model=OPENROUTER_MODEL
        )
        
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/warmup-openrouter')
@login_required
def warmup_openrouter():
    """Test OpenRouter API connection"""
    try:
        # Simple test call
        client = get_openrouter_client()
        response = client.generate_response(
            prompt="Hello",
            model=OPENROUTER_MODEL,
            max_tokens=10
        )
        return jsonify({'success': True, 'message': 'OpenRouter API is working', 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/user-summary')
@login_required
def get_user_summary():
    """Get summarized user data for AI chat (last 7 days)"""
    try:
        from datetime import timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Get user profile
        user_profile = {
            'id': current_user.id,
            'name': current_user.name,
            'age': current_user.age,
            'weight': current_user.weight,
            'height': current_user.height,
            'health_goals': current_user.health_goals,
            'ailments_concerns': current_user.ailments_concerns
        }
        
        # Get summarized food data
        food_logs = FoodLog.query.filter(
            FoodLog.user_id == current_user.id,
            FoodLog.date >= start_date,
            FoodLog.date <= end_date
        ).all()
        
        food_summary = {
            'total_entries': len(food_logs),
            'avg_calories': sum(log.calories for log in food_logs) / len(food_logs) if food_logs else 0,
            'total_calories': sum(log.calories for log in food_logs),
            'common_foods': _get_common_foods(food_logs),
            'recent_meals': [{
                'name': log.name,
                'calories': log.calories,
                'date': log.date.isoformat(),
                'time_of_day': log.time_of_day
            } for log in food_logs[-5:]]  # Last 5 meals
        }
        
        # Get summarized mood data
        mood_logs = MoodLog.query.filter(
            MoodLog.user_id == current_user.id,
            MoodLog.date >= start_date,
            MoodLog.date <= end_date
        ).all()
        
        mood_summary = {
            'total_entries': len(mood_logs),
            'avg_mood': sum(log.mood for log in mood_logs) / len(mood_logs) if mood_logs else 0,
            'mood_trend': _get_mood_trend(mood_logs),
            'recent_moods': [{
                'mood': log.mood,
                'date': log.date.isoformat()
            } for log in mood_logs[-5:]]
        }
        
        # Get summarized water data
        water_logs = WaterLog.query.filter(
            WaterLog.user_id == current_user.id,
            WaterLog.date >= start_date,
            WaterLog.date <= end_date
        ).all()
        
        water_summary = {
            'total_entries': len(water_logs),
            'total_water': sum(log.amount for log in water_logs),
            'avg_daily_water': sum(log.amount for log in water_logs) / 7 if water_logs else 0,
            'recent_water': [{
                'amount': log.amount,
                'date': log.date.isoformat()
            } for log in water_logs[-5:]]
        }
        
        # Get recent patterns from stored analysis
        recent_patterns = []
        analysis_record = AIAnalysis.query.filter_by(user_id=current_user.id).first()
        if analysis_record:
            analysis_data = json.loads(analysis_record.analysis_data)
            recent_patterns = analysis_data.get('patterns', [])[:3]  # Top 3 patterns
        
        return jsonify({
            'success': True,
            'summary': {
                'profile': user_profile,
                'food_summary': food_summary,
                'mood_summary': mood_summary,
                'water_summary': water_summary,
                'recent_patterns': recent_patterns
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai-chat', methods=['POST'])
@premium_required
@rate_limit(max_requests=30, window=60)  # Limit AI chat requests
def ai_chat():
    try:
        # Check AI usage limits before processing request
        limits_ok, limit_message = check_ai_usage_limits(current_user.id)
        if not limits_ok:
            return jsonify({
                'success': False, 
                'error': f'AI usage limit exceeded: {limit_message}',
                'limit_exceeded': True
            }), 429  # Too Many Requests
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
            
        message = data.get('message', '').strip()
        context = data.get('context', {})
        context_type = data.get('context_type', 'minimal')
        chat_history = data.get('chat_history', [])
        
        # Input validation and sanitization
        if not validate_user_input(message, max_length=1000):
            return jsonify({'success': False, 'error': 'Invalid message format'}), 400
            
        if not validate_user_input(context_type, max_length=50):
            return jsonify({'success': False, 'error': 'Invalid context type'}), 400
            
        # Validate chat history structure separately (list of dict objects with role/content)
        if chat_history is not None:
            if not isinstance(chat_history, list):
                return jsonify({'success': False, 'error': 'Invalid chat history format - must be a list'}), 400
            
            # Limit the number of history items and validate each
            if len(chat_history) > 10:  # Reasonable limit for chat history
                return jsonify({'success': False, 'error': 'Too many chat history items'}), 400
                
            for i, item in enumerate(chat_history):
                if not isinstance(item, dict):
                    return jsonify({'success': False, 'error': f'Invalid chat history item {i} - must be a dict'}), 400
                
                role = item.get('role', '')
                content = item.get('content', '')
                
                if role not in ['user', 'assistant']:
                    return jsonify({'success': False, 'error': f'Invalid chat history role in item {i}'}), 400
                    
                if not validate_user_input(content, max_length=2000):  # Allow longer content for chat history
                    return jsonify({'success': False, 'error': f'Invalid chat history content in item {i}'}), 400
        
        # Sanitize inputs
        message = sanitize_user_input(message, max_length=1000)
        context_type = sanitize_user_input(context_type, max_length=50)
        
        # Sanitize chat history content while preserving structure
        if chat_history:
            for item in chat_history:
                if isinstance(item, dict) and 'content' in item:
                    item['content'] = sanitize_user_input(item['content'], max_length=2000)
        
        print(f"AI Chat Request - Message: {message}")
        print(f"AI Chat Request - Context Type: {context_type}")
        print(f"AI Chat Request - Context Keys: {list(context.keys()) if context else 'None'}")
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'})
        
        # Create optimized prompt based on context type
        try:
            prompt = _create_optimized_prompt(message, context, context_type, chat_history)
            print(f"AI Chat - Prompt length: {len(prompt)} characters")
        except Exception as prompt_error:
            print(f"AI Chat - Prompt creation error: {str(prompt_error)}")
            return jsonify({'success': False, 'error': f'Prompt creation failed: {str(prompt_error)}'})
        
        # Call OpenRouter API with timeout
        try:
            start_time = datetime.now()
            client = get_openrouter_client()
            ai_response = client.generate_response(
                prompt=prompt,
                model=OPENROUTER_MODEL,
                max_tokens=500
            )
            
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            print(f"AI Chat - Response received, length: {len(ai_response)} characters")
            
            # Log AI usage for analytics (if we have usage data)
            try:
                # Estimate token counts (OpenRouter doesn't always return usage info)
                estimated_input_tokens = len(prompt.split()) * 1.3  # Rough estimate
                estimated_output_tokens = len(ai_response.split()) * 1.3
                
                # Get model pricing for cost calculation
                model_pricing = client.get_model_pricing(OPENROUTER_MODEL)
                input_cost = (estimated_input_tokens / 1000000) * model_pricing.get('input', 0.20)
                output_cost = (estimated_output_tokens / 1000000) * model_pricing.get('output', 0.80)
                
                # Safety check: ensure costs are finite values
                if not (isinstance(input_cost, (int, float)) and input_cost != float('inf') and input_cost != float('-inf')):
                    input_cost = 0.0
                if not (isinstance(output_cost, (int, float)) and output_cost != float('inf') and output_cost != float('-inf')):
                    output_cost = 0.0
                
                analytics_service.log_ai_usage(
                    user_id=current_user.id,
                    model_used=OPENROUTER_MODEL,
                    input_tokens=int(estimated_input_tokens),
                    output_tokens=int(estimated_output_tokens),
                    input_cost=input_cost,
                    output_cost=output_cost,
                    endpoint='/api/ai-chat',
                    response_time_ms=response_time_ms,
                    success=True
                )
            except Exception as log_error:
                print(f"⚠️ Could not log AI usage: {log_error}")
            
            return jsonify({'success': True, 'response': ai_response})
            
        except Exception as openrouter_error:
            print(f"AI Chat - OpenRouter error: {str(openrouter_error)}")
            
            # Log failed usage attempt
            try:
                analytics_service.log_ai_usage(
                    user_id=current_user.id,
                    model_used=OPENROUTER_MODEL,
                    input_tokens=len(prompt.split()),
                    output_tokens=0,
                    input_cost=0,
                    output_cost=0,
                    endpoint='/api/ai-chat',
                    response_time_ms=0,
                    success=False,
                    error_message=str(openrouter_error)
                )
            except Exception as log_error:
                print(f"⚠️ Could not log failed AI usage: {log_error}")
            
            # Provide a helpful fallback response when OpenRouter is not available
            fallback_response = _get_fallback_response(message, context_type)
            return jsonify({
                'success': True, 
                'response': fallback_response,
                'note': 'Using fallback response - AI model temporarily unavailable'
            })
        
    except Exception as e:
        print(f"AI Chat - General error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def _create_optimized_prompt(message, context, context_type, chat_history):
    """Create an optimized prompt based on context type"""
    
    # Safely get context values with error handling
    try:
        profile = context.get('profile', {}) if context else {}
        profile_name = profile.get('name', 'User') if profile else 'User'
    except Exception as e:
        print(f"Error extracting profile data: {e}")
        profile_name = 'User'
    
    # Start with a concise base prompt
    base_prompt = f"AI Health Coach for {profile_name}. Keep responses short and actionable.\n\nQ: {message}\n\n"
    
    # Add only essential context based on the specific question
    relevant_context = _extract_relevant_context(message, context, context_type)
    if relevant_context and len(relevant_context) < 100:  # Only add if context is concise
        base_prompt += f"Context: {relevant_context}\n"
        print(f"Extracted relevant context: {relevant_context}")
    
    # Add only 1-2 most relevant resources to save space
    resources = get_relevant_resources(context_type, _determine_topic(message))
    if resources:
        # Limit to 2 most relevant resources
        limited_resources = resources[:2]
        base_prompt += format_resources_for_prompt(limited_resources)
        print(f"Added {len(limited_resources)} relevant resources")
    
    base_prompt += """Provide a short, helpful response (max 2-3 sentences) with relevant links. Format:
    
    [Your helpful response here]
    
    📚 Resources:
    - [Link 1: Brief description]
    - [Link 2: Brief description]
    
    Include Medium blog (kiwellness.medium.com) when relevant."""
    
    # Proactive prompt size management
    if len(base_prompt) > 800:  # Lower threshold for better optimization
        print(f"Prompt too large ({len(base_prompt)} chars), optimizing...")
        # Create ultra-concise version
        base_prompt = f"AI Health Coach for {profile_name}. Q: {message}\n\nProvide short, helpful response with relevant links. Include Medium blog when relevant."
    
    print(f"Final prompt length: {len(base_prompt)} characters")
    return base_prompt

def _determine_topic(message):
    """Determine the specific topic of the user's question for resource matching"""
    
    message_lower = message.lower()
    
    # Nutrition topics
    if any(word in message_lower for word in ['energy', 'energizing', 'boost', 'power', 'fuel']):
        return 'nutrition'
    elif any(word in message_lower for word in ['calorie', 'calories', 'weight', 'diet', 'meal', 'eating', 'food']):
        return 'nutrition'
    
    # Mood topics
    elif any(word in message_lower for word in ['mood', 'feel', 'emotion', 'happy', 'sad', 'stress', 'anxiety', 'depression']):
        return 'mood'
    
    # Hydration topics
    elif any(word in message_lower for word in ['water', 'hydrate', 'drink', 'fluid', 'dehydrated']):
        return 'hydration'
    
    # Exercise topics
    elif any(word in message_lower for word in ['exercise', 'workout', 'fitness', 'activity', 'training']):
        return 'exercise'
    
    # General wellness
    elif any(word in message_lower for word in ['health', 'wellness', 'habit', 'lifestyle', 'goal']):
        return 'wellness'
    
    # Default to general
    return 'general'

def _get_fallback_response(message, context_type):
    """Provide helpful fallback responses when AI model is unavailable"""
    
    message_lower = message.lower()
    
    # Anti-inflammation responses
    if any(word in message_lower for word in ['anti-inflammation', 'anti-inflammatory', 'inflammation']):
        return """For anti-inflammatory meals, focus on foods rich in omega-3s, antioxidants, and fiber. Try a salmon salad with leafy greens, berries, and walnuts, or a turmeric-spiced lentil soup with ginger.

📚 Helpful Resources:
- [Anti-Inflammatory Diet Guide](https://kiwellness.medium.com/anti-inflammatory-foods) - Ki Wellness blog
- [Mayo Clinic: Anti-inflammatory diet](https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/anti-inflammatory-diet/art-20457586) - Medical guidance"""
    
    # Energy and nutrition
    elif any(word in message_lower for word in ['energy', 'energizing', 'boost', 'meal', 'food', 'nutrition']):
        return """For sustained energy, combine complex carbs with protein and healthy fats. Try oatmeal with nuts and berries, or a quinoa bowl with vegetables and lean protein.

📚 Helpful Resources:
- [Energy-Boosting Foods](https://kiwellness.medium.com/energy-foods) - Ki Wellness blog
- [Harvard Health: Foods that fight fatigue](https://www.health.harvard.edu/healthbeat/foods-that-fight-fatigue) - Expert advice"""
    
    # Water and hydration
    elif any(word in message_lower for word in ['water', 'hydrate', 'drink']):
        return """Stay hydrated by drinking water throughout the day. Aim for 8-10 glasses daily, and include hydrating foods like cucumbers, watermelon, and citrus fruits.

📚 Helpful Resources:
- [Hydration Tips](https://kiwellness.medium.com/hydration-guide) - Ki Wellness blog
- [WebMD: How much water should you drink?](https://www.webmd.com/diet/how-much-water-to-drink) - Daily recommendations"""
    
    # Mood and wellness
    elif any(word in message_lower for word in ['mood', 'feel', 'stress', 'anxiety', 'wellness']):
        return """Support your mood with regular exercise, adequate sleep, and mood-boosting foods like dark chocolate, fatty fish, and leafy greens. Practice stress management techniques daily.

📚 Helpful Resources:
- [Mood-Boosting Habits](https://kiwellness.medium.com/mood-wellness) - Ki Wellness blog
- [Mayo Clinic: Stress management](https://www.mayoclinic.org/healthy-lifestyle/stress-management) - Expert guidance"""
    
    # General health
    else:
        return """I'm here to support your wellness journey! For personalized guidance, try logging your meals, water intake, and mood regularly. This helps identify patterns and make informed health decisions.

📚 Helpful Resources:
- [Wellness Tips](https://kiwellness.medium.com/wellness-guide) - Ki Wellness blog
- [Personalized Health Coaching](https://kiwellness.org/human-help) - Book a session with our certified nutritionist"""

def _extract_relevant_context(message, context, context_type):
    """Extract only context that's relevant to the user's specific question"""
    
    message_lower = message.lower()
    relevant_parts = []
    
    try:
        # Food-related questions
        if context_type == 'food' and context.get('food_summary'):
            food_data = context['food_summary']
            
            # Check for specific food-related keywords
            if any(word in message_lower for word in ['energy', 'energizing', 'boost', 'power']):
                # For energy questions, focus on calorie intake and meal frequency
                relevant_parts.append(f"Logged {food_data.get('total_entries', 0)} meals")
                if food_data.get('avg_calories', 0) > 0:
                    relevant_parts.append(f"avg {food_data.get('avg_calories', 0):.0f} cal/meal")
                    
            elif any(word in message_lower for word in ['calorie', 'calories', 'weight', 'diet']):
                # For calorie/weight questions, focus on total calories
                total_cals = food_data.get('total_calories', 0)
                relevant_parts.append(f"Total calories: {total_cals:.0f}")
                if food_data.get('avg_calories', 0) > 0:
                    relevant_parts.append(f"avg {food_data.get('avg_calories', 0):.0f} cal/meal")
                    
            elif any(word in message_lower for word in ['meal', 'eating', 'food', 'nutrition']):
                # For general food questions, provide basic summary
                relevant_parts.append(f"Logged {food_data.get('total_entries', 0)} meals")
                if food_data.get('common_foods'):
                    common_foods = food_data.get('common_foods', [])[:3]
                    relevant_parts.append(f"common foods: {', '.join(common_foods)}")
                    
            else:
                # Default food context - keep it concise
                relevant_parts.append(f"Logged {food_data.get('total_entries', 0)} meals")
                if food_data.get('avg_calories', 0) > 0:
                    relevant_parts.append(f"avg {food_data.get('avg_calories', 0):.0f} cal/meal")
        
        # Mood-related questions
        elif context_type == 'mood' and context.get('mood_summary'):
            mood_data = context['mood_summary']
            
            if any(word in message_lower for word in ['trend', 'pattern', 'improving', 'declining']):
                # For trend questions, focus on mood trend
                relevant_parts.append(f"Mood trend: {mood_data.get('mood_trend', 'stable')}")
                if mood_data.get('avg_mood', 0) > 0:
                    relevant_parts.append(f"avg {mood_data.get('avg_mood', 0):.1f}/10")
                    
            elif any(word in message_lower for word in ['happy', 'sad', 'stress', 'anxiety', 'depression']):
                # For emotional state questions, focus on current mood
                if mood_data.get('avg_mood', 0) > 0:
                    relevant_parts.append(f"Current avg mood: {mood_data.get('avg_mood', 0):.1f}/10")
                if mood_data.get('mood_trend', 'stable') != 'stable':
                    relevant_parts.append(f"trend: {mood_data.get('mood_trend', 'stable')}")
                    
            else:
                # Default mood context
                if mood_data.get('avg_mood', 0) > 0:
                    relevant_parts.append(f"Avg mood: {mood_data.get('avg_mood', 0):.1f}/10")
        
        # Water-related questions
        elif context_type == 'water' and context.get('water_summary'):
            water_data = context['water_summary']
            
            if any(word in message_lower for word in ['enough', 'adequate', 'sufficient', 'dehydrated']):
                # For hydration adequacy questions, compare to recommended intake
                avg_daily = water_data.get('avg_daily_water', 0)
                relevant_parts.append(f"Daily avg: {avg_daily:.0f}ml")
                if avg_daily < 2000:
                    relevant_parts.append("(below 2000ml)")
                elif avg_daily > 3000:
                    relevant_parts.append("(above 3000ml)")
                    
            elif any(word in message_lower for word in ['increase', 'more', 'boost']):
                # For increasing water intake
                current_avg = water_data.get('avg_daily_water', 0)
                relevant_parts.append(f"Daily avg: {current_avg:.0f}ml")
                
            else:
                # Default water context - keep concise
                relevant_parts.append(f"Daily avg: {water_data.get('avg_daily_water', 0):.0f}ml")
        
        # Analysis/pattern questions
        elif context_type == 'analysis' and context.get('recent_patterns'):
            recent_patterns = context.get('recent_patterns', [])
            
            if any(word in message_lower for word in ['pattern', 'trend', 'insight', 'analysis']):
                if recent_patterns:
                    # Extract key insights from patterns
                    pattern_titles = [p.get('title', '') for p in recent_patterns[:2]]
                    relevant_parts.append(f"Key patterns: {', '.join(pattern_titles)}")
                else:
                    relevant_parts.append("No recent patterns identified")
        
        # Health goals context (for any question)
        if context.get('profile', {}).get('health_goals'):
            goals = context['profile']['health_goals']
            if any(word in message_lower for word in ['goal', 'target', 'objective', 'aim']):
                relevant_parts.append(f"Health goals: {goals}")
        
        # Ailments/concerns context (for health-related questions)
        if context.get('profile', {}).get('ailments_concerns'):
            ailments = context['profile']['ailments_concerns']
            # More specific keywords to avoid conflicts with health goals
            if any(word in message_lower for word in ['condition', 'ailment', 'concern', 'medical', 'symptom', 'issue', 'diabetes', 'blood pressure', 'pressure', 'disease', 'chronic', 'manage', 'management', 'avoid', 'safe', 'affect']):
                relevant_parts.append(f"Health concerns: {ailments}")
        
        # Age context (for age-specific advice)
        if context.get('profile', {}).get('age'):
            age = context['profile']['age']
            if any(word in message_lower for word in ['age', 'older', 'younger', 'senior', 'teen']):
                relevant_parts.append(f"Age: {age}")
        
    except Exception as e:
        print(f"Error extracting relevant context: {e}")
        return None
    
    return '; '.join(relevant_parts) if relevant_parts else None

def _get_common_foods(food_logs):
    """Get most common foods from logs"""
    food_counts = {}
    for log in food_logs:
        food_name = log.name.lower()
        food_counts[food_name] = food_counts.get(food_name, 0) + 1
    
    return [food for food, count in sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

def _get_mood_trend(mood_logs):
    """Determine mood trend from recent logs"""
    if len(mood_logs) < 2:
        return 'insufficient_data'
    
    recent_moods = [log.mood for log in mood_logs[-3:]]
    if len(recent_moods) >= 2:
        if recent_moods[-1] > recent_moods[0]:
            return 'improving'
        elif recent_moods[-1] < recent_moods[0]:
            return 'declining'
        else:
            return 'stable'
    return 'stable'

import asyncio
import concurrent.futures
from functools import lru_cache
import time

# Simple in-memory cache for food search results
food_search_cache = {}
CACHE_DURATION = 300  # 5 minutes
MAX_CACHE_SIZE = 100  # Maximum number of cached items

def cleanup_cache():
    """Clean up old cache entries to prevent memory issues"""
    global food_search_cache
    current_time = time.time()
    expired_keys = []
    
    for key, (_, cache_time) in food_search_cache.items():
        if current_time - cache_time > CACHE_DURATION:
            expired_keys.append(key)
    
    for key in expired_keys:
        del food_search_cache[key]
    
    # If cache is still too large, remove oldest entries
    if len(food_search_cache) > MAX_CACHE_SIZE:
        sorted_items = sorted(food_search_cache.items(), key=lambda x: x[1][1])
        items_to_remove = len(food_search_cache) - MAX_CACHE_SIZE
        for i in range(items_to_remove):
            del food_search_cache[sorted_items[i][0]]

def rank_food_search_results(results, query):
    """
    Rank food search results by match quality, prioritizing exact matches
    Returns results sorted by relevance (best matches first)
    """
    if not results or not query:
        return results
    
    query_lower = query.lower().strip()
    ranked_results = []
    
    for result in results:
        name = result.get('name', '').lower().strip()
        brand = result.get('brand', '').lower().strip()
        
        # Calculate match score (higher = better match)
        score = 0
        
        # Exact name match (highest priority)
        if name == query_lower:
            score += 1000
        # Exact match ignoring articles (a, an, the)
        elif name.replace('the ', '').replace('an ', '').replace('a ', '') == query_lower:
            score += 950
        # Exact match with commas/parentheses (e.g., "apple" matches "apple, red")
        elif name.split(',')[0].strip() == query_lower or name.split('(')[0].strip() == query_lower:
            score += 920
        # Name starts with query (very high priority)
        elif name.startswith(query_lower):
            score += 800
        # Query is whole word in name
        elif f' {query_lower} ' in f' {name} ' or name.startswith(f'{query_lower} ') or name.endswith(f' {query_lower}'):
            score += 700
        # Name contains query as substring (high priority)
        elif query_lower in name:
            score += 500
        
        # Handle plurals and common variations
        query_singular = query_lower.rstrip('s') if query_lower.endswith('s') and len(query_lower) > 3 else query_lower
        query_plural = query_lower + 's' if not query_lower.endswith('s') else query_lower
        
        # Check singular/plural variations
        if query_singular != query_lower and name == query_singular:
            score += 980  # High score for singular match
        elif query_plural != query_lower and name == query_plural:
            score += 980  # High score for plural match
        
        # Brand exact match bonus
        if brand and brand == query_lower:
            score += 300
        elif brand and query_lower in brand:
            score += 100
        
        # Penalize very long names (they're often less relevant)
        if len(name) > 50:
            score -= 50
        elif len(name) > 30:
            score -= 20
        
        # Bonus for simple/common foods (shorter names often more relevant)
        if len(name) <= 15:
            score += 50
        
        # Bonus for foods with nutritional data
        if result.get('calories', 0) > 0:
            score += 25
        
        # Store the score in the result
        result_with_score = result.copy()
        result_with_score['match_score'] = score
        ranked_results.append(result_with_score)
    
    # Sort by score (descending - highest scores first)
    ranked_results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    # Optional: Log ranking information for debugging (uncomment if needed)
    # if ranked_results:
    #     print(f"🔍 Search ranking for '{query}': Top 3 results:")
    #     for i, result in enumerate(ranked_results[:3]):
    #         score = result.get('match_score', 0)
    #         name = result.get('name', 'Unknown')
    #         print(f"  {i+1}. {name} (score: {score})")
    
    # Remove the temporary score field
    for result in ranked_results:
        result.pop('match_score', None)
    
    return ranked_results

@app.route('/api/search-food', methods=['POST'])
@login_required
def search_food():
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'message': 'Query is required'})
    
    # Clean up cache periodically
    if len(food_search_cache) > MAX_CACHE_SIZE * 0.8:  # Clean when 80% full
        cleanup_cache()
    
    # Check cache first
    cache_key = query.lower()
    current_time = time.time()
    if cache_key in food_search_cache:
        cached_result, cache_time = food_search_cache[cache_key]
        if current_time - cache_time < CACHE_DURATION:
            return jsonify({'success': True, 'results': cached_result, 'cached': True})
    
    # Check fallback database first for exact matches (instant)
    fallback_results = []
    exact_matches = []
    partial_matches = []
    query_lower = query.lower()
    
    for food_key, food_data in COMMON_FOODS_DB.items():
        if query_lower == food_key.lower():
            # Exact match - highest priority
            exact_matches.append(food_data)
        elif query_lower in food_key.lower() or food_key.lower() in query_lower:
            # Partial match - lower priority
            partial_matches.append(food_data)
    
    # Combine results with exact matches first
    fallback_results = exact_matches + partial_matches
    
    # If we have good fallback results, rank them and return immediately
    if len(fallback_results) >= 3:
        ranked_fallback = rank_food_search_results(fallback_results, query)
        result = ranked_fallback[:8]
        food_search_cache[cache_key] = (result, current_time)
        return jsonify({'success': True, 'results': result, 'fast': True, 'exact_matches': len(exact_matches)})
    
    # Determine if this is a basic food
    is_basic_food = any(basic_food in query.lower() for basic_food in BASIC_FOODS)
    
    # Run API searches in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        
        # Submit USDA search if applicable
        if is_basic_food and USDA_API_KEY:
            futures['usda'] = executor.submit(search_usda_api, query)
        
        # Submit Open Food Facts search
        futures['openfoodfacts'] = executor.submit(search_openfoodfacts_api, query)
        
        # Collect results as they complete
        usda_results = []
        openfoodfacts_results = []
        
        for name, future in futures.items():
            try:
                result = future.result(timeout=3)  # 3 second timeout per API
                if name == 'usda':
                    usda_results = result
                elif name == 'openfoodfacts':
                    openfoodfacts_results = result
            except concurrent.futures.TimeoutError:
                print(f"Timeout for {name} API")
            except Exception as e:
                print(f"Error in {name} API: {e}")
    
    # Combine all results for ranking
    all_results = fallback_results + usda_results + openfoodfacts_results
    
    # Rank results by match quality (exact matches first)
    ranked_results = rank_food_search_results(all_results, query)
    
    # Remove duplicates while preserving ranking
    unique_results = []
    seen_names = set()
    
    for result in ranked_results:
        # Use normalized name for duplicate detection
        normalized_name = result['name'].lower().strip()
        if normalized_name not in seen_names:
            unique_results.append(result)
            seen_names.add(normalized_name)
    
    final_results = unique_results[:8]
    
    # Cache the results
    food_search_cache[cache_key] = (final_results, current_time)
    
    return jsonify({
        'success': True,
        'results': final_results,
        'cached': False
    })

@app.route('/api/search-food-barcode', methods=['POST'])
@login_required
def search_food_barcode():
    """Search for food by barcode"""
    data = request.get_json()
    barcode = data.get('barcode', '').strip()
    
    if not barcode:
        return jsonify({'success': False, 'message': 'Barcode is required'})
    
    try:
        # Clean and validate barcode
        if not barcode or len(barcode) < 8:
            return jsonify({'success': False, 'message': 'Invalid barcode format'})
        
        # Use the newer API endpoint for better reliability
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}"
        headers = {
            'User-Agent': 'KiWellness/1.0 (https://kiwellness.org)',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        api_data = response.json()
        
        if api_data.get('status') == 1 and api_data.get('product'):
            product = api_data['product']
            nutriments = product.get('nutriments', {})
            
            result = {
                'name': product.get('product_name', 'Unknown Product'),
                'brand': product.get('brands', ''),
                'calories': int(nutriments.get('energy-kcal_100g', 0)),
                'protein': round(nutriments.get('proteins_100g', 0), 1),
                'carbs': round(nutriments.get('carbohydrates_100g', 0), 1),
                'fat': round(nutriments.get('fat_100g', 0), 1),
                'fiber': round(nutriments.get('fiber_100g', 0), 1),
                'sugar': round(nutriments.get('sugars_100g', 0), 1),
                'sodium': round(nutriments.get('sodium_100g', 0), 1),
                'serving_size': 100,
                'serving_unit': 'g'
            }
            
            return jsonify({'success': True, 'result': result})
        else:
            return jsonify({'success': False, 'message': 'Product not found'})
            
    except Exception as e:
        print(f"Barcode search error: {e}")
        return jsonify({'success': False, 'message': 'Failed to search product'})

@app.route('/api/add-product-to-off', methods=['POST'])
@login_required
def add_product_to_open_food_facts():
    """Add a new product to Open Food Facts database"""
    try:
        # Get form data
        barcode = request.form.get('barcode', '').strip()
        product_name = request.form.get('product_name', '').strip()
        
        # Validate required fields
        if not product_name:
            return jsonify({'success': False, 'message': 'Product name is required'})
        
        # Prepare data for Open Food Facts API
        form_data = {
            'user_id': 'kiwellness-app',  # Our app's username
            'password': os.environ.get('OPENFOODFACTS_PASSWORD', ''),  # Set this in environment
            'product_name': product_name,
        }
        
        # Add barcode if provided
        if barcode:
            form_data['code'] = barcode
        
        # Add optional fields if provided
        optional_fields = {
            'brands': request.form.get('brands'),
            'categories': request.form.get('categories'),
            'quantity': request.form.get('quantity'),
            'ingredients_text': request.form.get('ingredients_text'),
        }
        
        for field, value in optional_fields.items():
            if value and value.strip():
                form_data[field] = value.strip()
        
        # Add nutrition facts if provided
        nutrition_fields = {
            'nutrition_data_per': '100g',
            'nutrition_data_prepared_per': '100g',
        }
        
        nutrition_mapping = {
            'nutrition_energy_kcal': 'energy-kcal',
            'nutrition_proteins': 'proteins',
            'nutrition_carbohydrates': 'carbohydrates', 
            'nutrition_fat': 'fat',
            'nutrition_fiber': 'fiber',
            'nutrition_sugars': 'sugars'
        }
        
        for form_field, off_field in nutrition_mapping.items():
            value = request.form.get(form_field)
            if value and value.strip():
                try:
                    # Convert to float and add to form data
                    float_value = float(value)
                    form_data[f'nutriment_{off_field}'] = str(float_value)
                    form_data[f'nutriment_{off_field}_unit'] = 'g' if off_field != 'energy-kcal' else 'kcal'
                except ValueError:
                    pass  # Skip invalid nutrition values
        
        # Handle image uploads
        files = {}
        uploaded_files = request.files.getlist('images')
        
        for i, file in enumerate(uploaded_files):
            if file and file.filename:
                # Determine image type based on order
                if i == 0:
                    field_name = 'imgupload_front'
                elif i == 1:
                    field_name = 'imgupload_ingredients'
                elif i == 2:
                    field_name = 'imgupload_nutrition'
                else:
                    field_name = f'imgupload_other_{i}'
                
                files[field_name] = (file.filename, file.stream, file.content_type)
        
        # Submit to Open Food Facts
        url = 'https://world.openfoodfacts.org/cgi/product_jqm2.pl'
        headers = {
            'User-Agent': 'KiWellness/1.0 (https://kiwellness.org; contact@kiwellness.org)'
        }
        
        response = requests.post(url, data=form_data, files=files, headers=headers, timeout=30)
        
        # Check if submission was successful
        if response.status_code == 200:
            # Open Food Facts doesn't always return clear success indicators
            # We'll assume success if we get a 200 response
            return jsonify({
                'success': True, 
                'message': 'Product successfully added to Open Food Facts database!'
            })
        else:
            return jsonify({
                'success': False, 
                'message': f'Failed to add product (HTTP {response.status_code})'
            })
            
    except Exception as e:
        print(f"Error adding product to Open Food Facts: {e}")
        return jsonify({
            'success': False, 
            'message': 'Network error occurred while adding product'
        })

@app.route('/api/product/<barcode>')
@login_required
def get_product(barcode):
    """Get product information from Open Food Facts API"""
    try:
        # Clean and validate barcode
        barcode = str(barcode).strip()
        if not barcode or len(barcode) < 8:
            return jsonify({'success': False, 'message': 'Invalid barcode format'})
        
        # Use the newer API endpoint for better reliability
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}"
        headers = {
            'User-Agent': 'KiWellness/1.0 (https://kiwellness.org)',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 1 and data.get('product'):
            product = data['product']
            nutriments = product.get('nutriments', {})
            
            # Extract product information with fallbacks
            result = {
                'name': product.get('product_name') or product.get('generic_name') or 'Unknown Product',
                'brand': product.get('brands') or product.get('brand_owner') or 'Unknown Brand',
                'calories': float(nutriments.get('energy-kcal_100g', 0) or 0),
                'protein': float(nutriments.get('proteins_100g', 0) or 0),
                'carbs': float(nutriments.get('carbohydrates_100g', 0) or 0),
                'fat': float(nutriments.get('fat_100g', 0) or 0),
                'fiber': float(nutriments.get('fiber_100g', 0) or 0),
                'sugar': float(nutriments.get('sugars_100g', 0) or 0),
                'sodium': float(nutriments.get('sodium_100g', 0) or 0),
                'source': 'openfoodfacts',
                'barcode': barcode,
                'image_url': product.get('image_front_url') or product.get('image_url'),
                'ingredients': product.get('ingredients_text'),
                'allergens': product.get('allergens_tags', []),
                'nutrition_grade': product.get('nutrition_grade_fr') or product.get('nutrition_grade'),
                'nova_group': product.get('nova_group'),
                'ecoscore_grade': product.get('ecoscore_grade')
            }
            
            # Validate that we have at least basic nutritional info
            if result['calories'] == 0 and result['protein'] == 0 and result['carbs'] == 0 and result['fat'] == 0:
                return jsonify({
                    'success': False, 
                    'message': 'Product found but no nutritional information available',
                    'product_name': result['name'],
                    'barcode': barcode
                })
            
            return jsonify({'success': True, 'product': result})
        else:
            # Try alternative API endpoint for better coverage
            alt_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
            alt_response = requests.get(alt_url, headers=headers, timeout=15)
            
            if alt_response.status_code == 200:
                alt_data = alt_response.json()
                if alt_data.get('status') == 1 and alt_data.get('product'):
                    product = alt_data['product']
                    nutriments = product.get('nutriments', {})
                    
                    result = {
                        'name': product.get('product_name') or product.get('generic_name') or 'Unknown Product',
                        'brand': product.get('brands') or 'Unknown Brand',
                        'calories': float(nutriments.get('energy-kcal_100g', 0) or 0),
                        'protein': float(nutriments.get('proteins_100g', 0) or 0),
                        'carbs': float(nutriments.get('carbohydrates_100g', 0) or 0),
                        'fat': float(nutriments.get('fat_100g', 0) or 0),
                        'fiber': float(nutriments.get('fiber_100g', 0) or 0),
                        'sugar': float(nutriments.get('sugars_100g', 0) or 0),
                        'sodium': float(nutriments.get('sodium_100g', 0) or 0),
                        'source': 'openfoodfacts_alt',
                        'barcode': barcode
                    }
                    
                    if result['calories'] > 0 or result['protein'] > 0 or result['carbs'] > 0 or result['fat'] > 0:
                        return jsonify({'success': True, 'product': result})
            
            return jsonify({
                'success': False, 
                'message': 'Product not found in database',
                'barcode': barcode,
                'suggestion': 'Try searching manually or check the barcode number'
            })
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'Request timeout - please try again'})
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'Network error: {str(e)}'})
    except Exception as e:
        print(f"Error fetching product {barcode}: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch product information'})

@app.route('/api/food-log', methods=['POST'])
@login_required
def add_food_log():
    data = request.get_json()
    
    food_log = FoodLog(
        user_id=current_user.id,
        name=data['name'],
        brand=data.get('brand', ''),
        calories=data['calories'],
        protein=data['protein'],
        carbs=data['carbs'],
        fat=data['fat'],
        fiber=data.get('fiber', 0),
        sugar=data.get('sugar', 0),
        sodium=data.get('sodium', 0),
        serving_size=data['serving_size'],
        original_amount=data['original_amount'],
        original_unit=data['original_unit'],
        quantity=data['quantity'],
        time_of_day=data.get('time_of_day', 'snack'),
        date=datetime.strptime(data['date'], '%Y-%m-%d').date()
    )
    
    db.session.add(food_log)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/water-log', methods=['POST'])
@login_required
def add_water_log():
    data = request.get_json()
    
    water_log = WaterLog(
        user_id=current_user.id,
        amount=data['amount'],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date()
    )
    
    db.session.add(water_log)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/mood-log', methods=['POST'])
@login_required
def add_mood_log():
    data = request.get_json()
    
    mood_log = MoodLog(
        user_id=current_user.id,
        mood=data['mood'],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date()
    )
    
    db.session.add(mood_log)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/notes', methods=['POST'])
@login_required
def save_notes():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'content' not in data or 'date' not in data:
            return jsonify({'success': False, 'error': 'Missing required fields: content and date'}), 400
        
        # Parse and validate date
        try:
            note_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Validate content is not empty
        if not data['content'].strip():
            return jsonify({'success': False, 'error': 'Note content cannot be empty'}), 400
        
        # Create new note entry
        note = Note(
            user_id=current_user.id,
            content=data['content'].strip(),
            date=note_date,
            timestamp=datetime.utcnow()
        )
        
        # Add to database
        db.session.add(note)
        db.session.commit()
        
        # Log successful save
        print(f"✅ Note saved successfully - User: {current_user.username}, Date: {note_date}, Content: {data['content'][:50]}...")
        
        return jsonify({
            'success': True, 
            'message': 'Note saved successfully',
            'note_id': note.id,
            'timestamp': note.timestamp.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving note: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to save note. Please try again.'}), 500

@app.route('/api/mood-notes-history')
@login_required
def get_mood_notes_history():
    try:
        date_str = request.args.get('date', date.today().isoformat())
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get mood logs for the selected date
        mood_logs = MoodLog.query.filter_by(
            user_id=current_user.id,
            date=selected_date
        ).order_by(MoodLog.timestamp.desc()).all()
        
        # Get notes for the selected date
        notes = Note.query.filter_by(
            user_id=current_user.id,
            date=selected_date
        ).order_by(Note.timestamp.desc()).all()
        
        # Log the retrieval
        print(f"📋 Retrieved {len(notes)} notes and {len(mood_logs)} mood logs for User: {current_user.username}, Date: {selected_date}")
        
        return jsonify({
            'success': True,
            'mood_logs': [{
                'id': log.id,
                'mood': log.mood,
                'timestamp': log.timestamp.isoformat()
            } for log in mood_logs],
            'notes': [{
                'id': note.id,
                'content': note.content,
                'timestamp': note.timestamp.isoformat()
            } for note in notes]
        })
        
    except Exception as e:
        print(f"❌ Error retrieving mood/notes history: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve history'}), 500

@app.route('/api/test-auth')
def test_auth():
    """Simple test endpoint to debug authentication"""
    print(f"🧪 Test auth endpoint called")
    print(f"🧪 User authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        return jsonify({'success': True, 'message': 'User is authenticated', 'user_id': current_user.id})
    else:
        return jsonify({'success': False, 'message': 'User not authenticated'}), 401

@app.route('/api/dashboard-data')
@login_required
def get_dashboard_data():
    # Use Flask-Login authentication (matching existing dashboard route)
    user_id = current_user.id
    date_str = request.args.get('date', date.today().isoformat())
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format', 'success': False}), 400
    
    # Get food logs using SQLAlchemy
    food_logs = FoodLog.query.filter_by(
        user_id=user_id,
        date=selected_date
    ).all()
    
    # Get water logs
    water_logs = WaterLog.query.filter_by(
        user_id=user_id,
        date=selected_date
    ).all()
    
    # Get mood logs
    mood_logs = MoodLog.query.filter_by(
        user_id=user_id,
        date=selected_date
    ).all()
    
    # Get notes
    notes = Note.query.filter_by(
        user_id=user_id,
        date=selected_date
    ).order_by(Note.timestamp.desc()).all()
    
    # Calculate totals
    total_calories = sum(log.calories or 0 for log in food_logs)
    total_protein = sum(log.protein or 0 for log in food_logs)
    total_carbs = sum(log.carbs or 0 for log in food_logs)
    total_fat = sum(log.fat or 0 for log in food_logs)
    total_water = sum(log.amount or 0 for log in water_logs)  # Amount already in oz
    
    # Convert to dictionaries for JSON serialization
    food_logs_data = [
        {
            'id': log.id,
            'name': log.name,
            'brand': log.brand,
            'calories': log.calories or 0,
            'protein': log.protein or 0,
            'carbs': log.carbs or 0,
            'fat': log.fat or 0,
            'fiber': log.fiber or 0,
            'sugar': log.sugar or 0,
            'sodium': log.sodium or 0,
            'serving_size': log.serving_size or 0,
            'quantity': log.quantity or 1,
            'time_of_day': log.time_of_day,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None
        } for log in food_logs
    ]
    
    water_logs_data = [
        {
            'id': log.id,
            'amount': log.amount or 0,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None
        } for log in water_logs
    ]
    
    mood_logs_data = [
        {
            'id': log.id,
            'mood': log.mood,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None
        } for log in mood_logs
    ]
    
    notes_data = [
        {
            'id': log.id,
            'content': log.content,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None
        } for log in notes
    ]
    
    # Get recent recipes (limit 5)
    recent_recipes = Recipe.query.filter_by(user_id=user_id).order_by(Recipe.created_at.desc()).limit(5).all()
    recipes_data = [
        {
            'id': recipe.id,
            'name': recipe.name,
            'description': recipe.description,
            'image_path': recipe.image_path,
            'created_at': recipe.created_at.isoformat() if recipe.created_at else None
        } for recipe in recent_recipes
    ]
    
    return jsonify({
        'success': True,
        'data': {
            'food_logs': food_logs_data,
            'water_logs': water_logs_data,
            'mood_logs': mood_logs_data,
            'notes': notes_data,
            'recent_recipes': recipes_data,
            'totals': {
                'calories': total_calories,
                'protein': total_protein,
                'carbs': total_carbs,
                'fat': total_fat,
                'water': total_water
            }
        },
        'date': date_str
    })

@app.route('/api/profile', methods=['GET', 'POST'])
@login_required
def profile_api():
    if request.method == 'POST':
        data = request.get_json()
        
        current_user.name = data['name']
        current_user.age = data.get('age')
        current_user.weight = data.get('weight')
        current_user.height = data.get('height')
        current_user.health_goals = data.get('health_goals')
        current_user.ailments_concerns = data.get('ailments_concerns')
        
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({
        'success': True,
        'data': {
            'name': current_user.name,
            'age': current_user.age,
            'weight': current_user.weight,
            'height': current_user.height,
            'health_goals': current_user.health_goals,
            'ailments_concerns': current_user.ailments_concerns,
            'profile_image': current_user.profile_image,
            'is_admin': current_user.is_admin
        }
    })

@app.route('/api/profile/upload-image', methods=['POST'])
@login_required
def upload_profile_image():
    """Upload profile image"""
    if 'profile_image' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['profile_image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP'})
    
    try:
        # Delete old profile image if exists
        if current_user.profile_image:
            delete_profile_image(current_user.profile_image)
        
        # Save new profile image
        filename = save_profile_image(file, current_user.id)
        if filename:
            current_user.profile_image = filename
            db.session.commit()
            return jsonify({
                'success': True, 
                'message': 'Profile image uploaded successfully',
                'image_url': url_for('static', filename=filename)
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save image'})
            
    except Exception as e:
        print(f"Error uploading profile image: {e}")
        return jsonify({'success': False, 'message': 'Failed to upload image'})

@app.route('/api/profile/remove-image', methods=['POST'])
@login_required
def remove_profile_image():
    """Remove profile image"""
    try:
        if current_user.profile_image:
            delete_profile_image(current_user.profile_image)
            current_user.profile_image = None
            db.session.commit()
            return jsonify({'success': True, 'message': 'Profile image removed successfully'})
        else:
            return jsonify({'success': False, 'message': 'No profile image to remove'})
    except Exception as e:
        print(f"Error removing profile image: {e}")
        return jsonify({'success': False, 'message': 'Failed to remove image'})

@app.route('/api/profile/select-avatar', methods=['POST'])
@login_required
def select_avatar():
    """Select a predefined avatar"""
    data = request.get_json()
    avatar_id = data.get('avatar_id')
    
    if not avatar_id:
        return jsonify({'success': False, 'message': 'Avatar ID is required'})
    
    # Get available avatars
    avatars = get_available_avatars()
    selected_avatar = next((avatar for avatar in avatars if avatar['id'] == avatar_id), None)
    
    if not selected_avatar:
        return jsonify({'success': False, 'message': 'Invalid avatar selection'})
    
    try:
        # Delete old custom profile image if exists
        if current_user.profile_image and not current_user.profile_image.startswith('assets/avatars/'):
            delete_profile_image(current_user.profile_image)
        
        # Set the selected avatar
        current_user.profile_image = selected_avatar['path']
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Avatar selected successfully',
            'image_url': url_for('static', filename=selected_avatar['path'])
        })
        
    except Exception as e:
        print(f"Error selecting avatar: {e}")
        return jsonify({'success': False, 'message': 'Failed to select avatar'})

@app.route('/api/profile/avatars', methods=['GET'])
@login_required
def get_avatars():
    """Get available avatars"""
    avatars = get_available_avatars()
    return jsonify({
        'success': True,
        'avatars': avatars,
        'current_avatar': current_user.profile_image
    })

@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    data = request.get_json()
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    # Validate current password
    if not current_password:
        return jsonify({'success': False, 'message': 'Current password is required'})
    
    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    # Validate new password
    if not new_password:
        return jsonify({'success': False, 'message': 'New password is required'})
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New passwords do not match'})
    
    # Validate password strength
    is_valid_password, password_error = validate_password_strength(new_password)
    if not is_valid_password:
        return jsonify({'success': False, 'message': password_error})
    
    # Update password
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})


@app.route('/api/food-log/<int:food_id>', methods=['DELETE'])
@login_required
def delete_food_log(food_id):
    food_log = FoodLog.query.filter_by(id=food_id, user_id=current_user.id).first()
    
    if not food_log:
        return jsonify({'success': False, 'message': 'Food log not found'})
    
    db.session.delete(food_log)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/food-log/<int:food_id>/edit', methods=['PUT'])
@login_required
def edit_food_log(food_id):
    food_log = FoodLog.query.filter_by(id=food_id, user_id=current_user.id).first()
    
    if not food_log:
        return jsonify({'success': False, 'message': 'Food log not found'})
    
    data = request.get_json()
    new_date = data.get('date')
    new_time_of_day = data.get('time_of_day')
    
    if not new_date:
        return jsonify({'success': False, 'message': 'New date is required'})
    
    try:
        # Convert string date to date object
        new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
        food_log.date = new_date_obj
        
        # Update time of day if provided
        if new_time_of_day:
            food_log.time_of_day = new_time_of_day
        
        # Update nutrition values if provided (for serving size changes)
        if 'quantity' in data:
            food_log.quantity = data['quantity']
        if 'calories' in data:
            food_log.calories = data['calories']
        if 'protein' in data:
            food_log.protein = data['protein']
        if 'carbs' in data:
            food_log.carbs = data['carbs']
        if 'fat' in data:
            food_log.fat = data['fat']
        if 'serving_size' in data:
            food_log.serving_size = data['serving_size']
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Food item updated successfully'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update food item'})

@app.route('/api/food-log/<int:food_id>/copy', methods=['POST'])
@login_required
def copy_food_log(food_id):
    """Copy a food log item to a new date"""
    food_log = FoodLog.query.filter_by(id=food_id, user_id=current_user.id).first()
    
    if not food_log:
        return jsonify({'success': False, 'message': 'Food log not found'})
    
    data = request.get_json()
    target_date = data.get('target_date')
    time_of_day = data.get('time_of_day', 'snack')
    
    if not target_date:
        return jsonify({'success': False, 'message': 'Target date is required'})
    
    try:
        # Convert string date to date object
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Create a new food log entry with the same data but new date and time
        new_food_log = FoodLog(
            user_id=current_user.id,
            name=food_log.name,
            brand=food_log.brand,
            calories=food_log.calories,
            protein=food_log.protein,
            carbs=food_log.carbs,
            fat=food_log.fat,
            fiber=food_log.fiber,
            sugar=food_log.sugar,
            sodium=food_log.sodium,
            serving_size=food_log.serving_size,
            original_amount=food_log.original_amount,
            original_unit=food_log.original_unit,
            quantity=food_log.quantity,
            date=target_date_obj,
            time_of_day=time_of_day
        )
        
        db.session.add(new_food_log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Food item copied successfully'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error copying food item: {e}")
        return jsonify({'success': False, 'message': 'Failed to copy food item'})

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

@app.route('/human-help')
def human_help():
    """Human help page with Calendly booking"""
    return render_template('human_help.html')

# Payment and Subscription Routes
@app.route('/api/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session for subscription upgrade"""
    try:
        stripe_client = get_stripe_client()
        
        if not stripe_client or not stripe_client.is_payment_ready():
            return jsonify({
                'success': False, 
                'error': 'Payment system not ready. Please check your Stripe configuration.',
                'details': 'The payment system is initializing. Please try again in a moment.'
            }), 503
        
        # Get or create Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe_client.create_customer(
                email=current_user.email,
                name=current_user.name,
                user_id=current_user.id
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session
        success_url = url_for('payment_success', _external=True)
        cancel_url = url_for('profile', _external=True)
        
        checkout_session = stripe_client.create_checkout_session(
            customer_id=current_user.stripe_customer_id,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url
        })
        
    except Exception as e:
        print(f"❌ Error creating checkout session: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/customer-portal', methods=['POST'])
@login_required
def create_customer_portal_session():
    """Create a customer portal session for subscription management"""
    try:
        if not current_user.stripe_customer_id:
            return jsonify({'success': False, 'error': 'No subscription found'})
        
        stripe_client = get_stripe_client()
        if not stripe_client or not stripe_client.is_payment_ready():
            return jsonify({
                'success': False, 
                'error': 'Payment system not ready. Please check your Stripe configuration.',
                'details': 'The payment system is initializing. Please try again in a moment.'
            }), 503
        
        return_url = url_for('profile', _external=True)
        
        session = stripe_client.create_customer_portal_session(
            customer_id=current_user.stripe_customer_id,
            return_url=return_url
        )
        
        return jsonify({
            'success': True,
            'portal_url': session.url
        })
        
    except Exception as e:
        print(f"❌ Error creating customer portal session: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/subscription-status')
@login_required
def get_subscription_status():
    """Get current user's subscription status and premium access"""
    try:
        # Check if user has premium access based on role
        has_premium = current_user.has_premium_access()
        
        # Get active subscription for regular users
        subscription = None
        if current_user.is_regular_user():
            subscription = Subscription.query.filter_by(
                user_id=current_user.id,
                status='active'
            ).first()
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict() if subscription else None,
            'is_premium': has_premium,
            'user_role': current_user.role,
            'is_admin': current_user.is_admin_role(),
            'is_ff': current_user.is_ff_role()
        })
            
    except Exception as e:
        print(f"❌ Error getting subscription status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/log-health-coaching-revenue', methods=['POST'])
@login_required
def log_health_coaching_revenue():
    """Log revenue from health coaching sessions"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        description = data.get('description', 'Health coaching session')
        
        if not amount:
            return jsonify({'success': False, 'error': 'Amount is required'}), 400
        
        # Log the revenue
        analytics_service.log_revenue(
            user_id=current_user.id,
            revenue_type='health_coaching',
            amount=float(amount),
            description=description
        )
        
        return jsonify({'success': True, 'message': 'Revenue logged successfully'})
        
    except Exception as e:
        print(f"❌ Error logging health coaching revenue: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        if not sig_header:
            return jsonify({'error': 'No signature header'}), 400
        
        # Get webhook secret from environment
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        if not webhook_secret:
            print("⚠️ STRIPE_WEBHOOK_SECRET not set, skipping signature verification")
            event = json.loads(payload)
        else:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except ValueError as e:
                print(f"❌ Invalid payload: {e}")
                return jsonify({'error': 'Invalid payload'}), 400
            except stripe.error.SignatureVerificationError as e:
                print(f"❌ Invalid signature: {e}")
                return jsonify({'error': 'Invalid signature'}), 400
        
        # Handle the event
        stripe_client = get_stripe_client()
        if not stripe_client or not stripe_client.is_configured():
            print("⚠️ Stripe client not configured, skipping webhook processing")
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 500
        
        result = stripe_client.handle_webhook_event(event)
        
        # Update local database based on webhook events
        event_type = event['type']
        event_data = event['data']['object']
        
        print(f"📨 Processing webhook: {event_type}")
        
        if event_type == 'customer.subscription.created':
            handle_subscription_created(event_data)
        elif event_type == 'customer.subscription.updated':
            handle_subscription_updated(event_data)
        elif event_type == 'customer.subscription.deleted':
            handle_subscription_deleted(event_data)
        elif event_type == 'invoice.payment_succeeded':
            handle_invoice_payment_succeeded(event_data)
        elif event_type == 'invoice.payment_failed':
            handle_invoice_payment_failed(event_data)
        elif event_type == 'payment_intent.succeeded':
            handle_payment_intent_succeeded(event_data)
        elif event_type == 'payment_intent.payment_failed':
            handle_payment_intent_failed(event_data)
        elif event_type == 'customer.created':
            handle_customer_created(event_data)
        elif event_type == 'customer.updated':
            handle_customer_updated(event_data)
        elif event_type == 'charge.succeeded':
            handle_charge_succeeded(event_data)
        elif event_type == 'charge.failed':
            handle_charge_failed(event_data)
        elif event_type == 'charge.refunded':
            handle_charge_refunded(event_data)
        else:
            print(f"ℹ️ Unhandled webhook event: {event_type}")
        
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        print(f"❌ Error handling webhook: {e}")
        return jsonify({'error': str(e)}), 500

def handle_subscription_created(stripe_subscription):
    """Handle subscription creation webhook"""
    try:
        customer_id = stripe_subscription['customer']
        subscription_id = stripe_subscription['id']
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"❌ User not found for customer ID: {customer_id}")
            return
        
        # Create or update subscription record
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if not subscription:
            subscription = Subscription(
                user_id=user.id,
                stripe_subscription_id=subscription_id,
                stripe_customer_id=customer_id,
                plan_type='premium',
                status=stripe_subscription['status'],
                current_period_start=datetime.fromtimestamp(stripe_subscription['current_period_start']),
                current_period_end=datetime.fromtimestamp(stripe_subscription['current_period_end'])
            )
            db.session.add(subscription)
        else:
            subscription.status = stripe_subscription['status']
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription['current_period_end'])
        
        db.session.commit()
        print(f"✅ Subscription created/updated for user {user.id}")
        
    except Exception as e:
        print(f"❌ Error handling subscription creation: {e}")
        db.session.rollback()

def handle_subscription_updated(stripe_subscription):
    """Handle subscription update webhook"""
    try:
        subscription_id = stripe_subscription['id']
        
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = stripe_subscription['status']
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription['current_period_end'])
            subscription.cancel_at_period_end = stripe_subscription.get('cancel_at_period_end', False)
            subscription.updated_at = datetime.utcnow()
            
            db.session.commit()
            print(f"✅ Subscription updated: {subscription_id}")
        
    except Exception as e:
        print(f"❌ Error handling subscription update: {e}")
        db.session.rollback()

def handle_subscription_deleted(stripe_subscription):
    """Handle subscription deletion webhook"""
    try:
        subscription_id = stripe_subscription['id']
        
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'canceled'
            subscription.updated_at = datetime.utcnow()
            
            db.session.commit()
            print(f"✅ Subscription marked as canceled: {subscription_id}")
        
    except Exception as e:
        print(f"❌ Error handling subscription deletion: {e}")
        db.session.rollback()

def handle_invoice_payment_succeeded(invoice):
    """Handle successful invoice payment webhook"""
    try:
        customer_id = invoice['customer']
        subscription_id = invoice.get('subscription')
        amount = invoice['amount_paid'] / 100  # Convert from cents
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"❌ User not found for customer ID: {customer_id}")
            return
        
        # Log revenue
        analytics_service.log_revenue(
            user_id=user.id,
            revenue_type='subscription',
            amount=amount,
            stripe_subscription_id=subscription_id,
            description=f"Monthly subscription payment - {invoice['currency'].upper()}"
        )
        
        print(f"✅ Invoice payment succeeded for user {user.id}: ${amount}")
        
    except Exception as e:
        print(f"❌ Error handling invoice payment success: {e}")

def handle_invoice_payment_failed(invoice):
    """Handle failed invoice payment webhook"""
    try:
        customer_id = invoice['customer']
        subscription_id = invoice.get('subscription')
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"❌ User not found for customer ID: {customer_id}")
            return
        
        # Update subscription status if needed
        if subscription_id:
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            if subscription:
                subscription.status = 'past_due'
                db.session.commit()
                print(f"⚠️ Subscription marked as past_due for user {user.id}")
        
        print(f"❌ Invoice payment failed for user {user.id}")
        
    except Exception as e:
        print(f"❌ Error handling invoice payment failure: {e}")

def handle_payment_intent_succeeded(payment_intent):
    """Handle successful payment intent webhook"""
    try:
        customer_id = payment_intent['customer']
        amount = payment_intent['amount'] / 100  # Convert from cents
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"❌ User not found for customer ID: {customer_id}")
            return
        
        # Log revenue for one-time payments
        if not payment_intent.get('metadata', {}).get('subscription_type'):
            analytics_service.log_revenue(
                user_id=user.id,
                revenue_type='one_time_payment',
                amount=amount,
                stripe_payment_intent_id=payment_intent['id'],
                description=f"One-time payment - {payment_intent['currency'].upper()}"
            )
            print(f"✅ One-time payment succeeded for user {user.id}: ${amount}")
        
    except Exception as e:
        print(f"❌ Error handling payment intent success: {e}")

def handle_payment_intent_failed(payment_intent):
    """Handle failed payment intent webhook"""
    try:
        customer_id = payment_intent['customer']
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"❌ User not found for customer ID: {customer_id}")
            return
        
        print(f"❌ Payment intent failed for user {user.id}: {payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Error handling payment intent failure: {e}")

def handle_customer_created(customer):
    """Handle customer creation webhook"""
    try:
        customer_id = customer['id']
        email = customer['email']
        
        print(f"✅ New Stripe customer created: {email} (ID: {customer_id})")
        
        # You could add additional logic here like:
        # - Sending welcome emails
        # - Creating user profiles
        # - Setting up default preferences
        
    except Exception as e:
        print(f"❌ Error handling customer creation: {e}")

def handle_customer_updated(customer):
    """Handle customer update webhook"""
    try:
        customer_id = customer['id']
        email = customer['email']
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            # Update user information if needed
            if customer.get('name') and customer['name'] != user.name:
                user.name = customer['name']
                db.session.commit()
                print(f"✅ Updated user name for {email}")
        
        print(f"ℹ️ Stripe customer updated: {email} (ID: {customer_id})")
        
    except Exception as e:
        print(f"❌ Error handling customer update: {e}")

def handle_charge_succeeded(charge):
    """Handle successful charge webhook"""
    try:
        customer_id = charge['customer']
        amount = charge['amount'] / 100  # Convert from cents
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"❌ User not found for customer ID: {customer_id}")
            return
        
        print(f"✅ Charge succeeded for user {user.id}: ${amount}")
        
    except Exception as e:
        print(f"❌ Error handling charge success: {e}")

def handle_charge_failed(charge):
    """Handle failed charge webhook"""
    try:
        customer_id = charge['customer']
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"❌ User not found for customer ID: {customer_id}")
            return
        
        print(f"❌ Charge failed for user {user.id}: {charge.get('failure_message', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Error handling charge failure: {e}")

def handle_charge_refunded(charge):
    """Handle charge refund webhook"""
    try:
        customer_id = charge['customer']
        refund_amount = charge['amount_refunded'] / 100  # Convert from cents
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"❌ User not found for customer ID: {customer_id}")
            return
        
        # Log refund
        analytics_service.log_revenue(
            user_id=user.id,
            revenue_type='refund',
            amount=-refund_amount,  # Negative amount for refunds
            stripe_payment_intent_id=charge.get('payment_intent'),
            description=f"Refund processed - {charge['currency'].upper()}"
        )
        
        print(f"💰 Charge refunded for user {user.id}: ${refund_amount}")
        
    except Exception as e:
        print(f"❌ Error handling charge refund: {e}")

@app.route('/payment-success')
@login_required
def payment_success():
    """Payment success page"""
    return render_template('payment_success.html')

# Register recipe blueprint
app.register_blueprint(recipe_bp)

# Recipe page route
@app.route('/recipes')
@login_required
def recipes():
    """Recipe management page"""
    return render_template('recipes/recipes.html', current_user_id=current_user.id)

@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt for AI crawlers and search engines"""
    return send_from_directory(app.static_folder, 'robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    """Serve sitemap.xml for search engines"""
    return send_from_directory(app.static_folder, 'sitemap.xml', mimetype='application/xml')

@app.route('/health')
def health_check():
    """Health check endpoint for debugging"""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'booking_system': 'calendly'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

def validate_password_strength(password):
    """
    Validate password strength with comprehensive requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    
    # Check for common patterns
    common_patterns = [
        'password', '123456', 'qwerty', 'abc123', 'password123',
        'admin', 'user', 'test', 'welcome', 'letmein'
    ]
    
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            return False, "Password contains common patterns that are not allowed"
    
    # Check for repeated characters
    if re.search(r'(.)\1{2,}', password):
        return False, "Password cannot contain more than 2 consecutive identical characters"
    
    return True, "Password meets all requirements"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
        initialize_app_settings()
        
        # Initialize Stripe products and prices
        try:
            from stripe_client import get_stripe_client
            stripe_client = get_stripe_client()
            if stripe_client:
                print("🔧 Initializing Stripe products and prices...")
                stripe_client.setup_products_and_prices()
                if stripe_client.is_payment_ready():
                    print("✅ Stripe payment system ready!")
                else:
                    print("⚠️ Stripe products setup incomplete")
            else:
                print("⚠️ Stripe client not available")
        except Exception as e:
            print(f"⚠️ Error initializing Stripe: {e}")
    
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='127.0.0.1', port=port)
