#!/usr/bin/env python3
"""
Quick Fix for Missing is_active Column
======================================

This script quickly adds the missing is_active column to the users table
using the existing Flask app context and database connection.

Author: Ki Wellness Team
Version: 1.0
"""

import os
import sys
from sqlalchemy import text

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def quick_fix_is_active():
    """Quick fix to add the missing is_active column"""
    
    try:
        # Import the Flask app and database
        from app.main import app, db
        
        print("🔧 Quick Fix: Adding missing is_active column...")
        
        with app.app_context():
            # Check if the column already exists
            try:
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'is_active'
                """))
                
                if result.fetchone():
                    print("✅ is_active column already exists")
                    return True
                    
            except Exception as e:
                print(f"⚠️  Error checking column existence: {e}")
            
            # Add the missing column
            try:
                print("➕ Adding is_active column to users table...")
                db.session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL
                """))
                db.session.commit()
                print("✅ Successfully added is_active column")
                return True
                
            except Exception as e:
                print(f"❌ Error adding column: {e}")
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"❌ Error in quick fix: {e}")
        return False

if __name__ == "__main__":
    success = quick_fix_is_active()
    if success:
        print("🎉 Quick fix completed successfully!")
        sys.exit(0)
    else:
        print("💥 Quick fix failed!")
        sys.exit(1)
