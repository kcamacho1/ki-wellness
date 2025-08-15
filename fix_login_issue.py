#!/usr/bin/env python3
"""
Comprehensive Fix for Login Issue
=================================

This script fixes the login issue by:
1. Checking for PostgreSQL adapter
2. Adding the missing is_active column
3. Providing detailed error reporting

Author: Ki Wellness Team
Version: 1.0
"""

import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def check_postgresql_adapter():
    """Check if PostgreSQL adapter is available"""
    print("🔍 Checking PostgreSQL adapter...")
    
    try:
        import psycopg2
        print("✅ psycopg2 found")
        return True
    except ImportError:
        try:
            import psycopg
            print("✅ psycopg found")
            return True
        except ImportError:
            print("❌ No PostgreSQL adapter found")
            print("💡 Installing psycopg2-binary...")
            
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
                print("✅ psycopg2-binary installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to install psycopg2-binary")
                return False

def fix_is_active_column():
    """Fix the missing is_active column"""
    print("🔧 Fixing missing is_active column...")
    
    try:
        # Import the Flask app and database
        from app.main import app, db
        from sqlalchemy import text
        
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
        print(f"❌ Error in fix: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 Comprehensive Login Issue Fix")
    print("================================")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # Check PostgreSQL adapter
    if not check_postgresql_adapter():
        print("❌ Cannot proceed without PostgreSQL adapter")
        return False
    
    print()
    
    # Fix the column
    if not fix_is_active_column():
        print("❌ Failed to fix is_active column")
        return False
    
    print()
    print("🎉 Fix completed successfully!")
    print("💡 Users should now be able to log in successfully.")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ All fixes applied successfully!")
        sys.exit(0)
    else:
        print("💥 Fix failed!")
        sys.exit(1)
