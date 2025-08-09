#!/usr/bin/env python3
"""
Migration script to add admin functionality
- Adds is_admin column to users table
- Sets ADMIN_EMAIL from environment as the only admin user
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app, db
from sqlalchemy import text

def migrate_admin():
    """Add admin functionality to the database"""
    with app.app_context():
        try:
            # Get admin email from environment variable
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@kiwellness.org')
            
            # Add is_admin column to users table
            with db.engine.connect() as conn:
                # Check if column already exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'is_admin'
                """))
                
                if not result.fetchone():
                    print("Adding is_admin column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL"))
                    conn.commit()
                    print("✓ is_admin column added successfully")
                else:
                    print("✓ is_admin column already exists")
                
                # Set admin privileges for admin email
                print(f"Setting admin privileges for {admin_email}...")
                result = conn.execute(text("""
                    UPDATE users 
                    SET is_admin = TRUE 
                    WHERE LOWER(email) = :admin_email
                """), {"admin_email": admin_email.lower()})
                conn.commit()
                
                if result.rowcount > 0:
                    print(f"✓ Admin privileges set for {result.rowcount} user(s)")
                else:
                    print(f"⚠ No user found with email {admin_email}")
                    print("  Admin privileges will be set when this user registers")
                
                # Verify admin user exists
                result = conn.execute(text("""
                    SELECT username, email, is_admin 
                    FROM users 
                    WHERE LOWER(email) = :admin_email
                """), {"admin_email": admin_email.lower()})
                
                admin_user = result.fetchone()
                if admin_user:
                    print(f"✓ Admin user found: {admin_user[0]} ({admin_user[1]}) - Admin: {admin_user[2]}")
                else:
                    print(f"⚠ Admin user not found. Create account with {admin_email} to get admin privileges")
                
                # Show all users and their admin status
                print("\nCurrent users and admin status:")
                result = conn.execute(text("SELECT username, email, is_admin FROM users ORDER BY created_at"))
                users = result.fetchall()
                
                for user in users:
                    admin_status = "ADMIN" if user[2] else "User"
                    print(f"  - {user[0]} ({user[1]}) - {admin_status}")
                
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False
        
        print("\n✅ Admin migration completed successfully!")
        return True

if __name__ == "__main__":
    print("Starting admin migration...")
    success = migrate_admin()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)
