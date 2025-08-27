"""
Initialize the Ki Wellness database with all required tables
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from database import User, FoodLog, WaterLog, MoodLog, Note, Recipe, RecipeIngredient, RecipeInstruction, Subscription

def init_database():
    """Initialize the database with all tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database initialized successfully!")
        print("All tables created:")
        
        # List all tables using SQLAlchemy inspection
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        for table in tables:
            print(f"  - {table}")

if __name__ == "__main__":
    init_database()
