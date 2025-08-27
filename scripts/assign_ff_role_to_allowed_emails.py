#!/usr/bin/env python3
"""
Script to assign 'ff' role to all users whose email addresses are in the allowed emails list
from the admin dashboard settings.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_connection():
    """Get database connection"""
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
    else:
        db_url = 'sqlite:///ki_wellness.db'
    
    return create_engine(db_url)

def get_allowed_emails():
    """Get the allowed emails from app settings"""
    engine = get_database_connection()
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT value FROM app_settings WHERE key = 'allowed_emails'
        """))
        
        setting = result.fetchone()
        if not setting or not setting[0]:
            print("❌ No allowed emails found in app settings")
            return []
        
        # Parse comma-separated emails
        allowed_emails = [email.strip().lower() for email in setting[0].split(',') if email.strip()]
        return allowed_emails

def assign_ff_role_to_allowed_emails():
    """Assign 'ff' role to all users with allowed email addresses"""
    engine = get_database_connection()
    
    # Get allowed emails
    allowed_emails = get_allowed_emails()
    if not allowed_emails:
        return
    
    print(f"📧 Found {len(allowed_emails)} allowed email addresses:")
    for email in allowed_emails:
        print(f"  - {email}")
    
    with engine.connect() as conn:
        # Find users with allowed email addresses
        placeholders = ','.join([f"'{email}'" for email in allowed_emails])
        result = conn.execute(text(f"""
            SELECT id, username, email, name, role 
            FROM "user" 
            WHERE LOWER(email) IN ({placeholders})
            ORDER BY email
        """))
        
        users = result.fetchall()
        
        if not users:
            print("❌ No users found with the allowed email addresses")
            return
        
        print(f"\n👥 Found {len(users)} users with allowed email addresses:")
        print("=" * 80)
        print(f"{'ID':<4} {'Username':<15} {'Email':<25} {'Name':<20} {'Current Role':<12}")
        print("-" * 80)
        
        updated_count = 0
        already_ff_count = 0
        
        for user in users:
            user_id, username, email, name, current_role = user
            print(f"{user_id:<4} {username:<15} {email:<25} {name:<20} {current_role:<12}")
            
            # Update role to 'ff' if not already
            if current_role != 'ff':
                conn.execute(text("UPDATE \"user\" SET role = 'ff' WHERE id = :user_id"), 
                            {"user_id": user_id})
                updated_count += 1
                print(f"  ✅ Updated {username} ({email}) to 'ff' role")
            else:
                already_ff_count += 1
                print(f"  ℹ️  {username} ({email}) already has 'ff' role")
        
        conn.commit()
        
        print(f"\n📊 Summary:")
        print(f"  - Total users with allowed emails: {len(users)}")
        print(f"  - Updated to 'ff' role: {updated_count}")
        print(f"  - Already had 'ff' role: {already_ff_count}")
        
        if updated_count > 0:
            print(f"\n✅ Successfully assigned 'ff' role to {updated_count} users!")
        else:
            print(f"\nℹ️  All users already have the 'ff' role.")

def main():
    """Main function"""
    print("🔧 Assign FF Role to Allowed Emails")
    print("=" * 40)
    
    try:
        assign_ff_role_to_allowed_emails()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
