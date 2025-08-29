#!/usr/bin/env python3
"""
Quick script to check if a specific user exists in the database
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db, User
    
    def check_user(email):
        """Check if user exists with given email"""
        with app.app_context():
            try:
                user = User.query.filter_by(email=email).first()
                
                if user:
                    print(f"✅ User found!")
                    print(f"   ID: {user.id}")
                    print(f"   Username: {user.username}")
                    print(f"   Email: {user.email}")
                    print(f"   Name: {user.name}")
                    print(f"   Role: {user.role}")
                    print(f"   Email Verified: {user.email_verified}")
                    print(f"   Created At: {user.created_at}")
                    print(f"   Last Login: {getattr(user, 'last_login', 'N/A')}")
                    
                    # Check if user shows in normal query
                    all_users = User.query.all()
                    print(f"\n📊 Total users in database: {len(all_users)}")
                    
                    # Check pagination
                    paginated = User.query.order_by(User.created_at.desc()).paginate(
                        page=1, per_page=20, error_out=False
                    )
                    print(f"📄 Users on first page: {len(paginated.items)}")
                    print(f"📄 Total pages: {paginated.pages}")
                    
                    # Check if this user is in first page
                    user_emails_page1 = [u.email for u in paginated.items]
                    if email in user_emails_page1:
                        print(f"✅ User is on page 1")
                    else:
                        print(f"❌ User is NOT on page 1")
                        
                        # Find which page the user is on
                        for page_num in range(1, paginated.pages + 1):
                            page_users = User.query.order_by(User.created_at.desc()).paginate(
                                page=page_num, per_page=20, error_out=False
                            )
                            page_emails = [u.email for u in page_users.items]
                            if email in page_emails:
                                print(f"📍 User is on page {page_num}")
                                break
                else:
                    print(f"❌ User with email '{email}' not found")
                    
                    # Show recent users for comparison
                    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
                    print(f"\n🔍 Recent 5 users:")
                    for user in recent_users:
                        print(f"   - {user.email} (created: {user.created_at})")
                        
            except Exception as e:
                print(f"❌ Error checking user: {e}")
                return False
        
        return True

    if __name__ == '__main__':
        email = 'stephaniecamacho1@gmail.com'
        print(f"🔍 Checking for user: {email}")
        check_user(email)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the correct directory")
