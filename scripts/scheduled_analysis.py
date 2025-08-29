#!/usr/bin/env python3
"""
Weekly Analysis Generator for Ki Wellness
Runs every Monday to generate AI analysis for all users based on the past 7 days
"""

import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from services.openrouter_client import get_openrouter_client
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

# OpenRouter configuration
OPENROUTER_MODEL = os.getenv('MODEL', 'openai/gpt-4o-mini')

def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

def get_user_data(session, user_id, start_date, end_date):
    """Get user data for analysis"""
    # Get user profile
    user_result = session.execute(
        text('SELECT name, age, weight, height, health_goals, ailments_concerns FROM "user" WHERE "id" = :user_id'),
        {"user_id": user_id}
    ).fetchone()
    
    if not user_result:
        return None
    
    user_profile = {
        'name': user_result[0],
        'age': user_result[1],
        'weight': user_result[2],
        'height': user_result[3],
        'health_goals': user_result[4],
        'ailments_concerns': user_result[5]
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
    
    # Prepare user info to avoid f-string nesting issues
    user_name = user_data.get('profile', {}).get('name', 'User')
    user_goals = user_data.get('profile', {}).get('health_goals', 'Not specified')
    user_concerns = user_data.get('profile', {}).get('ailments_concerns', 'Not specified')
    
    analysis_prompt = f"""
    Weekly Health Coach Analysis - concise, evidence-based, grounded in local knowledge.

    User: {user_name}
    Goals: {user_goals}
    Health Concerns: {user_concerns}
    
    Data Summary (past 7 days):
    - {food_summary}
    - {water_summary}
    - {mood_summary}

    Task:
    - Find specific, data-backed patterns from the past 7 days connecting mood & notes to food & water intake.
    - Provide short reasons for how the user may be feeling based on these weekly patterns.
    - Create 2-3 actionable, personalized suggestions to try this upcoming week with brief source citations when helpful.

    If the user has little or no data for the past 7 days, provide encouragement to continue logging and basic wellness tips.

    OUTPUT STRICT JSON ONLY:
    {{
      "patterns": [
        {{"title": "Pattern Title", "description": "Brief explanation of weekly correlation (mood vs notes, food, water)."}}
      ],
      "suggestions": [
        {{
          "title": "Suggestion Title",
          "description": "Brief, actionable advice for the upcoming week.",
          "sources": [
            {{"title": "Short Source Name", "url": "https://example.com"}}
          ]
        }}
      ]
    }}
    """
    
    try:
        client = get_openrouter_client()
        ai_response = client.generate_response(
            prompt=analysis_prompt,
            model=OPENROUTER_MODEL,
            max_tokens=800
        )
        
        # Parse the JSON response
        try:
            analysis = json.loads(ai_response)
            return analysis
        except json.JSONDecodeError:
            # Fallback analysis
            return {
                "patterns": [
                    {"title": "Weekly Check-in", "description": "Welcome to your weekly AI Health Coach analysis! Continue logging your food, water, and mood this week to get personalized insights."}
                ],
                "suggestions": [
                    {"title": "Build Consistency", "description": "Try to log at least one meal and your mood daily this week to establish patterns."},
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
        
        # Calculate date range (last 7 days for weekly analysis)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        print(f"Generating weekly analysis for {len(users)} users (last 7 days: {start_date} to {end_date})...")
        
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
