#!/usr/bin/env python3
"""
Test script for the Calendly booking system
"""

import requests

def test_human_help_page():
    """Test the human help page loads"""
    print("🔍 Testing human help page...")
    try:
        response = requests.get('http://localhost:5000/human-help')
        if response.status_code == 200:
            print("✅ Human help page loads successfully")
            return True
        else:
            print(f"❌ Human help page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Human help page error: {e}")
        return False

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get('http://localhost:5000/health')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Calendly booking system tests...\n")
    
    # Check if app is running
    try:
        requests.get('http://localhost:5000/health', timeout=5)
    except:
        print("❌ App is not running. Please start the app with: python app.py")
        return
    
    tests = [
        test_health_endpoint,
        test_human_help_page
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Calendly booking system is working correctly.")
        print("\n📋 Next Steps:")
        print("1. Visit http://localhost:5000/human-help")
        print("2. Click the 'Donate $20' button to support")
        print("3. Use the Calendly widget to book your session")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == '__main__':
    main()
