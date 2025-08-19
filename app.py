import os
import requests
import json
import uuid
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import sqlite3
import ollama
import stripe
from food_data import BASIC_FOODS, COMMON_FOODS_DB
from health_resources import get_relevant_resources, format_resources_for_prompt

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
db_url = os.getenv('DATABASE_URL')
if db_url:
    # Normalize old Heroku-style URLs
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    # Development - SQLite fallback
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ki_wellness.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/profile_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# API Configuration
OPENFOODFACTS_API = "https://world.openfoodfacts.org/cgi/search.pl"
USDA_API_KEY = os.getenv('USDA_API_KEY')
USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"

# Stripe Configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_PRICE_ID_30MIN = os.getenv('STRIPE_PRICE_ID_30MIN')  # $20 for 30 minutes
STRIPE_PRICE_ID_DONATION = os.getenv('STRIPE_PRICE_ID_DONATION')  # Donation link

# Food data imported from food_data.py

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    weight = db.Column(db.Float)  # in kg
    height = db.Column(db.Float)  # in cm
    health_goals = db.Column(db.Text)
    profile_image = db.Column(db.String(255))  # Path to profile image
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Agreement tracking
    agreed_to_terms = db.Column(db.Boolean, default=False)
    agreed_to_privacy = db.Column(db.Boolean, default=False)
    agreed_to_disclaimer = db.Column(db.Boolean, default=False)
    agreements_date = db.Column(db.DateTime)  # When agreements were accepted
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='user', lazy=True)
    water_logs = db.relationship('WaterLog', backref='user', lazy=True)
    mood_logs = db.relationship('MoodLog', backref='user', lazy=True)
    notes = db.relationship('Note', backref='user', lazy=True)

class FoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(200))
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    fiber = db.Column(db.Float)
    sugar = db.Column(db.Float)
    sodium = db.Column(db.Float)
    serving_size = db.Column(db.Float)  # in grams
    original_amount = db.Column(db.Float)
    original_unit = db.Column(db.String(20))
    quantity = db.Column(db.Float, default=1)
    time_of_day = db.Column(db.String(20), nullable=False, default='snack')  # breakfast, lunch, dinner, snack
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class WaterLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # in cups (1 cup = 8 oz)
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class MoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood = db.Column(db.Integer, nullable=False)  # 1-5 scale
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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

def set_app_setting(key, value):
    """Set an app setting value"""
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
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if new account creation is enabled
    new_accounts_enabled = get_app_setting('new_accounts_enabled', 'true') == 'true'
    allowed_emails = get_app_setting('allowed_emails', '').split(',')
    allowed_emails = [email.strip().lower() for email in allowed_emails if email.strip()]
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower()
        
        # Check if registration is disabled and email is not in allowed list
        if not new_accounts_enabled and email not in allowed_emails:
            flash('New account registration is currently disabled. Please contact the administrator.', 'error')
            return render_template('register.html', registration_disabled=True)
    
    # Show disabled message if registration is disabled and no email is being submitted
    if not new_accounts_enabled and request.method == 'GET':
        flash('New account registration is currently disabled. Please contact the administrator.', 'error')
        return render_template('register.html', registration_disabled=True)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        # Validate agreements
        agree_terms = request.form.get('agree_terms') == 'on'
        agree_privacy = request.form.get('agree_privacy') == 'on'
        agree_disclaimer = request.form.get('agree_disclaimer') == 'on'
        
        # Check if all agreements are accepted
        if not agree_terms:
            flash('You must agree to the Terms of Service', 'error')
            return render_template('register.html')
        
        if not agree_privacy:
            flash('You must agree to the Privacy Policy', 'error')
            return render_template('register.html')
        
        if not agree_disclaimer:
            flash('You must acknowledge the Medical Disclaimer', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            name=name,
            password_hash=generate_password_hash(password),
            agreed_to_terms=True,
            agreed_to_privacy=True,
            agreed_to_disclaimer=True,
            agreements_date=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

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
    return render_template('ai_coach.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get app statistics
    total_users = User.query.count()
    total_food_logs = FoodLog.query.count()
    total_water_logs = WaterLog.query.count()
    total_mood_logs = MoodLog.query.count()
    
    # Get app settings
    new_accounts_enabled = get_app_setting('new_accounts_enabled', 'true') == 'true'
    maintenance_mode = get_app_setting('maintenance_mode', 'false') == 'true'
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

@app.route('/api/admin/settings', methods=['POST'])
@login_required
def update_admin_settings():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
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

# Configure Ollama (local AI model)
OLLAMA_MODEL = "mistral"  # Faster and smaller than llama2
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
            'health_goals': current_user.health_goals
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
@login_required
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

        USER: {user_name} | Age: {user_age} | Goals: {user_goals}

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
        
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        ai_response = response['message']['content']
        
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
    """Generate enhanced AI response using fine-tuned model and RAG"""
    try:
        # Try to use fine-tuned model first
        try:
            response = ollama.chat(
                model=FINE_TUNED_MODEL,
                messages=[{"role": "user", "content": question}]
            )
            return response['message']['content']
        except:
            # Fallback to base model
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": question}]
            )
            return response['message']['content']
            
    except Exception as e:
        print(f"❌ Error generating enhanced response: {e}")
        return "I apologize, but I encountered an error while processing your request."

@app.route('/api/test-ollama')
@login_required
def test_ollama():
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "user", "content": "Say 'Hello, AI is working!'"}
            ]
        )
        
        return jsonify({'success': True, 'response': response['message']['content']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/warmup-ollama')
@login_required
def warmup_ollama():
    """Warm up the Ollama model for faster subsequent requests"""
    try:
        # Simple warmup call
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "user", "content": "Hello"}
            ]
        )
        return jsonify({'success': True, 'message': 'Model warmed up'})
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
            'health_goals': current_user.health_goals
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
@login_required
def ai_chat():
    try:
        data = request.get_json()
        message = data.get('message')
        context = data.get('context', {})
        context_type = data.get('context_type', 'minimal')
        chat_history = data.get('chat_history', [])
        
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
        
        # Call Ollama with simple timeout
        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            ai_response = response['message']['content']
            print(f"AI Chat - Response received, length: {len(ai_response)} characters")
            
            return jsonify({'success': True, 'response': ai_response})
            
        except Exception as ollama_error:
            print(f"AI Chat - Ollama error: {str(ollama_error)}")
            
            # Provide a helpful fallback response when Ollama is not available
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
    base_prompt = f"You are a supportive AI Health Coach for {profile_name}. Keep responses short, helpful, and actionable.\n\nQuestion: {message}\n\n"
    
    # Add only relevant context based on the specific question
    relevant_context = _extract_relevant_context(message, context, context_type)
    if relevant_context:
        base_prompt += f"Relevant Data: {relevant_context}\n"
        print(f"Extracted relevant context: {relevant_context}")
    else:
        print("No relevant context extracted")
    
    # Add relevant resources
    resources = get_relevant_resources(context_type, _determine_topic(message))
    if resources:
        base_prompt += format_resources_for_prompt(resources)
        print(f"Added {len(resources)} relevant resources")
    
    base_prompt += """Provide a short, helpful response (max 2-3 sentences) and include relevant links. Format your response as:
    
    [Your helpful response here]
    
    📚 Helpful Resources:
    - [Link 1: Brief description]
    - [Link 2: Brief description]
    
    Always include at least one link to our Medium blog (kiwellness.medium.com) when relevant, and cite authoritative health sources like Mayo Clinic, WebMD, or Harvard Health for medical advice."""
    
    # Limit prompt size to prevent timeouts
    if len(base_prompt) > 1000:
        print(f"Warning: Prompt too large ({len(base_prompt)} chars), truncating...")
        # Keep only essential parts
        base_prompt = f"""You are a supportive AI Health Coach for {profile_name}. Keep responses short, helpful, and actionable.

Question: {message}

Provide a short, helpful response (max 2-3 sentences) and include relevant links. Format your response as:

[Your helpful response here]

📚 Helpful Resources:
- [Link 1: Brief description]
- [Link 2: Brief description]

Always include at least one link to our Medium blog (kiwellness.medium.com) when relevant, and cite authoritative health sources like Mayo Clinic, WebMD, or Harvard Health for medical advice."""
    
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
                # Default food context
                relevant_parts.append(f"Logged {food_data.get('total_entries', 0)} meals")
        
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
                    relevant_parts.append("(below recommended 2000ml)")
                elif avg_daily > 3000:
                    relevant_parts.append("(above recommended)")
                    
            elif any(word in message_lower for word in ['increase', 'more', 'boost']):
                # For increasing water intake
                current_avg = water_data.get('avg_daily_water', 0)
                relevant_parts.append(f"Current daily avg: {current_avg:.0f}ml")
                
            else:
                # Default water context
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
    query_lower = query.lower()
    for food_key, food_data in COMMON_FOODS_DB.items():
        if query_lower in food_key or food_key in query_lower:
            fallback_results.append(food_data)
    
    # If we have good fallback results, return them immediately
    if len(fallback_results) >= 3:
        result = fallback_results[:8]
        food_search_cache[cache_key] = (result, current_time)
        return jsonify({'success': True, 'results': result, 'fast': True})
    
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
    
    # Combine results (fallback first, then USDA, then Open Food Facts)
    combined_results = fallback_results + usda_results + openfoodfacts_results
    
    # Remove duplicates based on name
    unique_results = []
    seen_names = set()
    for result in combined_results:
        if result['name'] not in seen_names:
            unique_results.append(result)
            seen_names.add(result['name'])
    
    final_results = unique_results[:8]
    
    # Cache the results
    food_search_cache[cache_key] = (final_results, current_time)
    
    return jsonify({
        'success': True,
        'results': final_results,
        'cached': False
    })

@app.route('/api/product/<barcode>')
@login_required
def get_product(barcode):
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 1:
            product = data['product']
            nutriments = product.get('nutriments', {})
            
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
            
            return jsonify({'success': True, 'product': result})
        else:
            return jsonify({'success': False, 'message': 'Product not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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

@app.route('/api/dashboard-data')
@login_required
def get_dashboard_data():
    date_str = request.args.get('date', date.today().isoformat())
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Get food logs
    food_logs = FoodLog.query.filter_by(
        user_id=current_user.id,
        date=selected_date
    ).all()
    
    # Get water logs
    water_logs = WaterLog.query.filter_by(
        user_id=current_user.id,
        date=selected_date
    ).all()
    
    # Get mood logs
    mood_logs = MoodLog.query.filter_by(
        user_id=current_user.id,
        date=selected_date
    ).all()
    
    # Get notes
    notes = Note.query.filter_by(
        user_id=current_user.id,
        date=selected_date
    ).order_by(Note.timestamp.desc()).all()
    
    # Calculate totals
    total_calories = sum(log.calories for log in food_logs)
    total_protein = sum(log.protein for log in food_logs)
    total_carbs = sum(log.carbs for log in food_logs)
    total_fat = sum(log.fat for log in food_logs)
    total_water = sum(log.amount for log in water_logs) * 8  # Convert cups to oz
    
    return jsonify({
        'success': True,
        'data': {
            'food_logs': [{
                'id': log.id,
                'name': log.name,
                'brand': log.brand,
                'calories': log.calories,
                'protein': log.protein,
                'carbs': log.carbs,
                'fat': log.fat,
                'time_of_day': log.time_of_day,
                'serving_size': log.serving_size,
                'original_amount': log.original_amount,
                'original_unit': log.original_unit,
                'quantity': log.quantity,
                'date': log.date.isoformat(),
                'timestamp': log.timestamp.isoformat()
            } for log in food_logs],
            'water_logs': [{
                'id': log.id,
                'amount': log.amount * 8,  # Convert to oz
                'timestamp': log.timestamp.isoformat()
            } for log in water_logs],
            'mood_logs': [{
                'id': log.id,
                'mood': log.mood,
                'timestamp': log.timestamp.isoformat()
            } for log in mood_logs],
            'notes': [{
                'id': note.id,
                'content': note.content,
                'timestamp': note.timestamp.isoformat()
            } for note in notes],
            'totals': {
                'calories': total_calories,
                'protein': total_protein,
                'carbs': total_carbs,
                'fat': total_fat,
                'water': total_water,
                'food_count': len(food_logs)
            }
        }
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
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Food item updated successfully'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update food item'})

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
    """Human help page with payment integration"""
    return render_template('human_help.html', stripe_publishable_key=STRIPE_PUBLISHABLE_KEY)

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """Create a Stripe payment intent"""
    try:
        data = request.get_json()
        payment_type = data.get('payment_type', '30min_session')
        amount = data.get('amount', 2000)  # Default to $20.00
        
        # Create payment session
        session_id = str(uuid.uuid4())
        payment_session = PaymentSession(
            session_id=session_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            email=data.get('email', ''),
            name=data.get('name', ''),
            payment_type=payment_type,
            amount=amount,
            status='pending'
        )
        db.session.add(payment_session)
        db.session.commit()
        
        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={
                'session_id': session_id,
                'payment_type': payment_type,
                'user_id': str(current_user.id) if current_user.is_authenticated else 'anonymous'
            }
        )
        
        return jsonify({
            'clientSecret': intent.client_secret,
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Error creating payment intent: {e}")
        return jsonify({'error': 'Failed to create payment intent'}), 500

@app.route('/payment-success')
def payment_success():
    """Handle successful payment and show success page"""
    try:
        payment_intent_id = request.args.get('payment_intent')
        
        if not payment_intent_id:
            return redirect(url_for('human_help'))
        
        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status != 'succeeded':
            return redirect(url_for('human_help'))
        
        # Find payment session
        payment_session = PaymentSession.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        
        if not payment_session:
            # Create payment session if not found
            payment_session = PaymentSession(
                session_id=str(uuid.uuid4()),
                user_id=current_user.id if current_user.is_authenticated else None,
                email=intent.receipt_email or '',
                name=intent.metadata.get('name', ''),
                payment_type=intent.metadata.get('payment_type', '30min_session'),
                stripe_payment_intent_id=payment_intent_id,
                amount=intent.amount,
                status='completed'
            )
            db.session.add(payment_session)
        else:
            # Update existing session
            payment_session.status = 'completed'
            payment_session.stripe_payment_intent_id = payment_intent_id
        
        db.session.commit()
        
        # Get app settings
        calendly_link = get_app_setting('calendly_link', 'https://calendly.com/ki-wellness/human-health-coach')
        
        return render_template('payment_success.html', 
                             payment_intent_id=payment_intent_id,
                             payment_amount=intent.amount,
                             payment_type=payment_session.payment_type,
                             payment_date=datetime.utcnow(),
                             calendly_link=calendly_link)
        
    except Exception as e:
        print(f"Error processing payment success: {e}")
        return redirect(url_for('human_help'))

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for payment status updates"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET', '')
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # Update payment session status
        payment_session = PaymentSession.query.filter_by(
            stripe_payment_intent_id=payment_intent['id']
        ).first()
        
        if payment_session:
            payment_session.status = 'completed'
            db.session.commit()
    
    return '', 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
        initialize_app_settings()
    
    app.run(debug=True)
