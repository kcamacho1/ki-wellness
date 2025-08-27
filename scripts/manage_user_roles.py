#!/usr/bin/env python3
"""
Utility script to manage user roles
Supports setting roles: 'admin', 'user', 'ff'
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

def list_users():
    """List all users with their roles"""
    engine = get_database_connection()
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, username, email, name, role, is_admin 
            FROM "user" 
            ORDER BY id
        """))
        
        users = result.fetchall()
        
        print("\n📋 Current Users:")
        print("=" * 80)
        print(f"{'ID':<4} {'Username':<15} {'Email':<25} {'Name':<20} {'Role':<8} {'Admin'}")
        print("-" * 80)
        
        for user in users:
            print(f"{user[0]:<4} {user[1]:<15} {user[2]:<25} {user[3]:<20} {user[4]:<8} {user[5]}")
        
        print(f"\nTotal users: {len(users)}")

def set_user_role(user_id, role):
    """Set user role"""
    if role not in ['admin', 'user', 'ff']:
        print(f"❌ Invalid role: {role}. Must be 'admin', 'user', or 'ff'")
        return False
    
    engine = get_database_connection()
    
    with engine.connect() as conn:
        # Check if user exists
        result = conn.execute(text("SELECT username, email FROM \"user\" WHERE id = :user_id"), 
                            {"user_id": user_id})
        user = result.fetchone()
        
        if not user:
            print(f"❌ User with ID {user_id} not found")
            return False
        
        # Update user role
        conn.execute(text("UPDATE \"user\" SET role = :role WHERE id = :user_id"), 
                    {"role": role, "user_id": user_id})
        
        # If setting admin role, also set is_admin to true
        if role == 'admin':
            conn.execute(text("UPDATE \"user\" SET is_admin = true WHERE id = :user_id"), 
                        {"user_id": user_id})
        
        conn.commit()
        
        print(f"✅ Updated user {user[0]} ({user[1]}) to role: {role}")
        return True

def create_ff_user(username, email, name, password):
    """Create a new friends & family user"""
    from werkzeug.security import generate_password_hash
    
    engine = get_database_connection()
    
    with engine.connect() as conn:
        # Check if user already exists
        result = conn.execute(text("SELECT id FROM \"user\" WHERE username = :username OR email = :email"), 
                            {"username": username, "email": email})
        
        if result.fetchone():
            print(f"❌ User with username '{username}' or email '{email}' already exists")
            return False
        
        # Create new user
        password_hash = generate_password_hash(password)
        
        conn.execute(text("""
            INSERT INTO "user" (username, email, password_hash, name, role, is_admin, 
                               agreed_to_terms, agreed_to_privacy, agreed_to_disclaimer)
            VALUES (:username, :email, :password_hash, :name, 'ff', false, true, true, true)
        """), {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "name": name
        })
        
        conn.commit()
        
        print(f"✅ Created new friends & family user: {username} ({email})")
        return True

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_user_roles.py list")
        print("  python manage_user_roles.py set <user_id> <role>")
        print("  python manage_user_roles.py create-ff <username> <email> <name> <password>")
        print("\nRoles: admin, user, ff")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_users()
    
    elif command == "set":
        if len(sys.argv) != 4:
            print("❌ Usage: python manage_user_roles.py set <user_id> <role>")
            return
        
        user_id = int(sys.argv[2])
        role = sys.argv[3]
        set_user_role(user_id, role)
    
    elif command == "create-ff":
        if len(sys.argv) != 6:
            print("❌ Usage: python manage_user_roles.py create-ff <username> <email> <name> <password>")
            return
        
        username = sys.argv[2]
        email = sys.argv[3]
        name = sys.argv[4]
        password = sys.argv[5]
        create_ff_user(username, email, name, password)
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    print("🔧 User Role Management Tool")
    print("=" * 40)
    main()
