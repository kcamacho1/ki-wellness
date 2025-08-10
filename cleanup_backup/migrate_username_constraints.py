#!/usr/bin/env python3
"""
Database migration script to add case-insensitive unique constraints
This script will:
1. Add case-insensitive unique constraints for usernames and emails
2. Update existing data to ensure uniqueness
"""

import os
import sys
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from main import app, db, User

def migrate_username_constraints():
    """Run the username constraints migration"""
    print("Starting username constraints migration...")
    
    with app.app_context():
        try:
            # Check if case-insensitive unique constraints exist
            inspector = db.inspect(db.engine)
            
            # Get existing indexes
            indexes = inspector.get_indexes('users')
            existing_indexes = [idx['name'] for idx in indexes]
            
            print("Existing indexes:", existing_indexes)
            
            # Add case-insensitive unique constraints if they don't exist
            with db.engine.connect() as conn:
                # Check if we need to add case-insensitive constraints
                # This is a PostgreSQL-specific approach
                try:
                    # Create case-insensitive unique indexes
                    print("Adding case-insensitive unique constraints...")
                    
                    # For username (case-insensitive)
                    conn.execute(text("""
                        CREATE UNIQUE INDEX IF NOT EXISTS users_username_lower_idx 
                        ON users (LOWER(username))
                    """))
                    
                    # For email (case-insensitive)
                    conn.execute(text("""
                        CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_idx 
                        ON users (LOWER(email))
                    """))
                    
                    conn.commit()
                    print("Case-insensitive unique constraints added successfully!")
                    
                except Exception as e:
                    print(f"Note: Case-insensitive constraints may already exist or database doesn't support them: {e}")
                
                # Update existing usernames to ensure they're unique (lowercase)
                print("Ensuring username uniqueness...")
                users = conn.execute(text("SELECT id, username FROM users")).fetchall()
                
                for user in users:
                    # Convert username to lowercase for consistency
                    lowercase_username = user.username.lower()
                    if lowercase_username != user.username:
                        conn.execute(text("UPDATE users SET username = :username WHERE id = :id"), 
                                    {"username": lowercase_username, "id": user.id})
                        print(f"Updated username '{user.username}' to '{lowercase_username}'")
                
                # Update existing emails to ensure they're unique (lowercase)
                print("Ensuring email uniqueness...")
                users = conn.execute(text("SELECT id, email FROM users")).fetchall()
                
                for user in users:
                    # Convert email to lowercase for consistency
                    lowercase_email = user.email.lower()
                    if lowercase_email != user.email:
                        conn.execute(text("UPDATE users SET email = :email WHERE id = :id"), 
                                    {"email": lowercase_email, "id": user.id})
                        print(f"Updated email '{user.email}' to '{lowercase_email}'")
                
                conn.commit()
                print("Username and email uniqueness migration completed successfully!")
                
        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    migrate_username_constraints()
