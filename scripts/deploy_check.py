#!/usr/bin/env python3
"""
Deployment check script for Ki Wellness
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check environment variables"""
    print("🔍 Checking Environment Variables")
    print("=" * 40)
    
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'OPENROUTER_API_KEY'
    ]
    
    optional_vars = [
        'USDA_API_KEY',
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY'
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}...")
        else:
            print(f"❌ {var}: Not set")
            all_good = False
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}...")
        else:
            print(f"⚠️  {var}: Not set (optional)")
    
    return all_good

def check_dependencies():
    """Check Python dependencies"""
    print("\n🔍 Checking Dependencies")
    print("=" * 40)
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'psycopg',
        'dotenv',
        'requests',
        'werkzeug'
    ]
    
    all_good = True
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}: Not installed")
            all_good = False
    
    return all_good

def check_database():
    """Check database connection"""
    print("\n🔍 Checking Database")
    print("=" * 40)
    
    try:
        import psycopg
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            print("❌ DATABASE_URL not set")
            return False
        
        conn = psycopg.connect(database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection: {version[0][:50]}...")
        
        # Check user table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' AND table_schema = 'public'
        """)
        columns = [column[0] for column in cursor.fetchall()]
        
        if 'reset_token' in columns and 'reset_token_expires' in columns:
            print("✅ Password reset columns exist")
        else:
            print("❌ Password reset columns missing")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_app_import():
    """Check if the Flask app can be imported"""
    print("\n🔍 Checking Flask App")
    print("=" * 40)
    
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app import app
        print("✅ Flask app imports successfully")
        
        with app.app_context():
            from database import db, User
            print("✅ Database models import successfully")
            
            # Test basic query
            user_count = User.query.count()
            print(f"✅ Database query works: {user_count} users found")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app check failed: {e}")
        return False

def main():
    """Main deployment check"""
    print("🚀 Ki Wellness Deployment Check")
    print("=" * 50)
    
    env_ok = check_environment()
    deps_ok = check_dependencies()
    db_ok = check_database()
    app_ok = check_app_import()
    
    print("\n📊 Deployment Check Results")
    print("=" * 40)
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"Database: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"Flask App: {'✅ PASS' if app_ok else '❌ FAIL'}")
    
    if all([env_ok, deps_ok, db_ok, app_ok]):
        print("\n🎉 All checks passed! Ready for deployment.")
        return True
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
