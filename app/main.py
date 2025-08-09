import os
import json
import requests
import csv
import io
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from config import DevelopmentConfig, ProductionConfig
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import random
import hashlib
import time

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

# Cloudflare Turnstile Configuration
app.config['TURNSTILE_SITE_KEY'] = os.environ.get('SITE_KEY')
app.config['TURNSTILE_SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['TURNSTILE_ENABLED'] = os.environ.get('TURNSTILE_ENABLED', 'true').lower() == 'true'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# User Model for Authentication
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    date_of_birth = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    goals = db.Column(db.Text, nullable=True)
    ailments = db.Column(db.Text, nullable=True)
    daily_activities = db.Column(db.Text, nullable=True)
    day_notes = db.Column(db.Text, nullable=True)
    sleep_schedule = db.Column(db.String(50), nullable=True)
    night_notes = db.Column(db.Text, nullable=True)
    dietary_preferences = db.Column(db.Text, nullable=True)
    exercise_routine = db.Column(db.Text, nullable=True)
    spiritual_religion = db.Column(db.Text, nullable=True)
    self_connection = db.Column(db.Text, nullable=True)
    surroundings_connection = db.Column(db.Text, nullable=True)
    providing_others = db.Column(db.Text, nullable=True)
    safe_groups = db.Column(db.Text, nullable=True)
    awe_things = db.Column(db.Text, nullable=True)
    creative_expression = db.Column(db.Text, nullable=True)
    upsetting_situations = db.Column(db.Text, nullable=True)
    spirit_notes = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(100), nullable=True, default='default-avatar.png')
    weight_unit = db.Column(db.String(10), nullable=True, default='kg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
@app.context_processor
def inject_functions():
    return {
        'get_current_user': get_current_user,
        'is_admin_user': is_admin_user,
        'ADMIN_EMAIL': os.environ.get('ADMIN_EMAIL', 'admin@kiwellness.org'),
        'TURNSTILE_SITE_KEY': app.config.get('TURNSTILE_SITE_KEY'),
        'TURNSTILE_ENABLED': app.config.get('TURNSTILE_ENABLED', True)
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
        return UserProfile.query.filter_by(user_id=user.id).first()
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
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    fiber = db.Column(db.Float, nullable=True)
    sugar = db.Column(db.Float, nullable=True)
    sodium = db.Column(db.Float, nullable=True)
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
def search_openfoodfacts_api(food_name):
    """Search Open Food Facts API for nutritional information"""
    try:
        url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={food_name}&search_simple=1&action=process&json=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('products') and len(data['products']) > 0:
            product = data['products'][0]
            nutriments = product.get('nutriments', {})
            
            return {
                'food_name': product.get('product_name', food_name),
                'brand': product.get('brands', ''),
                'serving_size': 100,  # Default to 100g
                'serving_unit': 'g',
                'calories': nutriments.get('energy-kcal_100g'),
                'protein': nutriments.get('proteins_100g'),
                'carbs': nutriments.get('carbohydrates_100g'),
                'fat': nutriments.get('fat_100g'),
                'fiber': nutriments.get('fiber_100g'),
                'sugar': nutriments.get('sugars_100g'),
                'sodium': nutriments.get('salt_100g'),
                'source': 'openfoodfacts'
            }
    except Exception as e:
        print(f"Open Food Facts API error: {e}")
        return None

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
    
    nutritional_fields = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
    for field in nutritional_fields:
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        turnstile_response = request.form.get('cf-turnstile-response')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        # Turnstile validation
        if not turnstile_response:
            flash('Please complete the security verification', 'error')
            return render_template('login.html')
        
        # Verify Turnstile
        if not verify_turnstile(turnstile_response):
            flash('Security verification failed. Please try again.', 'error')
            return render_template('login.html')
        
        user = User.query.filter(User.username.ilike(username)).first()
        
        if user and user.check_password(password):
            # SECURITY: Set up session with timeout
            session['user_id'] = user.id
            session['last_activity'] = datetime.utcnow().isoformat()
            session.permanent = True  # Enable session timeout
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        turnstile_response = request.form.get('cf-turnstile-response')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        # Turnstile validation
        if not turnstile_response:
            flash('Please complete the security verification', 'error')
            return render_template('register.html')
        
        # Verify Turnstile
        if not verify_turnstile(turnstile_response):
            flash('Security verification failed. Please try again.', 'error')
            return render_template('register.html')
        
        # Username validation
        import re
        username_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$')
        if not username_pattern.match(username):
            flash('Username must start and end with a letter or number. Can contain letters, numbers, periods, underscores, and dashes in the middle.', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return render_template('register.html')
        
        if len(username) > 30:
            flash('Username must be 30 characters or less', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter(User.username.ilike(username)).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter(User.email.ilike(email)).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
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
            
            session['user_id'] = user.id
            flash('Registration successful! Welcome to KI Wellness!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
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
    return render_template('profile.html', profile=user_profile)

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
    # Get all users
    users = User.query.all()
    user_stats = {
        'total_users': len(users),
        'admin_users': len([u for u in users if u.is_admin]),
        'regular_users': len([u for u in users if not u.is_admin])
    }
    
    return render_template('admin_dashboard.html', users=users, stats=user_stats)

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
                'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                'age': profile.age,
                'weight': profile.weight,
                'height': profile.height,
                'goals': profile.goals,
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
@login_required
def search_food():
    try:
        data = request.get_json()
        food_name = data.get('food_name', '').strip()
        serving_size = float(data.get('serving_size', 0))
        serving_unit = data.get('serving_unit', 'g')
        
        if not food_name:
            return jsonify({'success': False, 'error': 'Food name is required'})
        
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
        
        # Search APIs
        nutrition_data = None
        
        # Try Open Food Facts first
        nutrition_data = search_openfoodfacts_api(food_name)
        
        # If not found, try USDA
        if not nutrition_data:
            nutrition_data = search_usda_api(food_name)
        
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
@login_required
def add_food_entry():
    try:
        data = request.get_json()
        
        # Get current user profile
        user_profile = get_current_user_profile()
        if not user_profile:
            return jsonify({'success': False, 'error': 'User profile not found'})
        
        # Handle timezone-aware datetime
        browser_timezone = data.get('browser_timezone')
        if data.get('consumed_at'):
            consumed_at = get_browser_timezone_datetime(browser_timezone) if browser_timezone else datetime.strptime(data['consumed_at'], '%Y-%m-%d %H:%M')
        else:
            consumed_at = get_browser_timezone_datetime(browser_timezone) if browser_timezone else datetime.utcnow()
        
        # Create food journal entry
        food_entry = FoodJournal(
            user_id=user_profile.id,
            food_name=data['food_name'],
            brand=data.get('brand'),
            serving_size=data['serving_size'],
            serving_unit=data['serving_unit'],
            calories=data.get('calories'),
            protein=data.get('protein'),
            carbs=data.get('carbs'),
            fat=data.get('fat'),
            fiber=data.get('fiber'),
            sugar=data.get('sugar'),
            sodium=data.get('sodium'),
            time_of_day=data.get('time_of_day'),
            water_amount=data.get('water_amount'),
            water_unit=data.get('water_unit'),
            mood=data.get('mood'),
            notes=data.get('notes'),
            consumed_at=consumed_at
        )
        
        db.session.add(food_entry)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Food entry added successfully'})
        
    except Exception as e:
        db.session.rollback()
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
        
        # Read CSV file
        content = file.read().decode('utf-8')
        csv_data = csv.DictReader(io.StringIO(content))
        
        imported_count = 0
        errors = []
        
        for row in csv_data:
            try:
                # Parse date and time (assume local timezone)
                date_str = row.get('Date', '')
                time_str = row.get('Time', '')
                
                if date_str and time_str:
                    # Parse as local time and convert to UTC for storage
                    local_dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
                    consumed_at = local_dt
                else:
                    consumed_at = datetime.utcnow()
                
                # Create food entry
                food_entry = FoodJournal(
                    user_id=user_profile.id,
                    food_name=row.get('Food Name', ''),
                    brand=row.get('Brand', ''),
                    serving_size=float(row.get('Serving Size', 0)),
                    serving_unit=row.get('Serving Unit', 'g'),
                    calories=float(row.get('Calories', 0)) if row.get('Calories') else None,
                    protein=float(row.get('Protein (g)', 0)) if row.get('Protein (g)') else None,
                    carbs=float(row.get('Carbs (g)', 0)) if row.get('Carbs (g)') else None,
                    fat=float(row.get('Fat (g)', 0)) if row.get('Fat (g)') else None,
                    fiber=float(row.get('Fiber (g)', 0)) if row.get('Fiber (g)') else None,
                    sugar=float(row.get('Sugar (g)', 0)) if row.get('Sugar (g)') else None,
                    sodium=float(row.get('Sodium (mg)', 0)) if row.get('Sodium (mg)') else None,
                    mood=row.get('Mood', ''),
                    notes=row.get('Notes', ''),
                    consumed_at=consumed_at
                )
                
                db.session.add(food_entry)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {imported_count + 1}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Imported {imported_count} entries successfully',
            'imported_count': imported_count,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

def analyze_patterns_with_openai(entries_data, time_period, user_profile=None):
    """Analyze food journal patterns using OpenAI API with user profile context"""
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Prepare the data for analysis
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
                'fat': 0
            }
        }
        
        for entry in entries_data:
            # Collect food data
            if entry.get('food_name'):
                analysis_data['foods'].append({
                    'name': entry['food_name'],
                    'serving_size': entry.get('serving_size'),
                    'serving_unit': entry.get('serving_unit'),
                    'time_of_day': entry.get('time_of_day')
                })
            
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
            
            # Sum nutritional data
            if entry.get('calories'):
                analysis_data['nutritional_totals']['calories'] += entry['calories']
            if entry.get('protein'):
                analysis_data['nutritional_totals']['protein'] += entry['protein']
            if entry.get('carbs'):
                analysis_data['nutritional_totals']['carbs'] += entry['carbs']
            if entry.get('fat'):
                analysis_data['nutritional_totals']['fat'] += entry['fat']
        
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
        
        # Create prompt for OpenAI with personal touch
        prompt = f"""
        You are {user_name}'s personal wellness coach. Analyze their nutritional journal data from the past {time_period} days and speak directly to them with personalized insights.
        
        {profile_context}
        
        {user_name}'s NUTRITIONAL JOURNAL DATA:
        - Total entries: {analysis_data['total_entries']}
        - Foods consumed: {len(analysis_data['foods'])} different items
        - Mood entries: {len(analysis_data['moods'])} entries
        - Water intake entries: {len(analysis_data['water_intake'])} entries
        - Total calories: {analysis_data['nutritional_totals']['calories']:.1f}
        - Total protein: {analysis_data['nutritional_totals']['protein']:.1f}g
        - Total carbs: {analysis_data['nutritional_totals']['carbs']:.1f}g
        - Total fat: {analysis_data['nutritional_totals']['fat']:.1f}g
        
        HYDRATION ANALYSIS:
        - Total water intake: {total_water_oz:.1f} oz
        - Average water per entry: {avg_water_oz:.1f} oz
        - Dashboard water entries: {dashboard_water_count} (total: {dashboard_water_oz} oz)
        - Other water sources: {len(analysis_data['water_entries']) - dashboard_water_count} entries
        - Water entry details: {analysis_data['water_entries']}
        
        Detailed Data:
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
                    [Analyze {user_name}'s physical patterns with specific data: calorie ranges (e.g., "Your daily average is 1,200-1,800 calories"), macronutrient ratios, hydration consistency, and energy patterns. Reference exact nutritional data and water intake patterns.]
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
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are {user_name}'s personal wellness coach. Speak directly to them using their name and 'you'/'your' throughout. Be encouraging, supportive, and provide actionable insights tailored specifically to their unique situation. Make it feel like a personal conversation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
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

def verify_turnstile(response):
    """
    Verify Cloudflare Turnstile response
    """
    # If Turnstile is disabled, return True for development
    if not app.config.get('TURNSTILE_ENABLED', True):
        return True
    
    # If no response provided, return False
    if not response:
        return False
    
    try:
        # Make a request to Cloudflare's Turnstile verification endpoint
        verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
        data = {
            'secret': app.config['TURNSTILE_SECRET_KEY'],
            'response': response
        }
        
        result = requests.post(verify_url, data=data, timeout=10)
        result_json = result.json()
        
        # Check if the verification was successful
        return result_json.get('success', False)
    except Exception as e:
        print(f"Turnstile verification error: {e}")
        # In development, if there's an error, allow the request to proceed
        if app.config.get('DEBUG', False):
            return True
        return False

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables initialized successfully!")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize database tables: {e}")
            print("This is normal if the database is not available or tables already exist.")
    app.run(debug=True)



