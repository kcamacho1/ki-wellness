#!/usr/bin/env python3
"""
Test script for the payment system
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

def test_payment_intent_creation():
    """Test payment intent creation"""
    print("\n🔍 Testing payment intent creation...")
    try:
        response = requests.post(
            'http://localhost:5000/create-payment-intent',
            headers={'Content-Type': 'application/json'},
            json={
                'payment_type': '30min_session',
                'amount': 2000,
                'email': 'test@example.com',
                'name': 'Test User'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'clientSecret' in data:
                print(f"✅ Payment intent created successfully")
                print(f"   Session ID: {data.get('session_id', 'N/A')}")
                print(f"   Client Secret: {data['clientSecret'][:20]}...")
                return True
            else:
                print(f"❌ No client secret in response: {data}")
                return False
        else:
            print(f"❌ Payment intent creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Payment intent creation error: {e}")
        return False

def test_human_help_page():
    """Test the human help page loads"""
    print("\n🔍 Testing human help page...")
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

def main():
    """Run all tests"""
    print("🚀 Starting payment system tests...\n")
    
    # Check if app is running
    try:
        requests.get('http://localhost:5000/health', timeout=5)
    except:
        print("❌ App is not running. Please start the app with: python app.py")
        return
    
    tests = [
        test_health_endpoint,
        test_payment_intent_creation,
        test_human_help_page
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Payment system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == '__main__':
    main()
