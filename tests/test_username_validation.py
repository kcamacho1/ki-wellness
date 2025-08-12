#!/usr/bin/env python3
"""
Test script for username validation - checks if usernames containing 'kiwellness' are properly rejected
"""

import sys
import os
# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import is_kiwellness_username

def test_username_validation():
    """Test the username validation function"""
    
    # Test cases that should be rejected (contain 'kiwellness' in some form)
    rejected_usernames = [
        'kiwellness',
        'ki_wellness',
        'ki-wellness', 
        'ki wellness',
        'kiwellness123',
        'ki_wellness_123',
        'ki-wellness-123',
        'ki wellness 123',
        'kiwellness2024',
        'ki_wellness_2024',
        'ki-wellness-2024',
        'ki wellness 2024',
        'kiwellness2023',
        'ki_wellness_2023',
        'ki-wellness-2023',
        'ki wellness 2023',
        'kiwellness2025',
        'ki_wellness_2025',
        'ki-wellness-2025',
        'ki wellness 2025',
        'my_kiwellness_user',
        'user_kiwellness',
        'kiwellness_test',
        'test_kiwellness',
        'KIWELLNESS',
        'KiWellness',
        'KI_WELLNESS',
        'Ki_Wellness',
        'ki wellness user',
        'user ki wellness',
        'kiwellness_user_123',
        '123_kiwellness_456',
        'kiwellness_2024_user',
        'user_kiwellness_2024'
    ]
    
    # Test cases that should be allowed (don't contain 'kiwellness')
    allowed_usernames = [
        'myusername',
        'user123',
        'test_user',
        'admin',
        'john.doe',
        'jane-smith',
        'user_2024',
        'testuser123',
        'my_user_name',
        'user-name',
        'username123',
        'test.user',
        'user_test',
        'myuser',
        'user2024',
        'test123',
        'admin_user',
        'john_doe_123',
        'jane_smith_2024',
        'user.name',
        'test-user',
        'my_username',
        'user_name_123',
        'test.user.2024',
        'user-test-123'
    ]
    
    print("🧪 Testing Username Validation")
    print("=" * 50)
    
    # Test rejected usernames
    print("\n❌ Testing usernames that should be REJECTED:")
    print("-" * 40)
    rejected_count = 0
    for username in rejected_usernames:
        result = is_kiwellness_username(username)
        status = "✅ REJECTED" if result else "❌ ALLOWED (SHOULD BE REJECTED)"
        print(f"{username:<25} -> {status}")
        if result:
            rejected_count += 1
        else:
            print(f"  ⚠️  WARNING: '{username}' was allowed but should be rejected!")
    
    # Test allowed usernames
    print("\n✅ Testing usernames that should be ALLOWED:")
    print("-" * 40)
    allowed_count = 0
    for username in allowed_usernames:
        result = is_kiwellness_username(username)
        status = "❌ REJECTED (SHOULD BE ALLOWED)" if result else "✅ ALLOWED"
        print(f"{username:<25} -> {status}")
        if not result:
            allowed_count += 1
        else:
            print(f"  ⚠️  WARNING: '{username}' was rejected but should be allowed!")
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 50)
    print(f"Rejected usernames: {rejected_count}/{len(rejected_usernames)} correctly rejected")
    print(f"Allowed usernames: {allowed_count}/{len(allowed_usernames)} correctly allowed")
    
    total_tests = len(rejected_usernames) + len(allowed_usernames)
    passed_tests = rejected_count + allowed_count
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! ({passed_tests}/{total_tests})")
        return True
    else:
        print(f"\n❌ SOME TESTS FAILED! ({passed_tests}/{total_tests})")
        return False

if __name__ == "__main__":
    success = test_username_validation()
    sys.exit(0 if success else 1)
