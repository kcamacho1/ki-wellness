from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Create SQLAlchemy instance
db = SQLAlchemy()

# Import models here to avoid circular imports
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    weight = db.Column(db.Float)  # in kg
    height = db.Column(db.Float)  # in cm
    health_goals = db.Column(db.Text)
    ailments_concerns = db.Column(db.Text)  # Ailments or areas of concern
    profile_image = db.Column(db.String(255))  # Path to profile image
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')  # 'admin', 'user', 'ff'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)  # Track user login activity
    
    # Agreement tracking
    agreed_to_terms = db.Column(db.Boolean, default=False)
    agreed_to_privacy = db.Column(db.Boolean, default=False)
    agreed_to_disclaimer = db.Column(db.Boolean, default=False)
    agreements_date = db.Column(db.DateTime)  # When agreements were accepted
    
    # Stripe customer ID for payments
    stripe_customer_id = db.Column(db.String(255))
    
    # Password reset fields
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    email_verification_expires = db.Column(db.DateTime, nullable=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='user', lazy=True)
    water_logs = db.relationship('WaterLog', backref='user', lazy=True)
    mood_logs = db.relationship('MoodLog', backref='user', lazy=True)
    notes = db.relationship('Note', backref='user', lazy=True)
    recipes = db.relationship('Recipe', backref='user', lazy=True)
    recipe_ratings = db.relationship('RecipeRating', backref='user', lazy=True)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    
    def is_admin_role(self):
        """Check if user has admin role"""
        return self.role == 'admin' or self.is_admin
    
    def is_ff_role(self):
        """Check if user has friends & family role"""
        return self.role == 'ff'
    
    def is_regular_user(self):
        """Check if user is a regular user (not admin or ff)"""
        return self.role == 'user'
    
    def has_premium_access(self):
        """Check if user has access to premium features"""
        # Admin and ff users always have premium access
        if self.is_admin_role() or self.is_ff_role():
            return True
        
        # Regular users need active premium subscription
        if self.is_regular_user():
            from datetime import datetime
            active_subscription = next((sub for sub in self.subscriptions if sub.status == 'active'), None)
            return active_subscription is not None
        
        return False
    
    def can_access_admin_dashboard(self):
        """Check if user can access admin dashboard"""
        return self.is_admin_role()

class FoodLog(db.Model):
    __tablename__ = 'food_log'
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
    original_unit = db.Column(db.String(50))
    quantity = db.Column(db.Float, default=1)
    date = db.Column(db.Date, nullable=False)
    time_of_day = db.Column(db.String(20), default='snack')  # breakfast, lunch, dinner, snack
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class WaterLog(db.Model):
    __tablename__ = 'water_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # in cups
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class MoodLog(db.Model):
    __tablename__ = 'mood_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood = db.Column(db.Integer, nullable=False)  # 1-5 scale
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Note(db.Model):
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Recipe models
class Recipe(db.Model):
    """Recipe model for storing user recipes"""
    __tablename__ = 'recipe'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    servings = db.Column(db.Integer, default=1)
    prep_time = db.Column(db.Integer)  # in minutes
    cook_time = db.Column(db.Integer)  # in minutes
    difficulty = db.Column(db.String(20))  # Easy, Medium, Hard
    category = db.Column(db.String(50))  # Breakfast, Lunch, Dinner, Snack
    is_favorite = db.Column(db.Boolean, default=False)
    image_path = db.Column(db.String(255))  # Path to recipe image
    is_public = db.Column(db.Boolean, default=False)  # Whether recipe is shared publicly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy=True, cascade='all, delete-orphan')
    instructions = db.relationship('RecipeInstruction', backref='recipe', lazy=True, cascade='all, delete-orphan', order_by='RecipeInstruction.step_number')
    ratings = db.relationship('RecipeRating', backref='recipe', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert recipe to dictionary with calculated nutrition"""
        total_calories = sum(ing.calories for ing in self.ingredients)
        total_protein = sum(ing.protein for ing in self.ingredients)
        total_carbs = sum(ing.carbs for ing in self.ingredients)
        total_fat = sum(ing.fat for ing in self.ingredients)
        total_fiber = sum(ing.fiber for ing in self.ingredients)
        total_sugar = sum(ing.sugar for ing in self.ingredients)
        total_sodium = sum(ing.sodium for ing in self.ingredients)
        
        # Calculate average rating
        avg_rating = 0
        rating_count = len(self.ratings)
        if rating_count > 0:
            avg_rating = sum(r.rating for r in self.ratings) / rating_count
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'servings': self.servings,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            'difficulty': self.difficulty,
            'category': self.category,
            'is_favorite': self.is_favorite,
            'image_path': self.image_path,
            'is_public': self.is_public,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'ingredients_count': len(self.ingredients),
            'ingredients': [ing.to_dict() for ing in self.ingredients],
            'instructions': [inst.to_dict() for inst in self.instructions],
            'avg_rating': round(avg_rating, 1),
            'rating_count': rating_count,
            'nutrition': {
                'calories': total_calories,
                'protein': total_protein,
                'carbs': total_carbs,
                'fat': total_fat,
                'fiber': total_fiber,
                'sugar': total_sugar,
                'sodium': total_sodium
            }
        }

class RecipeIngredient(db.Model):
    """Recipe ingredient model"""
    __tablename__ = 'recipe_ingredient'
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    food_name = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    serving_size_grams = db.Column(db.Float, default=0)  # Converted serving size in grams
    calories = db.Column(db.Float, default=0)
    protein = db.Column(db.Float, default=0)
    carbs = db.Column(db.Float, default=0)
    fat = db.Column(db.Float, default=0)
    fiber = db.Column(db.Float, default=0)
    sugar = db.Column(db.Float, default=0)
    sodium = db.Column(db.Float, default=0)
    
    # Optional: link to existing food data
    food_id = db.Column(db.Integer, db.ForeignKey('food_log.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'food_name': self.food_name,
            'amount': self.amount,
            'unit': self.unit,
            'serving_size_grams': self.serving_size_grams,
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fat': self.fat,
            'fiber': self.fiber,
            'sugar': self.sugar,
            'sodium': self.sodium
        }

class RecipeInstruction(db.Model):
    """Recipe instruction model"""
    __tablename__ = 'recipe_instruction'
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    instruction = db.Column(db.Text, nullable=False)
    
    def to_dict(self):
        return {
            'step_number': self.step_number,
            'instruction': self.instruction
        }

class RecipeRating(db.Model):
    """Recipe rating model"""
    __tablename__ = 'recipe_rating'
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review = db.Column(db.Text)  # Optional review text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one rating per user per recipe
    __table_args__ = (db.UniqueConstraint('recipe_id', 'user_id', name='unique_user_recipe_rating'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'recipe_id': self.recipe_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'review': self.review,
            'created_at': self.created_at.isoformat()
        }

class Subscription(db.Model):
    """Subscription model for managing user subscription plans"""
    __tablename__ = 'subscription'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), unique=True, nullable=False)
    stripe_customer_id = db.Column(db.String(255), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False, default='free')  # free, premium
    status = db.Column(db.String(50), nullable=False, default='active')  # active, canceled, past_due, unpaid
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'stripe_customer_id': self.stripe_customer_id,
            'plan_type': self.plan_type,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AIUsageLog(db.Model):
    """Track AI usage costs for analytics"""
    __tablename__ = 'ai_usage_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(255), nullable=False)  # Unique session identifier
    model_used = db.Column(db.String(255), nullable=False)  # Which model was used
    input_tokens = db.Column(db.Integer, nullable=False)    # Input token count
    output_tokens = db.Column(db.Integer, nullable=False)   # Output token count
    input_cost = db.Column(db.Numeric(10, 6), nullable=False)  # Input cost in USD
    output_cost = db.Column(db.Numeric(10, 6), nullable=False)   # Output cost in USD
    total_cost = db.Column(db.Numeric(10, 6), nullable=False)  # Total cost in USD
    endpoint = db.Column(db.String(100), nullable=False)   # Which endpoint was used
    response_time_ms = db.Column(db.Integer)               # Response time in milliseconds
    success = db.Column(db.Boolean, default=True)          # Whether the request succeeded
    error_message = db.Column(db.Text)                     # Error message if failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ai_usage_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'model_used': self.model_used,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'input_cost': float(self.input_cost),
            'output_cost': float(self.output_cost),
            'total_cost': float(self.total_cost),
            'endpoint': self.endpoint,
            'response_time_ms': self.response_time_ms,
            'success': self.success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RevenueLog(db.Model):
    """Track revenue from subscriptions and health coaching sessions"""
    __tablename__ = 'revenue_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be null for anonymous sessions
    revenue_type = db.Column(db.String(50), nullable=False)  # 'subscription', 'health_coaching', 'other'
    amount = db.Column(db.Numeric(10, 2), nullable=False)    # Amount in USD
    currency = db.Column(db.String(3), default='USD')
    stripe_payment_intent_id = db.Column(db.String(255))     # Stripe payment intent ID
    stripe_subscription_id = db.Column(db.String(255))       # Stripe subscription ID
    description = db.Column(db.Text)                         # Description of the revenue
    status = db.Column(db.String(50), default='completed')   # 'pending', 'completed', 'failed', 'refunded'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='revenue_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'revenue_type': self.revenue_type,
            'amount': float(self.amount),
            'currency': self.currency,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in ['active', 'trialing'] and not self.cancel_at_period_end
    
    @property
    def is_premium(self):
        """Check if user has premium access"""
        return self.is_active and self.plan_type == 'premium'


class AppSettings(db.Model):
    """Application settings model"""
    __tablename__ = 'app_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaymentSession(db.Model):
    """Payment session model for tracking human help payments"""
    __tablename__ = 'payment_session'
    
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


class AIAnalysis(db.Model):
    """AI analysis results for users"""
    __tablename__ = 'ai_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    analysis_data = db.Column(db.Text, nullable=False)  # JSON string of analysis
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
