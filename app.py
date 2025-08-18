import os
import requests
import json
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import sqlite3
import ollama

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
if os.getenv('DATABASE_URL'):
    # Production - PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
else:
    # Development - SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ki_wellness.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# API Configuration
OPENFOODFACTS_API = "https://world.openfoodfacts.org/cgi/search.pl"
USDA_API_KEY = os.getenv('USDA_API_KEY')
USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"

# Basic foods to prioritize USDA search
BASIC_FOODS = ['apple', 'banana', 'chicken', 'rice', 'bread', 'milk', 'eggs', 'beef', 'fish', 'pork', 'carrot', 'broccoli', 'spinach', 'tomato', 'potato', 'onion', 'garlic', 'cilantro', 'coriander']

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
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Admin user '{admin_username}' created successfully")

def search_usda_api(query):
    """Search USDA FoodData Central API"""
    if not USDA_API_KEY:
        return []
    
    try:
        url = f"{USDA_API_BASE}/foods/search"
        params = {
            'api_key': USDA_API_KEY,
            'query': query,
            'pageSize': 5,
            'dataType': 'Foundation',
            'sortBy': 'dataType.keyword',
            'sortOrder': 'asc'
        }
        
        response = requests.get(url, params=params, timeout=10)
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
        if query.lower() in ['chicken', 'apple', 'banana']:
            search_terms.extend([f'fresh {query}', f'{query} raw', f'{query} natural'])
        
        all_results = []
        for search_term in search_terms:
            params = {
                'search_terms': search_term,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 10
            }
            
            response = requests.get(OPENFOODFACTS_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for product in data.get('products', []):
                # Skip products without nutrition data
                if not product.get('nutriments'):
                    continue
                
                nutriments = product['nutriments']
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
                
                # Filter out processed products for basic foods
                if query.lower() in ['chicken', 'apple', 'banana']:
                    product_name = result['name'].lower()
                    if any(exclude in product_name for exclude in ['broth', 'soup', 'juice', 'sauce', 'candy', 'chips']):
                        continue
                
                all_results.append(result)
        
        # Remove duplicates and sort by relevance
        unique_results = []
        seen_names = set()
        for result in all_results:
            if result['name'] not in seen_names:
                unique_results.append(result)
                seen_names.add(result['name'])
        
        return unique_results[:7]  # Return up to 7 results
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
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
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
            password_hash=generate_password_hash(password)
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

@app.route('/daily-log')
@login_required
def daily_log():
    return render_template('daily_log.html')

@app.route('/ai-coach')
@login_required
def ai_coach():
    return render_template('ai_coach.html')

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
        
        analysis_prompt = f"""
        Health Coach Analysis - Be concise and actionable.

        USER: {profile.get('name', 'User')} | Age: {profile.get('age', 'N/A')} | Goals: {profile.get('health_goals', 'Not specified')}

        DATA SUMMARY:
        Food: {len(food_logs)} entries, {avg_calories:.0f} avg cal/day
        Water: {len(water_logs)} entries, {avg_water:.1f} cups/day
        Mood: {len(mood_logs)} entries, {avg_mood:.1f}/5 avg
        Notes: {len(notes)} entries

        RECENT ACTIVITY:
        Food: {[f"{log.get('name', 'Unknown')} ({log.get('time_of_day', 'snack')})" for log in recent_foods]}
        Mood: {[log.get('mood') for log in mood_logs[-2:]]}
        Notes: {[note.get('content', '')[:50] + '...' if len(note.get('content', '')) > 50 else note.get('content', '') for note in recent_notes]}

        Provide 2-3 specific patterns and 2-3 actionable suggestions based on this data.

        JSON format:
        {{
            "patterns": [
                {{"title": "Pattern Title", "description": "Brief description"}}
            ],
            "suggestions": [
                {{"title": "Suggestion Title", "description": "Brief actionable advice"}}
            ]
        }}
        """
        
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

@app.route('/api/ai-chat', methods=['POST'])
@login_required
def ai_chat():
    try:
        data = request.get_json()
        message = data.get('message')
        user_data = data.get('user_data')
        analysis = data.get('analysis')
        chat_history = data.get('chat_history', [])
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'})
        
        # Prepare context for the AI
        context = f"""
        You are a supportive and knowledgeable AI Health Coach for a wellness app. The user's name is {user_data.get('profile', {}).get('name', 'User')}.
        
        User Profile:
        - Age: {user_data.get('profile', {}).get('age', 'Not specified')}
        - Weight: {user_data.get('profile', {}).get('weight', 'Not specified')} kg
        - Height: {user_data.get('profile', {}).get('height', 'Not specified')} cm
        - Health Goals: {user_data.get('profile', {}).get('health_goals', 'Not specified')}
        
        Recent Analysis:
        Patterns: {json.dumps(analysis.get('patterns', []) if analysis else [], indent=2)}
        Suggestions: {json.dumps(analysis.get('suggestions', []) if analysis else [], indent=2)}
        
        Chat History:
        {json.dumps(chat_history, indent=2)}
        
        User's current question: {message}
        
        Provide a helpful, encouraging, and actionable response. Be conversational but professional. 
        Reference their specific data when relevant and provide practical advice.
        """
        
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "user", "content": context}
            ]
        )
        
        ai_response = response['message']['content']
        
        return jsonify({'success': True, 'response': ai_response})
        
    except Exception as e:
        print(f"AI Chat Error: {str(e)}")  # Add debugging
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/search-food', methods=['POST'])
@login_required
def search_food():
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'message': 'Query is required'})
    
    # Determine if this is a basic food
    is_basic_food = any(basic_food in query.lower() for basic_food in BASIC_FOODS)
    
    # Search USDA first for basic foods
    usda_results = []
    if is_basic_food and USDA_API_KEY:
        usda_results = search_usda_api(query)
    
    # Search Open Food Facts
    openfoodfacts_results = search_openfoodfacts_api(query)
    
    # Combine results (USDA first, then Open Food Facts)
    combined_results = usda_results + openfoodfacts_results
    
    return jsonify({
        'success': True,
        'results': combined_results[:5]  # Return top 5 results
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
    data = request.get_json()
    
    # Check if note already exists for today
    existing_note = Note.query.filter_by(
        user_id=current_user.id,
        date=datetime.strptime(data['date'], '%Y-%m-%d').date()
    ).first()
    
    if existing_note:
        existing_note.content = data['content']
        # Update the timestamp to reflect the time of this save
        existing_note.timestamp = datetime.utcnow()
    else:
        note = Note(
            user_id=current_user.id,
            content=data['content'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            timestamp=datetime.utcnow()
        )
        db.session.add(note)
    
    db.session.commit()
    return jsonify({'success': True})

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
    note = Note.query.filter_by(
        user_id=current_user.id,
        date=selected_date
    ).first()
    
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
            'notes': ({
                'content': note.content,
                'timestamp': note.timestamp.isoformat()
            } if note else ''),
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
            'is_admin': current_user.is_admin
        }
    })

@app.route('/api/food-log/<int:food_id>', methods=['DELETE'])
@login_required
def delete_food_log(food_id):
    food_log = FoodLog.query.filter_by(id=food_id, user_id=current_user.id).first()
    
    if not food_log:
        return jsonify({'success': False, 'message': 'Food log not found'})
    
    db.session.delete(food_log)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    
    app.run(debug=True)
