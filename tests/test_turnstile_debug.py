#!/usr/bin/env python3
"""
Turnstile Debug Test Script
This script helps debug Cloudflare Turnstile verification issues
"""

import requests
import json
import os
from datetime import datetime

def test_turnstile_config():
    """Test Turnstile configuration and environment variables"""
    print("🔍 Testing Turnstile Configuration...")
    print("=" * 50)
    
    # Check environment variables
    env_vars = {
        'SITE_KEY': os.getenv('SITE_KEY'),
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'TURNSTILE_ENABLED': os.getenv('TURNSTILE_ENABLED'),
        'FLASK_ENV': os.getenv('FLASK_ENV'),
        'HOST': os.getenv('HOST'),
        'SERVER_NAME': os.getenv('SERVER_NAME')
    }
    
    for key, value in env_vars.items():
        if value:
            if 'SECRET' in key:
                print(f"✅ {key}: {'*' * min(len(value), 8)}... (length: {len(value)})")
            else:
                print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: Not set")
    
    print()

def test_turnstile_status_endpoint():
    """Test the Turnstile status endpoint"""
    print("🔍 Testing Turnstile Status Endpoint...")
    print("=" * 50)
    
    try:
        # Test local endpoint
        response = requests.get('http://localhost:5001/api/turnstile-status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working: {data}")
        else:
            print(f"❌ Status endpoint returned {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"❌ Error testing status endpoint: {e}")
    
    print()

def test_turnstile_verification():
    """Test Turnstile verification with a mock token"""
    print("🔍 Testing Turnstile Verification...")
    print("=" * 50)
    
    # Mock token for testing
    mock_token = "mock-turnstile-token-" + str(int(datetime.now().timestamp()))
    
    try:
        # Test the verification endpoint directly
        response = requests.post('http://localhost:5001/test-turnstile', 
                               data={'cf-turnstile-response': mock_token}, 
                               timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Test endpoint working: {response.text}")
        else:
            print(f"❌ Test endpoint returned {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"❌ Error testing verification: {e}")
    
    print()

def test_cloudflare_api():
    """Test direct Cloudflare API connection"""
    print("🔍 Testing Cloudflare API Connection...")
    print("=" * 50)
    
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        print("❌ No secret key available for testing")
        return
    
    # Test with a mock response
    mock_response = "mock-response-" + str(int(datetime.now().timestamp()))
    
    try:
        verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
        data = {
            'secret': secret_key,
            'response': mock_response
        }
        
        print(f"🔍 Testing with mock response: {mock_response[:20]}...")
        response = requests.post(verify_url, data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cloudflare API response: {result}")
            
            if result.get('success') == False:
                error_codes = result.get('error-codes', [])
                print(f"ℹ️  Expected failure with error codes: {error_codes}")
            else:
                print("⚠️  Unexpected success with mock token")
        else:
            print(f"❌ Cloudflare API returned {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing Cloudflare API: {e}")
    
    print()

def check_browser_console_logs():
    """Provide guidance for checking browser console logs"""
    print("🔍 Browser Console Debugging Guide...")
    print("=" * 50)
    
    print("To debug Turnstile issues in the browser:")
    print("1. Open Developer Tools (F12)")
    print("2. Go to Console tab")
    print("3. Look for Turnstile-related messages:")
    print("   - 'Turnstile: Initializing with site key: ...'")
    print("   - 'Turnstile: Widget rendered with ID: ...'")
    print("   - 'Turnstile: Challenge completed, token received: ...'")
    print("   - Any error messages")
    print("4. Check Network tab for API calls to:")
    print("   - /api/turnstile-status")
    print("   - challenges.cloudflare.com")
    print("5. Look for form submission errors")
    print()

def generate_debug_report():
    """Generate a comprehensive debug report"""
    print("📋 Generating Debug Report...")
    print("=" * 50)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'flask_env': os.getenv('FLASK_ENV', 'Not set'),
            'host': os.getenv('HOST', 'Not set'),
            'server_name': os.getenv('SERVER_NAME', 'Not set')
        },
        'turnstile_config': {
            'site_key_present': bool(os.getenv('SITE_KEY')),
            'secret_key_present': bool(os.getenv('SECRET_KEY')),
            'enabled': os.getenv('TURNSTILE_ENABLED', 'Not set')
        },
        'recommendations': []
    }
    
    # Generate recommendations based on findings
    if not os.getenv('SITE_KEY'):
        report['recommendations'].append("Set SITE_KEY environment variable")
    
    if not os.getenv('SECRET_KEY'):
        report['recommendations'].append("Set SECRET_KEY environment variable")
    
    if os.getenv('FLASK_ENV') == 'development':
        report['recommendations'].append("Check if running on localhost (should bypass Turnstile)")
    
    if not report['recommendations']:
        report['recommendations'].append("Configuration looks correct - check browser console for JavaScript errors")
    
    print("📊 Debug Report:")
    print(json.dumps(report, indent=2))
    print()

def main():
    """Main test function"""
    print("🚀 Turnstile Debug Test Suite")
    print("=" * 60)
    print()
    
    test_turnstile_config()
    test_turnstile_status_endpoint()
    test_turnstile_verification()
    test_cloudflare_api()
    check_browser_console_logs()
    generate_debug_report()
    
    print("✅ Debug tests completed!")
    print("\nNext steps:")
    print("1. Check the recommendations above")
    print("2. Review browser console logs")
    print("3. Verify environment variables are set correctly")
    print("4. Test with a real Turnstile token from the browser")

if __name__ == "__main__":
    main()
