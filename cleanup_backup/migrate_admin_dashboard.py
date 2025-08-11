#!/usr/bin/env python3
"""
Migration script to add is_active field to User model for admin dashboard functionality.
This script should be run after updating the User model to include the is_active field.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, db, User
from sqlalchemy import text

def migrate_admin_dashboard():
    """Add is_active field to existing users and set them as active"""
    with app.app_context():
        try:
            print("🔄 Starting admin dashboard migration...")
            
            # Check if is_active column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'is_active' not in columns:
                print("📝 Adding is_active column to users table...")
                
                # Add the is_active column with default value True
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL
                    """))
                    conn.commit()
                
                print("✅ is_active column added successfully!")
            else:
                print("ℹ️  is_active column already exists")
            
            # Update all existing users to have is_active = True
            print("🔄 Updating existing users to active status...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE users 
                    SET is_active = 1 
                    WHERE is_active IS NULL
                """))
                conn.commit()
            
            print("✅ All users updated to active status!")
            
            # Verify the migration
            user_count = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            print(f"📊 Migration verification:")
            print(f"   Total users: {user_count}")
            print(f"   Active users: {active_users}")
            
            if user_count == active_users:
                print("✅ Migration completed successfully!")
            else:
                print("⚠️  Warning: Some users may not have been updated")
                
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    print("🚀 Admin Dashboard Migration Script")
    print("=" * 40)
    
    success = migrate_admin_dashboard()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now use the enhanced admin dashboard with user management features.")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
        sys.exit(1)
