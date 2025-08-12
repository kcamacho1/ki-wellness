#!/usr/bin/env python3
"""
Diagnostic script to test admin login issues in production.
This script will help identify why admin login is failing in production.
"""

import sys
import os
import requests
import json

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_admin_login_diagnostics():
    """Test admin login diagnostics for production"""
    
    # Get production URL from environment or use default
    production_url = os.getenv('PRODUCTION_URL', 'https://kiwellness.org')
    
    print("🔍 Admin Login Production Diagnostics")
    print("=" * 50)
    print(f"🌐 Testing against: {production_url}")
    
    # Test 1: Check if the application is accessible
    try:
        response = requests.get(f"{production_url}/", timeout=10)
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
        response = requests.get(f"{production_url}/login", timeout=10)
        if response.status_code == 200:
            print("✅ Login page is accessible")
            
            # Check if reCAPTCHA is present
            if 'g-recaptcha' in response.text:
                print("✅ reCAPTCHA is present on login page")
            else:
                print("⚠️  reCAPTCHA is NOT present on login page")
                
            # Check if Google reCAPTCHA script is loaded
            if 'google.com/recaptcha/api.js' in response.text:
                print("✅ Google reCAPTCHA script is loaded")
            else:
                print("⚠️  Google reCAPTCHA script is NOT loaded")
        else:
            print(f"❌ Login page returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access login page: {e}")
        return False
    
    # Test 3: Check reCAPTCHA configuration
    try:
        response = requests.get(f"{production_url}/api/recaptcha-status", timeout=10)
        if response.status_code == 200:
            recaptcha_data = response.json()
            print(f"✅ reCAPTCHA status API accessible")
            print(f"   - Enabled: {recaptcha_data.get('enabled', 'Unknown')}")
            print(f"   - Site key present: {recaptcha_data.get('site_key_present', 'Unknown')}")
            print(f"   - Secret key present: {recaptcha_data.get('secret_key_present', 'Unknown')}")
        else:
            print(f"⚠️  reCAPTCHA status API returned status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Cannot access reCAPTCHA status API: {e}")
    
    # Test 4: Test admin login with dummy credentials (should fail but show reCAPTCHA behavior)
    print("\n🧪 Testing admin login flow...")
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        # First, get the login page to establish session
        login_page = session.get(f"{production_url}/login", timeout=10)
        
        # Prepare login data (this will fail but show us the response)
        login_data = {
            'username': 'test_admin',
            'password': 'wrong_password',
            'g-recaptcha-response': 'dummy_response'
        }
        
        # Attempt login
        login_response = session.post(f"{production_url}/login", data=login_data, timeout=10)
        
        print(f"   - Login response status: {login_response.status_code}")
        
        # Check if we got redirected (success) or stayed on login page (failure)
        if login_response.status_code == 302:
            print("   - Login attempt resulted in redirect (possible success)")
            print(f"   - Redirect location: {login_response.headers.get('Location', 'Unknown')}")
        elif login_response.status_code == 200:
            print("   - Login attempt stayed on login page (expected failure)")
            
            # Check for error messages
            if 'Invalid username or password' in login_response.text:
                print("   - ✅ Correct error message displayed")
            elif 'Security verification failed' in login_response.text:
                print("   - ⚠️  reCAPTCHA verification failed (expected with dummy response)")
            elif 'Please complete the security verification' in login_response.text:
                print("   - ⚠️  reCAPTCHA response missing")
            else:
                print("   - ❓ Unexpected response content")
        else:
            print(f"   - ❌ Unexpected response status: {login_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   - ❌ Login test failed: {e}")
    
    print("\n📋 Production Admin Login Checklist:")
    print("1. ✅ Application accessible")
    print("2. ✅ Login page accessible")
    print("3. ⚠️  reCAPTCHA configuration needs verification")
    print("4. ⚠️  Admin credentials need verification")
    
    print("\n🔧 Common Production Issues:")
    print("- Missing RECAPTCHA_SITE_KEY environment variable")
    print("- Missing RECAPTCHA_SECRET_KEY environment variable")
    print("- Admin user not created in production database")
    print("- Wrong admin password in production")
    print("- Session configuration issues")
    print("- Database connection problems")
    
    print("\n🎯 Next Steps:")
    print("1. Verify environment variables are set correctly")
    print("2. Check if admin user exists in production database")
    print("3. Verify reCAPTCHA keys are valid")
    print("4. Test with valid admin credentials")
    print("5. Check production logs for specific error messages")
    
    return True

if __name__ == "__main__":
    success = test_admin_login_diagnostics()
    if success:
        print("\n🎉 Admin login diagnostics completed!")
    else:
        print("\n❌ Admin login diagnostics failed.")
        sys.exit(1)
