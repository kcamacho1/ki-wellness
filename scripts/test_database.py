#!/usr/bin/env python3
"""
Test database connection and identify issues
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing Database Connection")
    print("=" * 40)
    
    # Check DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    print(f"✅ DATABASE_URL found: {database_url[:30]}...")
    
    try:
        # Test psycopg connection
        import psycopg
        print("✅ psycopg imported successfully")
        
        # Test connection
        conn = psycopg.connect(database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection successful: {version[0][:50]}...")
        
        # Test user table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' AND table_schema = 'public'
        """)
        columns = [column[0] for column in cursor.fetchall()]
        print(f"✅ User table found with {len(columns)} columns")
        
        # Check for password reset columns
        if 'reset_token' in columns:
            print("✅ reset_token column exists")
        else:
            print("❌ reset_token column missing")
            
        if 'reset_token_expires' in columns:
            print("✅ reset_token_expires column exists")
        else:
            print("❌ reset_token_expires column missing")
        
        conn.close()
        return True
        
    except ImportError as e:
        print(f"❌ psycopg import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_flask_app():
    """Test Flask app initialization"""
    print("\n🔍 Testing Flask App")
    print("=" * 40)
    
    try:
        # Add current directory to path
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Import Flask app
        from app import app
        print("✅ Flask app imported successfully")
        
        # Test database initialization
        with app.app_context():
            from database import db
            print("✅ Database object imported successfully")
            
            # Test basic query
            from database import User
            user_count = User.query.count()
            print(f"✅ Database query successful: {user_count} users found")
            
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Ki Wellness Database Test")
    print("=" * 50)
    
    db_test = test_database_connection()
    flask_test = test_flask_app()
    
    print("\n📊 Test Results")
    print("=" * 30)
    print(f"Database Connection: {'✅ PASS' if db_test else '❌ FAIL'}")
    print(f"Flask App: {'✅ PASS' if flask_test else '❌ FAIL'}")
    
    if db_test and flask_test:
        print("\n🎉 All tests passed! The application should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
