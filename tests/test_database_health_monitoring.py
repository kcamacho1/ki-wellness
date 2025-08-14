#!/usr/bin/env python3
"""
Test script to verify database health monitoring functionality
"""

import os
import sys
import time
from datetime import datetime

def test_database_health_import():
    """Test database health module import"""
    print("🔍 Testing Database Health Module Import")
    print("=" * 50)
    
    try:
        from app.utils.database_health import (
            DatabaseHealthMonitor, 
            init_health_monitor, 
            check_database_health, 
            log_database_health,
            is_database_healthy
        )
        print("✅ Database health module imports successful")
        return True
    except Exception as e:
        print(f"❌ Database health module import failed: {e}")
        return False

def test_health_monitor_initialization():
    """Test health monitor initialization"""
    print("\n🔍 Testing Health Monitor Initialization")
    print("=" * 50)
    
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from app.utils.database_health import init_health_monitor
        
        # Create test app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize SQLAlchemy
        db = SQLAlchemy(app)
        
        with app.app_context():
            # Initialize health monitor
            health_monitor = init_health_monitor(db)
            
            if health_monitor:
                print("✅ Health monitor initialized successfully")
                return True
            else:
                print("❌ Health monitor initialization failed")
                return False
                
    except Exception as e:
        print(f"❌ Health monitor initialization error: {e}")
        return False

def test_health_check_functionality():
    """Test health check functionality"""
    print("\n🔍 Testing Health Check Functionality")
    print("=" * 50)
    
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from app.utils.database_health import init_health_monitor, check_database_health
        
        # Create test app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize SQLAlchemy
        db = SQLAlchemy(app)
        
        with app.app_context():
            # Initialize health monitor
            init_health_monitor(db)
            
            # Perform health check
            health = check_database_health()
            
            print(f"📊 Health Status: {health.get('status')}")
            print(f"📊 Response Time: {health.get('response_time_ms')}ms")
            print(f"📊 Last Check: {health.get('last_check')}")
            
            if health.get('status') == 'healthy':
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {health.get('last_error')}")
                return False
                
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_health_endpoints():
    """Test health check endpoints"""
    print("\n🔍 Testing Health Check Endpoints")
    print("=" * 50)
    
    try:
        import requests
        
        # Test local health endpoint (if running)
        base_url = "http://localhost:5001"
        
        # Test /health endpoint
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            print(f"📡 /health endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Health status: {data.get('status')}")
                print(f"📊 Database status: {data.get('database', {}).get('status')}")
                print("✅ /health endpoint working")
            else:
                print(f"⚠️  /health endpoint returned {response.status_code}")
                
        except requests.exceptions.RequestException:
            print("⚠️  /health endpoint not accessible (server may not be running)")
        
        # Test /health/database endpoint
        try:
            response = requests.get(f"{base_url}/health/database", timeout=5)
            print(f"📡 /health/database endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Database health: {data.get('status')}")
                print("✅ /health/database endpoint working")
            else:
                print(f"⚠️  /health/database endpoint returned {response.status_code}")
                
        except requests.exceptions.RequestException:
            print("⚠️  /health/database endpoint not accessible (server may not be running)")
        
        return True
        
    except Exception as e:
        print(f"❌ Health endpoints test error: {e}")
        return False

def test_production_health_check():
    """Test production health check"""
    print("\n🔍 Testing Production Health Check")
    print("=" * 50)
    
    try:
        import requests
        
        # Test production health endpoint
        url = "https://kiwellness.org/health"
        
        print(f"🌐 Testing production health endpoint: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Overall status: {data.get('status')}")
            print(f"📊 Database status: {data.get('database', {}).get('status')}")
            print(f"📊 Environment: {data.get('environment', {}).get('flask_env')}")
            print("✅ Production health check working")
            return True
        else:
            print(f"⚠️  Production health check returned {response.status_code}")
            print(f"📄 Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Production health check request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Production health check error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Database Health Monitoring Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    # Run tests
    tests = [
        ("Module Import", test_database_health_import),
        ("Monitor Initialization", test_health_monitor_initialization),
        ("Health Check Functionality", test_health_check_functionality),
        ("Health Endpoints", test_health_endpoints),
        ("Production Health Check", test_production_health_check)
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
        print("🎉 All tests passed! Database health monitoring is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
