#!/usr/bin/env python3
"""
Simple test script for KI Wellness Profile System
"""

import requests
import json
import sys
import time

def test_app():
    """Test the Flask application"""
    base_url = "http://localhost:5000"
    
    print("Testing KI Wellness Profile System...")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/profile", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the Flask app is running.")
        print("Run: python app/main.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False
    
    # Test 2: Get profile data
    try:
        response = requests.get(f"{base_url}/profile/data", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Profile data endpoint working")
            print(f"   Current profile fields: {len(data)} fields")
        else:
            print(f"❌ Profile data endpoint returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting profile data: {e}")
    
    # Test 3: Save profile data
    test_data = {
        "name": "Test User",
        "date_of_birth": "1990-01-01",
        "age": "30",
        "weight": "70.5",
        "height": "170.0",
        "goals": "Stay healthy and fit",
        "ailments": "None",
        "daily_activities": "Office work",
        "day_notes": "Focus on wellness",
        "sleep_schedule": "10:00 PM - 6:00 AM",
        "night_notes": "Get good sleep",
        "dietary_preferences": "Balanced diet"
    }
    
    try:
        response = requests.post(
            f"{base_url}/profile/save",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Profile save endpoint working")
            else:
                print(f"❌ Profile save failed: {result.get('message')}")
        else:
            print(f"❌ Profile save endpoint returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error saving profile: {e}")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\nTo access the application:")
    print(f"🌐 Open your browser and go to: {base_url}")
    print("\nTo stop the server:")
    print("Press Ctrl+C in the terminal where the Flask app is running")
    
    return True

if __name__ == "__main__":
    success = test_app()
    sys.exit(0 if success else 1)
