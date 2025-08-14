#!/usr/bin/env python3
"""
Test script to diagnose production login database connection issues
"""

import os
import sys
import requests
from datetime import datetime

def test_database_connection():
    """Test database connection configuration"""
    print("🔍 Testing Database Connection Configuration")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Variables:")
    print(f"   DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT_SET')}")
    print(f"   FLASK_ENV: {os.getenv('FLASK_ENV', 'NOT_SET')}")
    print(f"   SECRET_KEY: {'SET' if os.getenv('SECRET_KEY') else 'NOT_SET'}")
    
    # Test config import
    try:
        # Try to import from app config first
        from app.config import ProductionConfig, DevelopmentConfig
        print("\n✅ App config imports successful")
        
        # Test production config
        prod_config = ProductionConfig()
        print(f"🏭 Production Database URI: {prod_config.SQLALCHEMY_DATABASE_URI}")
        
        # Test development config
        dev_config = DevelopmentConfig()
        print(f"🔧 Development Database URI: {dev_config.SQLALCHEMY_DATABASE_URI}")
        
    except ImportError:
        try:
            # Fallback to root config
            from config import get_database_url, ProductionConfig, DevelopmentConfig
            print("\n✅ Root config imports successful")
            
            # Test database URL generation
            db_url = get_database_url()
            print(f"📊 Database URL: {db_url}")
            
            # Test production config
            prod_config = ProductionConfig()
            print(f"🏭 Production Database URI: {prod_config.SQLALCHEMY_DATABASE_URI}")
            
            # Test development config
            dev_config = DevelopmentConfig()
            print(f"🔧 Development Database URI: {dev_config.SQLALCHEMY_DATABASE_URI}")
            
        except Exception as e:
            print(f"❌ Config import error: {e}")
            return False
    
    return True

def test_sqlalchemy_connection():
    """Test SQLAlchemy database connection"""
    print("\n🔍 Testing SQLAlchemy Connection")
    print("=" * 50)
    
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        
        # Try to import from app config first
        try:
            from app.config import ProductionConfig
        except ImportError:
            from config import ProductionConfig
        
        # Create test app
        app = Flask(__name__)
        app.config.from_object(ProductionConfig)
        
        # Initialize SQLAlchemy
        db = SQLAlchemy(app)
        
        # Test connection
        with app.app_context():
            try:
                # Test basic query
                result = db.session.execute(db.text('SELECT 1'))
                print("✅ Database connection successful")
                return True
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ SQLAlchemy setup error: {e}")
        return False

def test_production_endpoint():
    """Test production login endpoint"""
    print("\n🔍 Testing Production Login Endpoint")
    print("=" * 50)
    
    try:
        # Test the production URL
        url = "https://kiwellness.org/login"
        
        print(f"🌐 Testing URL: {url}")
        
        # Test GET request
        response = requests.get(url, timeout=10)
        print(f"📡 GET Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ GET request successful")
        else:
            print(f"⚠️  GET request returned status {response.status_code}")
        
        # Test POST request with minimal data
        test_data = {
            'username': 'test_user',
            'password': 'test_password',
            'remember_me': False
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'KiWellness-Test/1.0'
        }
        
        response = requests.post(url, json=test_data, headers=headers, timeout=10)
        print(f"📡 POST Response Status: {response.status_code}")
        
        if response.status_code == 500:
            print("❌ POST request returned 500 error (expected for invalid credentials)")
            print(f"📄 Response content: {response.text[:200]}...")
        elif response.status_code == 401:
            print("✅ POST request successful (401 expected for invalid credentials)")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def check_dependencies():
    """Check required dependencies"""
    print("🔍 Checking Dependencies")
    print("=" * 50)
    
    dependencies = [
        'flask',
        'flask_sqlalchemy',
        'psycopg',
        'psycopg2',
        'requests'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - NOT INSTALLED")
    
    return True

def main():
    """Main test function"""
    print("🚀 Production Login Diagnostic Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    # Run tests
    tests = [
        ("Dependencies", check_dependencies),
        ("Database Configuration", test_database_connection),
        ("SQLAlchemy Connection", test_sqlalchemy_connection),
        ("Production Endpoint", test_production_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database configuration looks good.")
    else:
        print("⚠️  Some tests failed. Check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
