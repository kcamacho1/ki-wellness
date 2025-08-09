#!/usr/bin/env python3
"""
reCAPTCHA Setup Script
Helps users configure reCAPTCHA keys for the KI Wellness application
"""

import os
import sys

def print_banner():
    print("🔒 reCAPTCHA Setup for KI Wellness")
    print("=" * 50)

def print_instructions():
    print("\n📋 Instructions to get reCAPTCHA keys:")
    print("1. Visit: https://www.google.com/recaptcha/admin")
    print("2. Click 'Create' to register a new site")
    print("3. Choose 'reCAPTCHA v2' > 'I'm not a robot' Checkbox")
    print("4. Add your domains:")
    print("   - For development: localhost, 127.0.0.1")
    print("   - For production: your actual domain (e.g., example.com)")
    print("5. Accept the terms and click 'Submit'")
    print("6. Copy the 'Site Key' and 'Secret Key'")
    print("\n")

def get_user_input():
    print("🔑 Enter your reCAPTCHA keys:")
    public_key = input("Site Key (Public Key): ").strip()
    private_key = input("Secret Key (Private Key): ").strip()
    
    if not public_key or not private_key:
        print("❌ Both keys are required!")
        return None, None
    
    return public_key, private_key

def create_env_file(public_key, private_key):
    env_content = f"""# reCAPTCHA Configuration
# Replace these with your actual reCAPTCHA keys from Google
RECAPTCHA_PUBLIC_KEY={public_key}
RECAPTCHA_PRIVATE_KEY={private_key}
RECAPTCHA_ENABLED=true

# Other environment variables can be added here
# FLASK_ENV=development
# FLASK_DEBUG=true
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with your reCAPTCHA keys")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def update_main_py():
    print("\n🔧 Updating app/main.py to use environment variables...")
    print("Note: You'll need to restart your Flask application after making these changes.")
    
    # Read the current main.py file
    try:
        with open('app/main.py', 'r') as f:
            content = f.read()
        
        # Check if it's already using environment variables
        if 'os.environ.get' in content:
            print("✅ app/main.py is already configured to use environment variables")
            return True
        else:
            print("⚠️  You may need to manually update app/main.py to use environment variables")
            print("   Look for the reCAPTCHA configuration section and update it to use:")
            print("   os.environ.get('RECAPTCHA_PUBLIC_KEY', 'default_key')")
            return False
    except Exception as e:
        print(f"❌ Error reading app/main.py: {e}")
        return False

def print_next_steps():
    print("\n🎯 Next Steps:")
    print("1. Restart your Flask application")
    print("2. Test the reCAPTCHA functionality on /login and /register pages")
    print("3. Verify that the reCAPTCHA widget appears and works correctly")
    print("4. For production, make sure to:")
    print("   - Use HTTPS (reCAPTCHA requires it)")
    print("   - Add your production domain to the reCAPTCHA settings")
    print("   - Set RECAPTCHA_ENABLED=true in production")
    print("\n🔗 Useful Links:")
    print("- reCAPTCHA Admin Console: https://www.google.com/recaptcha/admin")
    print("- reCAPTCHA Documentation: https://developers.google.com/recaptcha")
    print("- Test Keys: https://developers.google.com/recaptcha/docs/faq#id-like-to-run-automated-tests-with-recaptcha-v2-what-should-i-do")

def main():
    print_banner()
    print_instructions()
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists. Do you want to overwrite it? (y/n): ", end='')
        response = input().strip().lower()
        if response != 'y':
            print("❌ Setup cancelled.")
            return
    
    public_key, private_key = get_user_input()
    if not public_key or not private_key:
        return
    
    if create_env_file(public_key, private_key):
        update_main_py()
        print_next_steps()
    else:
        print("❌ Setup failed. Please try again.")

if __name__ == "__main__":
    main()
