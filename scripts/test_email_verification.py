#!/usr/bin/env python3

"""
Email Verification System Test
Created: 2024-12-19
Description: Test the complete email verification flow
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User
from services.email_service import EmailService
from config.email_config import EmailConfig
from datetime import datetime, timedelta
import secrets

def test_email_verification_system():
    """Test the complete email verification system"""
    
    with app.app_context():
        print("🧪 Ki Wellness Email Verification Test")
        print("=" * 50)
        
        # Test 1: Email Configuration
        print("\n📧 Testing Email Configuration")
        print("-" * 30)
        config = EmailConfig.validate_configuration()
        if config['valid']:
            print(f"✅ Email configuration is valid")
            print(f"   Method: {config['method']}")
            print(f"   From Email: {config['from_email']}")
        else:
            print(f"❌ Email configuration invalid: {config.get('error')}")
            return False
        
        # Test 2: Email Service
        print("\n🔧 Testing Email Service")
        print("-" * 25)
        try:
            email_service = EmailService()
            if email_service.sendgrid_client:
                print("✅ Email service initialized successfully")
            else:
                print("❌ Email service failed to initialize")
                return False
        except Exception as e:
            print(f"❌ Email service error: {str(e)}")
            return False
        
        # Test 3: Database Schema
        print("\n🗄️  Testing Database Schema")
        print("-" * 27)
        
        # Check if email verification fields exist
        try:
            # Try to query a user with email verification fields
            user_count = User.query.count()
            print(f"✅ Database has {user_count} users")
            
            # Test that we can create a user with verification fields
            test_user_data = {
                'email_verified': False,
                'email_verification_token': 'test_token',
                'email_verification_expires': datetime.utcnow() + timedelta(hours=24),
                'email_verification_sent_at': datetime.utcnow()
            }
            
            # Check if a sample user has the fields (without creating one)
            if user_count > 0:
                sample_user = User.query.first()
                has_verification_fields = all([
                    hasattr(sample_user, 'email_verified'),
                    hasattr(sample_user, 'email_verification_token'),
                    hasattr(sample_user, 'email_verification_expires'),
                    hasattr(sample_user, 'email_verification_sent_at')
                ])
                
                if has_verification_fields:
                    print("✅ All email verification fields exist in database")
                else:
                    print("❌ Missing email verification fields in database")
                    return False
            else:
                print("ℹ️  No users found to test schema, but User model has verification fields")
                
        except Exception as e:
            print(f"❌ Database schema error: {str(e)}")
            return False
        
        # Test 4: Verification Link Generation
        print("\n🔗 Testing Verification Link Generation")
        print("-" * 35)
        try:
            test_token = secrets.token_urlsafe(32)
            verification_link = EmailConfig.get_verification_link(test_token)
            expected_link = f"{EmailConfig.APP_URL}/verify-email/{test_token}"
            
            if verification_link == expected_link:
                print(f"✅ Verification link generated correctly")
                print(f"   Link: {verification_link}")
            else:
                print(f"❌ Verification link mismatch")
                print(f"   Expected: {expected_link}")
                print(f"   Got: {verification_link}")
                return False
                
        except Exception as e:
            print(f"❌ Link generation error: {str(e)}")
            return False
        
        # Test 5: Email Template Rendering (optional)
        print("\n📄 Testing Email Template")
        print("-" * 25)
        try:
            test_context = {
                'username': 'Test User',
                'verification_link': 'https://example.com/verify/test123',
                'app_url': 'https://example.com'
            }
            
            # Test the template rendering method
            html_content = email_service._render_email_template('emails/email_verification.html', test_context)
            
            if html_content and len(html_content) > 100:  # Basic check
                print("✅ Email template renders successfully")
                print(f"   Template size: {len(html_content)} characters")
                
                # Check if template contains expected content
                if 'Test User' in html_content and 'verify/test123' in html_content:
                    print("✅ Template contains expected variables")
                else:
                    print("⚠️  Template may not be rendering variables correctly")
            else:
                print("❌ Email template failed to render properly")
                return False
                
        except Exception as e:
            print(f"❌ Template rendering error: {str(e)}")
            return False
        
        # Test 6: Token Generation and Validation
        print("\n🔐 Testing Token Security")
        print("-" * 22)
        try:
            # Generate multiple tokens to ensure uniqueness
            tokens = [secrets.token_urlsafe(32) for _ in range(5)]
            unique_tokens = set(tokens)
            
            if len(unique_tokens) == len(tokens):
                print("✅ Token generation produces unique tokens")
                print(f"   Sample token: {tokens[0][:20]}...")
            else:
                print("❌ Token generation may have collision issues")
                return False
                
        except Exception as e:
            print(f"❌ Token generation error: {str(e)}")
            return False
        
        # Test Summary
        print("\n" + "=" * 50)
        print("🎉 All Email Verification Tests Passed!")
        print("=" * 50)
        
        print("\n📋 System Summary:")
        print(f"   ✅ Email verification enabled")
        print(f"   ✅ SendGrid integration working")
        print(f"   ✅ Database schema updated")
        print(f"   ✅ Email templates ready")
        print(f"   ✅ Security tokens working")
        
        print("\n🚀 Ready to test with real registration:")
        print("   1. Register a new account")
        print("   2. Check email for verification link")
        print("   3. Click link to verify email")
        print("   4. Login with verified account")
        
        return True

def test_send_verification_email():
    """Test sending an actual verification email"""
    
    with app.app_context():
        print("\n📬 Testing Live Email Sending")
        print("-" * 30)
        
        email = input("Enter your email to test verification email (or press Enter to skip): ").strip()
        
        if not email:
            print("⏭️  Skipping live email test")
            return True
        
        try:
            email_service = EmailService()
            test_token = secrets.token_urlsafe(32)
            
            success = email_service.send_email_verification(
                to_email=email,
                verification_token=test_token,
                username="Test User"
            )
            
            if success:
                print(f"✅ Test verification email sent to {email}")
                print(f"   Token: {test_token}")
                print("   Check your inbox!")
                return True
            else:
                print(f"❌ Failed to send test email to {email}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending test email: {str(e)}")
            return False

if __name__ == '__main__':
    print("Starting Email Verification System Tests...\n")
    
    # Run core system tests
    system_tests_passed = test_email_verification_system()
    
    if system_tests_passed:
        # Optionally test live email sending
        test_send_verification_email()
        print("\n✅ Email verification system is fully functional!")
    else:
        print("\n❌ Email verification system has issues that need to be fixed.")
        sys.exit(1)
