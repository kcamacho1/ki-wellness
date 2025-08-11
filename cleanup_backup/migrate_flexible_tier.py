#!/usr/bin/env python3
"""
Migration script to add flexible service tier settings to existing databases.
This script adds the new system settings for OpenAI API optimization.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

def migrate_flexible_tier():
    """Add flexible service tier settings to the database"""
    try:
        print("🔄 Starting flexible service tier migration...")
        
        # Get the database path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'ki_wellness.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            return False
        
        print(f"📁 Database found at: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if system_settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_settings'")
        if not cursor.fetchone():
            print("❌ system_settings table not found. Please run the enhanced admin migration first.")
            return False
        
        # Check if the new settings already exist
        cursor.execute("SELECT COUNT(*) FROM system_settings WHERE key IN ('flexible_service_tier', 'presence_penalty', 'frequency_penalty', 'top_p')")
        existing_count = cursor.fetchone()[0]
        
        if existing_count >= 4:
            print("✅ Flexible service tier settings already exist")
            return True
        
        print(f"📊 Found {existing_count} existing flexible tier settings")
        
        # Get admin user ID (first admin user)
        cursor.execute("SELECT id FROM users WHERE is_admin = 1 LIMIT 1")
        admin_result = cursor.fetchone()
        
        if not admin_result:
            print("❌ No admin user found. Please create an admin account first.")
            return False
        
        admin_user_id = admin_result[0]
        print(f"👤 Using admin user ID: {admin_user_id}")
        
        # Define the new settings
        new_settings = [
            {
                'key': 'flexible_service_tier',
                'value': 'true',
                'description': 'Enable flexible service tier for cost optimization'
            },
            {
                'key': 'presence_penalty',
                'value': '0.0',
                'description': 'Presence penalty for OpenAI API (0.0 = disabled)'
            },
            {
                'key': 'frequency_penalty',
                'value': '0.0',
                'description': 'Frequency penalty for OpenAI API (0.0 = disabled)'
            },
            {
                'key': 'top_p',
                'value': '0.9',
                'description': 'Top-p sampling for OpenAI API (0.9 = focused responses)'
            }
        ]
        
        # Add each setting if it doesn't exist
        added_count = 0
        for setting in new_settings:
            cursor.execute("SELECT COUNT(*) FROM system_settings WHERE key = ?", (setting['key'],))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO system_settings (key, value, description, updated_at, updated_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    setting['key'],
                    setting['value'],
                    setting['description'],
                    datetime.utcnow().isoformat(),
                    admin_user_id
                ))
                added_count += 1
                print(f"✅ Added setting: {setting['key']} = {setting['value']}")
            else:
                print(f"ℹ️ Setting already exists: {setting['key']}")
        
        # Commit the changes
        conn.commit()
        print(f"✅ Successfully added {added_count} new flexible service tier settings")
        
        # Verify the settings
        cursor.execute("SELECT key, value FROM system_settings WHERE key IN ('flexible_service_tier', 'presence_penalty', 'frequency_penalty', 'top_p')")
        settings = cursor.fetchall()
        
        print("\n📋 Current flexible service tier settings:")
        for key, value in settings:
            print(f"  • {key}: {value}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Flexible Service Tier Migration Script")
    print("=" * 50)
    
    success = migrate_flexible_tier()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nThe following new features are now available:")
        print("• Flexible service tier toggle for cost optimization")
        print("• Configurable presence penalty (-2.0 to 2.0)")
        print("• Configurable frequency penalty (-2.0 to 2.0)")
        print("• Configurable top-p sampling (0.0 to 1.0)")
        print("\nYou can now manage these settings from the admin dashboard!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)
