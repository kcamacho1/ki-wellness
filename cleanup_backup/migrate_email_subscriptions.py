#!/usr/bin/env python3
"""
Email Subscriptions Migration Script
====================================

This script creates the email_subscriptions table for managing
waitlist subscriptions when account creation is closed.

Author: Ki Wellness Team
Version: 1.0
"""

import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, EmailSubscription

def migrate_email_subscriptions():
    """Create the email_subscriptions table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Creating email_subscriptions table...")
            
            # Create the table
            db.create_all()
            
            # Verify the table was created
            result = db.engine.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='email_subscriptions'
            """).fetchone()
            
            if result:
                print("✅ email_subscriptions table created successfully!")
                
                # Show table structure
                print("\n📋 Table structure:")
                columns = db.engine.execute("PRAGMA table_info(email_subscriptions)").fetchall()
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                    
            else:
                print("❌ Failed to create email_subscriptions table")
                return False
                
        except Exception as e:
            print(f"❌ Error creating email_subscriptions table: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Email Subscriptions Migration...")
    success = migrate_email_subscriptions()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\n📧 Email subscription system is now ready!")
        print("   - Users can subscribe to waitlist notifications")
        print("   - Unsubscribe links will be generated automatically")
        print("   - Database tracks subscription status and timestamps")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)
