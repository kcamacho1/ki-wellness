#!/usr/bin/env python3
"""
Test script to verify username validation with periods and dashes
"""

import os
import sys
import re

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from main import app, db, User

def test_username_validation():
    """Test username validation with various characters"""
    print("Testing username validation with periods and dashes...")
    
    # Test cases
    test_cases = [
        # Valid usernames
        ("john.doe", True, "Period in middle"),
        ("john-doe", True, "Dash in middle"),
        ("john_doe", True, "Underscore in middle"),
        ("john.doe-123", True, "Multiple special characters"),
        ("j.doe", True, "Single letter with period"),
        ("j-doe", True, "Single letter with dash"),
        ("john123", True, "Letters and numbers"),
        ("123john", True, "Numbers and letters"),
        ("john", True, "Simple letters"),
        ("joh", True, "Minimum length"),
        ("a" * 30, True, "Maximum length"),
        
        # Invalid usernames
        ("jo", False, "Too short"),
        ("a" * 31, False, "Too long"),
        ("john@doe", False, "Invalid character @"),
        ("john#doe", False, "Invalid character #"),
        ("john$doe", False, "Invalid character $"),
        ("john doe", False, "Space not allowed"),
        ("john/doe", False, "Invalid character /"),
        ("john\\doe", False, "Invalid character \\"),
        ("", False, "Empty string"),
        ("john.doe.", False, "Ends with period"),
        ("john.doe-", False, "Ends with dash"),
        ("john.doe_", False, "Ends with underscore"),
        (".john", False, "Starts with period"),
        ("-john", False, "Starts with dash"),
        ("_john", False, "Starts with underscore"),
        ("j.d", True, "Valid 3-character username"),
        ("j", False, "Too short"),
        ("a", False, "Too short"),
    ]
    
    # Username pattern from the application
    username_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$')
    
    print("\nTesting username validation patterns:")
    print("=" * 50)
    
    for username, should_be_valid, description in test_cases:
        # Check pattern match
        pattern_match = bool(username_pattern.match(username))
        
        # Check length
        length_valid = 3 <= len(username) <= 30 if username else False
        
        # Overall validation
        is_valid = pattern_match and length_valid
        
        status = "✅ PASS" if is_valid == should_be_valid else "❌ FAIL"
        result = "VALID" if is_valid else "INVALID"
        expected = "VALID" if should_be_valid else "INVALID"
        
        print(f"{status} {username:20} -> {result:8} (expected: {expected:8}) - {description}")
        
        if is_valid != should_be_valid:
            print(f"    Pattern match: {pattern_match}, Length valid: {length_valid}")
    
    print("\n" + "=" * 50)
    print("Username validation test completed!")
    
    # Test with actual database operations
    print("\nTesting database operations with valid usernames...")
    
    with app.app_context():
        try:
            # Test valid usernames
            valid_usernames = ["john.doe", "john-doe", "john_doe", "john.doe-123"]
            
            for username in valid_usernames:
                try:
                    # Check if username already exists
                    existing_user = User.query.filter(User.username.ilike(username)).first()
                    if existing_user:
                        print(f"⚠️  Username '{username}' already exists in database")
                        continue
                    
                    # Try to create user with this username
                    test_user = User(
                        username=username,
                        email=f"{username}@test.com",
                        password_hash="[REDACTED]"
                    )
                    db.session.add(test_user)
                    db.session.commit()
                    print(f"✅ Successfully created user with username: '{username}'")
                    
                    # Clean up
                    db.session.delete(test_user)
                    db.session.commit()
                    
                except Exception as e:
                    print(f"❌ Failed to create user with username '{username}': {e}")
                    db.session.rollback()
            
            print("\n✅ Database username validation tests completed!")
            
        except Exception as e:
            print(f"❌ Error during database testing: {e}")
            db.session.rollback()

if __name__ == "__main__":
    test_username_validation()
