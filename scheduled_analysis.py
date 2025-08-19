#!/usr/bin/env python3
"""
Scheduled Analysis Generator for Ki Wellness
Runs every Monday at midnight to pre-generate AI analysis for all users
"""

import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import ollama
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Database configuration
if os.getenv('DATABASE_URL'):
    # Production - PostgreSQL
    DATABASE_URL = os.getenv('DATABASE_URL')
else:
    # Development - SQLite
    DATABASE_URL = 'sqlite:///ki_wellness.db'

# Ollama configuration
OLLAMA_MODEL = "mistral"

def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

def get_user_data(session, user_id, start_date, end_date):
    """Get user data for analysis"""
    # Get user profile
    user_result = session.execute(
        text('SELECT name, age, weight, height, health_goals FROM "user" WHERE "id" = :user_id'),
        {"user_id": user_id}
    ).fetchone()
    
    if not user_result:
        return None
    
    user_profile = {
        'name': user_result[0],
        'age': user_result[1],
        'weight': user_result[2],
        'height': user_result[3],
        'health_goals': user_result[4]
    }
    
    # Get food logs
    food_logs = session.execute(
        text("""
            SELECT name, brand, calories, protein, carbs, fat, time_of_day, quantity 
            FROM food_log 
            WHERE user_id = :user_id AND date >= :start_date AND date <= :end_date
        """),
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
    ).fetchall()
    
    # Get water logs
    water_logs = session.execute(
        text("""
            SELECT amount FROM water_log 
            WHERE user_id = :user_id AND date >= :start_date AND date <= :end_date
        """),
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
    ).fetchall()
    
    # Get mood logs
    mood_logs = session.execute(
        text("""
            SELECT mood FROM mood_log 
            WHERE user_id = :user_id AND date >= :start_date AND date <= :end_date
        """),
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
    ).fetchall()
    
    # Get notes
    notes = session.execute(
        text("""
            SELECT content, date FROM note 
            WHERE user_id = :user_id AND date >= :start_date AND date <= :end_date
        """),
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
    ).fetchall()

    return {
        'profile': user_profile,
        'food_logs': [dict(zip(['name', 'brand', 'calories', 'protein', 'carbs', 'fat', 'time_of_day', 'quantity'], row)) for row in food_logs],
        'water_logs': [{'amount': row[0]} for row in water_logs],
        'mood_logs': [{'mood': row[0]} for row in mood_logs],
        'notes': [dict(zip(['content', 'date'], row)) for row in notes]
    }

def generate_analysis(user_data):
    """Generate AI analysis for user data"""
    if not user_data:
        return None
    
    # Prepare data for AI analysis - optimized for speed
    food_summary = f"Total food entries: {len(user_data.get('food_logs', []))}"
    water_summary = f"Total water entries: {len(user_data.get('water_logs', []))}"
    mood_summary = f"Total mood entries: {len(user_data.get('mood_logs', []))}"
    
    analysis_prompt = f"""
    Health Coach Analysis - concise, evidence-based, grounded in local knowledge.

    User: {user_data.get('profile', {}).get('name', 'User')}
    Goals: {user_data.get('profile', {}).get('health_goals', 'Not specified')}
    
    Data Summary:
    - {food_summary}
    - {water_summary}
    - {mood_summary}

    Task:
    - Find specific, data-backed patterns connecting mood & notes to food & water intake.
    - Provide short reasons for how the user may be feeling based on these links.
    - Create 2-3 actionable, personalized suggestions to try this week with brief source citations.

    OUTPUT STRICT JSON ONLY:
    {
      "patterns": [
        {"title": "Pattern Title", "description": "Brief explanation of correlation (mood vs notes, food, water)."}
      ],
      "suggestions": [
        {
          "title": "Suggestion Title",
          "description": "Brief, actionable advice.",
          "sources": [
            {"title": "Short Source Name", "url": "https://example.com"}
          ]
        }
      ]
    }
    """
    
    try:
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
            return analysis
        except json.JSONDecodeError:
            # Fallback analysis
            return {
                "patterns": [
                    {"title": "Getting Started", "description": "Welcome to your AI Health Coach! Start logging your food, water, and mood to get personalized insights."}
                ],
                "suggestions": [
                    {"title": "Complete Your Profile", "description": "Add your health goals to your profile to get personalized suggestions."}
                ]
            }
    except Exception as e:
        print(f"Error generating analysis: {e}")
        return None

def store_analysis(session, user_id, analysis):
    """Store analysis in database"""
    try:
        # Check if analysis already exists for this user
        existing = session.execute(
            text("SELECT id FROM ai_analysis WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        
        if existing:
            # Update existing analysis
            session.execute(
                text("""
                    UPDATE ai_analysis 
                    SET analysis_data = :analysis_data, updated_at = :updated_at 
                    WHERE user_id = :user_id
                """),
                {
                    "analysis_data": json.dumps(analysis),
                    "updated_at": datetime.utcnow(),
                    "user_id": user_id
                }
            )
        else:
            # Insert new analysis
            session.execute(
                text("""
                    INSERT INTO ai_analysis (user_id, analysis_data, created_at, updated_at)
                    VALUES (:user_id, :analysis_data, :created_at, :updated_at)
                """),
                {
                    "user_id": user_id,
                    "analysis_data": json.dumps(analysis),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
        
        session.commit()
        return True
    except Exception as e:
        print(f"Error storing analysis: {e}")
        session.rollback()
        return False

def create_analysis_table(session):
    """Create analysis table if it doesn't exist"""
    try:
        # Check if we're using PostgreSQL or SQLite
        if 'postgresql' in DATABASE_URL:
            # PostgreSQL syntax
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    analysis_data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES "user" (id)
                )
            """))
        else:
            # SQLite syntax
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    analysis_data TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """))
        session.commit()
    except Exception as e:
        print(f"Error creating analysis table: {e}")

def main():
    """Main function to generate analysis for all users"""
    print(f"Starting scheduled analysis generation at {datetime.now()}")
    
    session = get_db_session()
    
    try:
        # Create analysis table if it doesn't exist
        create_analysis_table(session)
        
        # Get all users
        users = session.execute(text('SELECT "id" FROM "user"')).fetchall()
        
        # Calculate date range (last 30 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        print(f"Generating analysis for {len(users)} users...")
        
        for user_row in users:
            user_id = user_row[0]
            print(f"Processing user {user_id}...")
            
            # Get user data
            user_data = get_user_data(session, user_id, start_date, end_date)
            
            if user_data:
                # Generate analysis
                analysis = generate_analysis(user_data)
                
                if analysis:
                    # Store analysis
                    if store_analysis(session, user_id, analysis):
                        print(f"✓ Analysis stored for user {user_id}")
                    else:
                        print(f"✗ Failed to store analysis for user {user_id}")
                else:
                    print(f"✗ Failed to generate analysis for user {user_id}")
            else:
                print(f"✗ No data found for user {user_id}")
        
        print("Scheduled analysis generation completed!")
        
    except Exception as e:
        print(f"Error in scheduled analysis: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
