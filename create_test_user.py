#!/usr/bin/env python3
"""
Create a test user for AI chat testing
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, FoodLog, WaterLog, MoodLog, Note
from werkzeug.security import generate_password_hash

def create_test_user():
    """Create a test user with some sample data"""
    
    with app.app_context():
        try:
            print("Creating test user and sample data...")
            
            # Check if test user already exists
            test_user = User.query.filter_by(username='test_user').first()
            if test_user:
                print("✓ Test user already exists")
                return test_user.id
            
            # Create test user
            test_user = User(
                username='test_user',
                email='test@example.com',
                name='Test User',
                age=30,
                weight=70.0,
                height=170.0,
                health_goals='Lose weight and improve mood',
                # Auto-agreement for test user
                agreed_to_terms=True,
                agreed_to_privacy=True,
                agreed_to_disclaimer=True,
                agreements_date=datetime.utcnow()
            )
            test_user.password_hash = generate_password_hash('test_password')
            
            db.session.add(test_user)
            db.session.commit()
            
            print("✓ Test user created successfully")
            
            # Add some sample food logs
            today = datetime.now().date()
            for i in range(5):
                date = today - timedelta(days=i)
                food_log = FoodLog(
                    user_id=test_user.id,
                    name=f'Sample Food {i+1}',
                    brand='Test Brand',
                    calories=300 + (i * 50),
                    protein=20 + i,
                    carbs=30 + i,
                    fat=10 + i,
                    time_of_day='lunch',
                    date=date,
                    quantity=1
                )
                db.session.add(food_log)
            
            # Add some sample water logs
            for i in range(7):
                date = today - timedelta(days=i)
                water_log = WaterLog(
                    user_id=test_user.id,
                    amount=2000 + (i * 100),
                    date=date
                )
                db.session.add(water_log)
            
            # Add some sample mood logs
            for i in range(7):
                date = today - timedelta(days=i)
                mood_log = MoodLog(
                    user_id=test_user.id,
                    mood=7 + (i % 3),  # Mood between 7-9
                    date=date
                )
                db.session.add(mood_log)
            
            # Add some sample notes
            for i in range(3):
                date = today - timedelta(days=i)
                note = Note(
                    user_id=test_user.id,
                    content=f'Sample note {i+1}: Feeling good today!',
                    date=date
                )
                db.session.add(note)
            
            db.session.commit()
            print("✓ Sample data created successfully")
            
            return test_user.id
            
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    create_test_user()
