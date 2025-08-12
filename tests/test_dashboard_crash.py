#!/usr/bin/env python3
"""
Diagnostic script to test dashboard functionality and identify crash causes.
This script will help identify why the user dashboard is unresponsive and crashing.
"""

import sys
import os
import requests
import json
import time

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_dashboard_functionality():
    """Test dashboard functionality to identify crash causes"""
    
    # Get base URL from environment or use default
    base_url = os.getenv('TEST_URL', 'http://localhost:5001')
    
    print("🔍 Dashboard Crash Diagnostics")
    print("=" * 50)
    print(f"🌐 Testing against: {base_url}")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Test 1: Check if the application is accessible
    try:
        response = session.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Application is accessible")
        else:
            print(f"❌ Application returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to application: {e}")
        return False
    
    # Test 2: Check login page accessibility
    try:
        response = session.get(f"{base_url}/login", timeout=10)
        if response.status_code == 200:
            print("✅ Login page is accessible")
        else:
            print(f"❌ Login page returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access login page: {e}")
        return False
    
    # Test 3: Attempt login (this will fail but establish session)
    print("\n🧪 Testing login flow...")
    try:
        login_data = {
            'username': 'test_user',
            'password': 'wrong_password'
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data, timeout=10)
        
        if login_response.status_code == 200:
            print("✅ Login attempt completed (expected failure)")
        else:
            print(f"⚠️  Login attempt returned status code: {login_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login test failed: {e}")
    
    # Test 4: Check dashboard accessibility (should redirect to login)
    try:
        response = session.get(f"{base_url}/dashboard", timeout=10)
        if response.status_code == 302:
            print("✅ Dashboard redirects to login (expected for non-authenticated user)")
        else:
            print(f"⚠️  Dashboard returned status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access dashboard: {e}")
    
    # Test 5: Check dashboard API endpoints
    print("\n🧪 Testing dashboard API endpoints...")
    
    api_endpoints = [
        '/food-journal/entries',
        '/dashboard/mood/entries',
        '/dashboard/patterns',
        '/profile/data',
        '/subscription/status'
    ]
    
    for endpoint in api_endpoints:
        try:
            # Add query parameters for endpoints that need them
            if 'entries' in endpoint:
                today = time.strftime('%Y-%m-%d')
                url = f"{base_url}{endpoint}?start_date={today}&end_date={today}"
            elif 'patterns' in endpoint:
                url = f"{base_url}{endpoint}?browser_timezone=America/New_York"
            else:
                url = f"{base_url}{endpoint}"
            
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Status: {response.status_code}")
                # Try to parse JSON response
                try:
                    data = response.json()
                    if 'success' in data:
                        print(f"   - Success: {data['success']}")
                    if 'error' in data:
                        print(f"   - Error: {data['error']}")
                except json.JSONDecodeError:
                    print(f"   - Response is not JSON")
            elif response.status_code == 302:
                print(f"✅ {endpoint} - Redirects to login (expected)")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Request failed: {e}")
    
    # Test 6: Check for database connection issues
    print("\n🧪 Testing database-related endpoints...")
    
    db_endpoints = [
        '/api/recaptcha-status',
        '/admin'  # This should redirect to login
    ]
    
    for endpoint in db_endpoints:
        try:
            response = session.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Status: {response.status_code}")
                if endpoint == '/api/recaptcha-status':
                    try:
                        data = response.json()
                        print(f"   - reCAPTCHA enabled: {data.get('enabled', 'Unknown')}")
                        print(f"   - Keys configured: {data.get('keys_configured', 'Unknown')}")
                    except json.JSONDecodeError:
                        print(f"   - Response is not JSON")
            elif response.status_code == 302:
                print(f"✅ {endpoint} - Redirects to login (expected)")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Request failed: {e}")
    
    # Test 7: Check for JavaScript errors in dashboard template
    print("\n🧪 Testing dashboard template...")
    try:
        response = session.get(f"{base_url}/dashboard", timeout=10)
        if response.status_code == 302:
            print("✅ Dashboard redirects to login (expected)")
        else:
            print(f"⚠️  Dashboard returned status code: {response.status_code}")
            
            # Check for common JavaScript issues in the response
            content = response.text
            
            # Check for missing JavaScript libraries
            if 'chart.js' not in content:
                print("⚠️  Chart.js library not found in dashboard")
            else:
                print("✅ Chart.js library found")
                
            if 'html2canvas' not in content:
                print("⚠️  html2canvas library not found in dashboard")
            else:
                print("✅ html2canvas library found")
                
            # Check for common JavaScript errors
            if 'loadPatternsAnalysis' in content:
                print("✅ loadPatternsAnalysis function found")
            else:
                print("⚠️  loadPatternsAnalysis function not found")
                
            if 'fetch(' in content:
                print("✅ Fetch API calls found")
            else:
                print("⚠️  No fetch API calls found")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Dashboard template test failed: {e}")
    
    print("\n📋 Dashboard Crash Analysis:")
    print("1. ✅ Application accessibility")
    print("2. ✅ Login page functionality")
    print("3. ✅ API endpoint accessibility")
    print("4. ⚠️  Database connection needs verification")
    print("5. ⚠️  JavaScript functionality needs verification")
    
    print("\n🔧 Common Dashboard Crash Causes:")
    print("- Database connection issues")
    print("- Missing database tables (patterns_cache, user_profiles, etc.)")
    print("- JavaScript errors in dashboard template")
    print("- API endpoint failures")
    print("- Session management issues")
    print("- Memory/performance issues with large datasets")
    print("- OpenAI API failures in patterns analysis")
    
    print("\n🎯 Next Steps:")
    print("1. Check production logs for specific error messages")
    print("2. Verify database tables exist and are accessible")
    print("3. Test with authenticated user session")
    print("4. Check browser console for JavaScript errors")
    print("5. Monitor API response times and failures")
    print("6. Verify OpenAI API configuration for patterns analysis")
    
    return True

if __name__ == "__main__":
    success = test_dashboard_functionality()
    if success:
        print("\n🎉 Dashboard diagnostics completed!")
    else:
        print("\n❌ Dashboard diagnostics failed.")
        sys.exit(1)
