#!/usr/bin/env python3
"""
Ki Wellness - Database Schema Verification
=========================================

This script verifies that all database tables have the correct schema
by comparing the actual database columns with the SQLAlchemy model definitions.

Usage:
    python cleanup_backup/verify_database_schema.py

Author: Ki Wellness Team
"""

import os
import sys
from sqlalchemy import text, inspect
from sqlalchemy.exc import ProgrammingError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_model_columns():
    """Get expected columns from SQLAlchemy models"""
    try:
        from app.models import User, UserProfile, FoodJournal, MoodEntry, PatternsCache, Review, UserAgreement, Reminder, ReminderLog, Notification, SystemSettings, TokenUsage, APICosts, UserSubscription, SessionCredits, AIUsageSession
        
        models = {
            'users': User,
            'user_profiles': UserProfile,
            'food_journal': FoodJournal,
            'mood_entries': MoodEntry,
            'patterns_cache': PatternsCache,
            'reviews': Review,
            'user_agreements': UserAgreement,
            'reminders': Reminder,
            'reminder_logs': ReminderLog,
            'notifications': Notification,
            'system_settings': SystemSettings,
            'token_usage': TokenUsage,
            'api_costs': APICosts,
            'user_subscriptions': UserSubscription,
            'session_credits': SessionCredits,
            'ai_usage_sessions': AIUsageSession
        }
        
        expected_columns = {}
        for table_name, model in models.items():
            expected_columns[table_name] = [column.name for column in model.__table__.columns]
        
        return expected_columns
        
    except Exception as e:
        print(f"❌ Error getting model columns: {e}")
        return {}

def get_actual_columns(engine):
    """Get actual columns from database"""
    try:
        inspector = inspect(engine)
        actual_columns = {}
        
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            actual_columns[table_name] = [col['name'] for col in columns]
        
        return actual_columns
        
    except Exception as e:
        print(f"❌ Error getting actual columns: {e}")
        return {}

def compare_schemas(expected_columns, actual_columns):
    """Compare expected vs actual database schemas"""
    issues = []
    
    for table_name, expected_cols in expected_columns.items():
        if table_name not in actual_columns:
            issues.append(f"❌ Table '{table_name}' missing from database")
            continue
        
        actual_cols = actual_columns[table_name]
        missing_cols = set(expected_cols) - set(actual_cols)
        extra_cols = set(actual_cols) - set(expected_cols)
        
        if missing_cols:
            issues.append(f"⚠️  Table '{table_name}' missing columns: {list(missing_cols)}")
        
        if extra_cols:
            issues.append(f"ℹ️  Table '{table_name}' has extra columns: {list(extra_cols)}")
    
    return issues

def verify_database_schema():
    """Verify database schema matches models"""
    
    try:
        # Import Flask app and database
        from app.main import app, db
        
        with app.app_context():
            print("🔍 Verifying database schema...")
            
            # Get database connection
            engine = db.engine
            
            # Get expected columns from models
            expected_columns = get_model_columns()
            if not expected_columns:
                print("❌ Failed to get expected columns from models")
                return False
            
            print(f"📋 Found {len(expected_columns)} model tables")
            
            # Get actual columns from database
            actual_columns = get_actual_columns(engine)
            if not actual_columns:
                print("❌ Failed to get actual columns from database")
                return False
            
            print(f"📋 Found {len(actual_columns)} database tables")
            
            # Compare schemas
            issues = compare_schemas(expected_columns, actual_columns)
            
            if not issues:
                print("✅ Database schema matches models perfectly!")
                return True
            
            print("\n📊 Schema Issues Found:")
            for issue in issues:
                print(f"  {issue}")
            
            return len([i for i in issues if i.startswith("❌")]) == 0
                    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 Ki Wellness - Database Schema Verification")
    print("=" * 50)
    
    success = verify_database_schema()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Schema verification completed successfully")
        return True
    else:
        print("❌ Schema verification found issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
