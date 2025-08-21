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
    recipes = db.relationship('Recipe', backref='user', lazy=True)
    recipe_ratings = db.relationship('RecipeRating', backref='user', lazy=True)

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
