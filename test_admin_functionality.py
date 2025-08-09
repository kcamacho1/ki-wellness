#!/usr/bin/env python3
"""
Test script to verify admin functionality
"""

import requests
import sys
import os

def test_admin_functionality():
    """Test admin functionality"""
    base_url = "http://localhost:5000"
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@kiwellness.org')
    
    print("Testing Admin Functionality...")
    print("=" * 50)
    
    # Test 1: Try to access admin dashboard without login
    print("\n1. Testing admin access without login...")
    try:
        response = requests.get(f"{base_url}/admin", allow_redirects=False)
        if response.status_code == 302:  # Redirect to login
            print("✓ Admin dashboard correctly redirects to login when not authenticated")
        else:
            print(f"✗ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Check if admin user exists
    print(f"\n2. Checking admin user in database...")
    try:
        from app.main import app, db, User
        with app.app_context():
            admin_user = User.query.filter(User.email.ilike(admin_email)).first()
            if admin_user:
                print(f"✓ Admin user found: {admin_user.username} ({admin_user.email})")
                print(f"  Admin status: {admin_user.is_admin}")
            else:
                print(f"✗ Admin user not found with email {admin_email}")
    except Exception as e:
        print(f"✗ Error checking admin user: {e}")
    
    # Test 3: Check regular users
    print("\n3. Checking regular users...")
    try:
        from app.main import app, db, User
        with app.app_context():
            regular_users = User.query.filter(User.is_admin == False).all()
            print(f"✓ Found {len(regular_users)} regular user(s):")
            for user in regular_users:
                print(f"  - {user.username} ({user.email}) - Admin: {user.is_admin}")
    except Exception as e:
        print(f"✗ Error checking regular users: {e}")
    
    # Test 4: Verify admin decorator function
    print("\n4. Testing admin decorator...")
    try:
        from app.main import is_admin_user, admin_required
        print("✓ Admin functions imported successfully")
        print(f"  is_admin_user function: {is_admin_user}")
        print(f"  admin_required decorator: {admin_required}")
    except Exception as e:
        print(f"✗ Error importing admin functions: {e}")
    
    print("\n" + "=" * 50)
    print("Admin functionality test completed!")
    print(f"\nTo test the full functionality:")
    print(f"1. Start the application: python run.py")
    print(f"2. Login with {admin_email}")
    print(f"3. Check if you see the 'Admin' link in navigation")
    print(f"4. Access the admin dashboard at /admin")

if __name__ == "__main__":
    test_admin_functionality()
