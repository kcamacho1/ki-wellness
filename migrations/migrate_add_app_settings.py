#!/usr/bin/env python3
"""
Migration script to add AppSettings table
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from app import AppSettings

def create_app_settings_table():
    """Create the AppSettings table and initialize default settings"""
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✅ Database tables created/updated successfully")
            
            # Initialize default settings
            settings = [
                ('new_accounts_enabled', 'true', 'Enable or disable new user account creation'),
                ('maintenance_mode', 'false', 'Enable maintenance mode for the application'),
                ('max_users', '1000', 'Maximum number of users allowed in the system'),
                ('allowed_emails', '', 'Comma-separated list of email addresses allowed to register even when disabled')
            ]
            
            for key, value, description in settings:
                setting = AppSettings.query.filter_by(key=key).first()
                if not setting:
                    setting = AppSettings(key=key, value=value, description=description)
                    db.session.add(setting)
                    print(f"✅ Added setting: {key} = {value}")
                else:
                    print(f"ℹ️  Setting already exists: {key}")
            
            db.session.commit()
            print("✅ AppSettings initialized successfully")
            
            # Display current settings
            print("\n📋 Current App Settings:")
            all_settings = AppSettings.query.all()
            for setting in all_settings:
                print(f"  • {setting.key}: {setting.value}")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    print("🚀 Starting AppSettings migration...")
    success = create_app_settings_table()
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
