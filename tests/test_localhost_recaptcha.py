#!/usr/bin/env python3
"""
Test Localhost reCAPTCHA Bypass
===============================

This test verifies that reCAPTCHA is properly bypassed on localhost
and doesn't cause the "unsupported domains" error.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

def test_localhost_recaptcha_bypass():
    """Test that reCAPTCHA is bypassed on localhost"""
    print("🧪 Testing Localhost reCAPTCHA Bypass...")
    
    with app.app_context():
        # Test the configuration
        from app.config import DevelopmentConfig
        
        config = DevelopmentConfig()
        print(f"✅ Development config loaded")
        print(f"🔧 reCAPTCHA enabled: {config.RECAPTCHA_ENABLED}")
        print(f"🔧 reCAPTCHA site key: {config.RECAPTCHA_SITE_KEY}")
        
        # Test that reCAPTCHA is disabled for localhost
        if not config.RECAPTCHA_ENABLED:
            print("✅ reCAPTCHA correctly disabled for development")
        else:
            print("⚠️  reCAPTCHA is enabled - this might cause issues on localhost")

def test_login_page_recaptcha():
    """Test that login page handles reCAPTCHA correctly"""
    print("\n🧪 Testing Login Page reCAPTCHA Handling...")
    
    with app.test_client() as client:
        # Test login page response
        response = client.get('/login')
        
        if response.status_code == 200:
            print("✅ Login page loads successfully")
            
            # Check if the page contains localhost detection
            content = response.get_data(as_text=True)
            
            if 'isLocalhost' in content:
                print("✅ Localhost detection JavaScript found")
            else:
                print("❌ Localhost detection JavaScript not found")
            
            if 'dev_bypass.js' in content:
                print("✅ Development bypass script referenced")
            else:
                print("❌ Development bypass script not found")
            
            if 'g-recaptcha' in content:
                print("⚠️  reCAPTCHA widget found - this might cause issues")
            else:
                print("✅ No reCAPTCHA widget found - bypass working")
                
        else:
            print(f"❌ Login page failed to load: {response.status_code}")

def test_recaptcha_configuration():
    """Test reCAPTCHA configuration"""
    print("\n🧪 Testing reCAPTCHA Configuration...")
    
    # Test environment detection
    import os
    
    # Simulate localhost environment
    os.environ['HOST'] = '127.0.0.1'
    
    from config import DevelopmentConfig
    config = DevelopmentConfig()
    
    print(f"🔧 Host: {os.environ.get('HOST', 'not set')}")
    print(f"🔧 reCAPTCHA enabled: {config.RECAPTCHA_ENABLED}")
    
    if not config.RECAPTCHA_ENABLED:
        print("✅ reCAPTCHA correctly disabled for localhost")
    else:
        print("❌ reCAPTCHA should be disabled for localhost")

def main():
    """Run all tests"""
    print("🚀 Testing Localhost reCAPTCHA Bypass")
    print("=" * 45)
    
    try:
        test_localhost_recaptcha_bypass()
        test_login_page_recaptcha()
        test_recaptcha_configuration()
        
        print("\n✅ All tests completed!")
        print("\n🎯 Summary:")
        print("  - reCAPTCHA should be disabled on localhost")
        print("  - Development bypass script should load")
        print("  - No 'unsupported domains' error should occur")
        print("  - Login page should work correctly on localhost")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
