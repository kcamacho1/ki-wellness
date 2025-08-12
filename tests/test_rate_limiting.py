#!/usr/bin/env python3
"""
Test script to verify rate limiting on food journal routes
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:5001"  # Change this to your server URL
TEST_USERNAME = "testuser"  # Change this to a test username
TEST_PASSWORD = "testpass123"  # Change this to a test password

def login():
    """Login and get session cookies"""
    login_data = {
        'username': TEST_USERNAME,
        'password': TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print("✅ Login successful")
        return response.cookies
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def test_search_rate_limit(cookies):
    """Test search rate limiting"""
    print("\n🔍 Testing search rate limiting...")
    
    search_data = {
        'food_name': 'apple',
        'serving_size': 100,
        'serving_unit': 'g'
    }
    
    # Make multiple rapid requests
    for i in range(35):  # Try to exceed the 30 per minute limit
        response = requests.post(
            f"{BASE_URL}/food-journal/search",
            json=search_data,
            cookies=cookies,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 429:  # Rate limit exceeded
            print(f"✅ Rate limit hit after {i+1} requests")
            print(f"Response: {response.text}")
            return True
        elif response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Search {i+1}: Success")
            else:
                print(f"⚠️ Search {i+1}: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Search {i+1}: HTTP {response.status_code}")
        
        time.sleep(0.1)  # Small delay between requests
    
    print("⚠️ Rate limit not hit - may need to adjust test")
    return False

def test_add_rate_limit(cookies):
    """Test add food rate limiting"""
    print("\n➕ Testing add food rate limiting...")
    
    add_data = {
        'food_name': 'Test Food',
        'serving_size': 100,
        'serving_unit': 'g',
        'time_of_day': 'breakfast',
        'water_amount': 0,
        'water_unit': 'ml',
        'mood': 'good',
        'notes': 'Test entry',
        'consumed_at': '2024-01-01T12:00:00',
        'browser_timezone': 'UTC'
    }
    
    # Make multiple rapid requests
    for i in range(25):  # Try to exceed the 20 per minute limit
        response = requests.post(
            f"{BASE_URL}/food-journal/add",
            json=add_data,
            cookies=cookies,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 429:  # Rate limit exceeded
            print(f"✅ Rate limit hit after {i+1} requests")
            print(f"Response: {response.text}")
            return True
        elif response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Add {i+1}: Success")
            else:
                print(f"⚠️ Add {i+1}: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Add {i+1}: HTTP {response.status_code}")
        
        time.sleep(0.1)  # Small delay between requests
    
    print("⚠️ Rate limit not hit - may need to adjust test")
    return False

def test_delete_rate_limit(cookies):
    """Test delete rate limiting"""
    print("\n🗑️ Testing delete rate limiting...")
    
    delete_data = {
        'entry_ids': [999]  # Non-existent entry ID
    }
    
    # Make multiple rapid requests
    for i in range(15):  # Try to exceed the 10 per minute limit
        response = requests.post(
            f"{BASE_URL}/food-journal/delete",
            json=delete_data,
            cookies=cookies,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 429:  # Rate limit exceeded
            print(f"✅ Rate limit hit after {i+1} requests")
            print(f"Response: {response.text}")
            return True
        elif response.status_code == 200:
            data = response.json()
            print(f"✅ Delete {i+1}: {data.get('message', 'Success')}")
        else:
            print(f"❌ Delete {i+1}: HTTP {response.status_code}")
        
        time.sleep(0.1)  # Small delay between requests
    
    print("⚠️ Rate limit not hit - may need to adjust test")
    return False

def main():
    """Run all rate limiting tests"""
    print("🚀 Starting rate limiting tests...")
    
    # Login first
    cookies = login()
    if not cookies:
        print("❌ Cannot proceed without login")
        return
    
    # Test each endpoint
    search_success = test_search_rate_limit(cookies)
    add_success = test_add_rate_limit(cookies)
    delete_success = test_delete_rate_limit(cookies)
    
    # Summary
    print("\n📊 Rate Limiting Test Results:")
    print(f"Search endpoint: {'✅ PASS' if search_success else '⚠️ MAYBE'}")
    print(f"Add endpoint: {'✅ PASS' if add_success else '⚠️ MAYBE'}")
    print(f"Delete endpoint: {'✅ PASS' if delete_success else '⚠️ MAYBE'}")
    
    if all([search_success, add_success, delete_success]):
        print("\n🎉 All rate limiting tests passed!")
    else:
        print("\n⚠️ Some tests may need adjustment or rate limits may be too high")

if __name__ == "__main__":
    main()
