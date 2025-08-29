#!/usr/bin/env python3
"""
Test script for email configuration
Run this to verify your Outlook email setup is working
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_email_configuration():
    """Test email configuration and service"""
    print("🧪 Testing Email Configuration")
    print("=" * 50)
    
    try:
        from config.email_config import EmailConfig
        
        # Test configuration validation
        config_status = EmailConfig.validate_configuration()
        print(f"📧 Email Configuration Status:")
        print(f"   Valid: {config_status['valid']}")
        print(f"   Method: {config_status['method']}")
        
        if config_status['valid']:
            print(f"   From Email: {config_status['from_email']}")
            if 'server' in config_status:
                print(f"   Server: {config_status['server']}:{config_status['port']}")
        else:
            print(f"   Error: {config_status.get('error', 'Unknown error')}")
            return False
        
        print(f"✅ Email configuration is valid!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_email_service():
    """Test email service initialization"""
    print(f"\n🔧 Testing Email Service")
    print("=" * 50)
    
    try:
        from services.email_service import EmailService
        
        email_service = EmailService()
        
        if email_service.sendgrid_client:
            print(f"✅ Email service initialized successfully")
            print(f"   Method: SendGrid")
            print(f"   From: {email_service.from_name} <{email_service.from_email}>")
            return True
        else:
            print(f"❌ Email service not configured properly")
            return False
            
    except Exception as e:
        print(f"❌ Email service error: {e}")
        return False

def test_send_email():
    """Test sending an actual email (optional)"""
    print(f"\n📬 Test Email Sending (Optional)")
    print("=" * 50)
    
    test_email = input("Enter your email to test sending (or press Enter to skip): ").strip()
    
    if not test_email:
        print("⏭️  Skipping email send test")
        return True
    
    try:
        from services.email_service import EmailService
        
        email_service = EmailService()
        
        print(f"📤 Sending test email to {test_email}...")
        
        success = email_service.send_password_reset_email(
            test_email, 
            "test-token-12345", 
            "Test User"
        )
        
        if success:
            print(f"✅ Test email sent successfully!")
            print(f"   Check {test_email} for the password reset email")
            print(f"   Note: This is a test - the reset link won't work")
        else:
            print(f"❌ Failed to send test email")
            print(f"   Check your email configuration and credentials")
        
        return success
        
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 Ki Wellness Email Configuration Test")
    print("=" * 60)
    
    # Check environment
    if not os.getenv('SENDGRID_API_KEY'):
        print("❌ SendGrid not configured")
        print("   Add SENDGRID_API_KEY to your .env file")
        print("   Get your API key from https://app.sendgrid.com/settings/api_keys")
        print("   See env_template for required variables")
        return
    
    # Run tests
    tests = [
        ("Configuration", test_email_configuration),
        ("Email Service", test_email_service),
        ("Send Email", test_send_email)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print(f"\n⏹️  Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n🎉 All tests passed! Your email configuration is ready.")
        print(f"   You can now use the password reset functionality.")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")
        print(f"   Review the EMAIL_SETUP_GUIDE.md for help.")

if __name__ == "__main__":
    main()
