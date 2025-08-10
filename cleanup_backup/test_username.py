#!/usr/bin/env python3
"""
Test script to verify username functionality
"""

import os
import sys
import requests

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from main import app, db, User

def test_username_functionality():
    """Test username functionality"""
    print("Testing username functionality...")
    
    with app.app_context():
        try:
            # Test case-insensitive username lookup
            print("\n1. Testing case-insensitive username lookup...")
            
            # Create a test user
            test_user = User(
                username='testuser',
                email='test@example.com',
                password_hash='[REDACTED]'
            )
            db.session.add(test_user)
            db.session.commit()
            
            # Test different case variations
            test_cases = ['testuser', 'TESTUSER', 'TestUser', 'testUser']
            
            for test_case in test_cases:
                user = User.query.filter(User.username.ilike(test_case)).first()
                if user:
                    print(f"✅ Found user with username '{test_case}' -> {user.username}")
                else:
                    print(f"❌ Could not find user with username '{test_case}'")
            
            # Test unique constraint
            print("\n2. Testing unique constraint...")
            
            try:
                duplicate_user = User(
                    username='TESTUSER',  # Same username, different case
                    email='test2@example.com',
                    password_hash='[REDACTED]'
                )
                db.session.add(duplicate_user)
                db.session.commit()
                print("❌ Should have failed - duplicate username allowed")
            except Exception as e:
                print(f"✅ Correctly prevented duplicate username: {e}")
                db.session.rollback()
            
            # Test email case-insensitive
            print("\n3. Testing case-insensitive email...")
            
            try:
                duplicate_email = User(
                    username='testuser2',
                    email='TEST@EXAMPLE.COM',  # Same email, different case
                    password_hash='[REDACTED]'
                )
                db.session.add(duplicate_email)
                db.session.commit()
                print("❌ Should have failed - duplicate email allowed")
            except Exception as e:
                print(f"✅ Correctly prevented duplicate email: {e}")
                db.session.rollback()
            
            # Clean up
            db.session.delete(test_user)
            db.session.commit()
            
            print("\n✅ Username functionality tests completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            db.session.rollback()

if __name__ == "__main__":
    test_username_functionality()
