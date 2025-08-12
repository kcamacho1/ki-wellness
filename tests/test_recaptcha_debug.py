#!/usr/bin/env python3
"""
Quick reCAPTCHA Debug Test
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 reCAPTCHA Configuration Debug")
print("=" * 40)

# Check environment variables
recaptcha_site_key = os.getenv('RECAPTCHA_SITE_KEY')
recaptcha_secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
recaptcha_enabled = os.getenv('RECAPTCHA_ENABLED', 'true').lower() == 'true'

print(f"RECAPTCHA_SITE_KEY: {recaptcha_site_key}")
print(f"RECAPTCHA_SECRET_KEY: {'*' * 8 if recaptcha_secret_key else 'NOT SET'}")
print(f"RECAPTCHA_ENABLED: {recaptcha_enabled}")

# Check if keys are properly configured
keys_configured = bool(recaptcha_site_key and recaptcha_secret_key and 
                       recaptcha_site_key != 'None' and recaptcha_secret_key != 'None')

print(f"\nKeys Configured: {keys_configured}")

if not keys_configured:
    print("\n❌ reCAPTCHA keys are not properly configured!")
    print("\nTo fix this:")
    print("1. Get reCAPTCHA keys from: https://www.google.com/recaptcha/admin")
    print("2. Add to your .env file:")
    print("   RECAPTCHA_SITE_KEY=your_site_key_here")
    print("   RECAPTCHA_SECRET_KEY=your_secret_key_here")
    print("3. Restart your Flask application")
else:
    print("\n✅ reCAPTCHA keys are configured!")
    print("If you're still having issues, check:")
    print("1. Flask app is restarted after setting environment variables")
    print("2. Browser console for JavaScript errors")
    print("3. Backend logs for verification errors")

print("\n🔧 For development testing:")
print("- The app should work on localhost without reCAPTCHA keys")
print("- Check browser console for 'Development mode' messages")
print("- Forms should submit normally in development mode")
