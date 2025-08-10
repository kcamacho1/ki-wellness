#!/usr/bin/env python3
"""
Database migration script to add authentication support
This script will:
1. Create the users table
2. Add user_id column to user_profiles table
3. Update existing data to link to a default user
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from main import app, db, User, UserProfile

def migrate_auth():
    """Run the authentication migration"""
    print("Starting authentication migration...")
    
    with app.app_context():
        try:
            # Create the users table
            print("Creating users table...")
            db.create_all()
            
            # Check if we need to create a default user
            default_user = User.query.filter_by(username='default_user').first()
            if not default_user:
                print("Creating default user...")
                default_password = os.environ.get('DEFAULT_USER_PASSWORD')
                if not default_password:
                    print("Warning: DEFAULT_USER_PASSWORD not set in environment variables")
                    return
                password_hash=generate_password_hash(default_password)
                default_user = User(
                    username='default_user',
                    email='default@kiwellness.org',
                    password_hash=password_hash
                )
                db.session.add(default_user)
                db.session.commit()
                print("Default user created with username: default_user")
                print("Password: [Set via DEFAULT_USER_PASSWORD environment variable]")
            
            # Check if user_profiles table has user_id column
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user_profiles')]
            
            if 'user_id' not in columns:
                print("Adding user_id column to user_profiles table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE user_profiles ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                    conn.commit()
                print("user_id column added to user_profiles table")
            
            # Update existing profiles to link to default user
            print("Updating existing profiles to link to default user...")
            profiles_without_user = UserProfile.query.filter_by(user_id=None).all()
            for profile in profiles_without_user:
                profile.user_id = default_user.id
            db.session.commit()
            print(f"Updated {len(profiles_without_user)} profiles to link to default user")
            
            # Update food journal entries to use user profile ID
            print("Updating food journal entries...")
            with db.engine.connect() as conn:
                food_entries = conn.execute(text("SELECT * FROM food_journal")).fetchall()
                for entry in food_entries:
                    # Check if this entry needs to be updated
                    if entry.user_id is None or entry.user_id not in [p.id for p in UserProfile.query.all()]:
                        # Link to the default user's profile
                        default_profile = UserProfile.query.filter_by(user_id=default_user.id).first()
                        if default_profile:
                            conn.execute(text("UPDATE food_journal SET user_id = :profile_id WHERE id = :entry_id"), 
                                        {"profile_id": default_profile.id, "entry_id": entry.id})
                conn.commit()
            
            # Update mood entries to use user profile ID
            print("Updating mood entries...")
            with db.engine.connect() as conn:
                mood_entries = conn.execute(text("SELECT * FROM mood_entries")).fetchall()
                for entry in mood_entries:
                    # Check if this entry needs to be updated
                    if entry.user_id is None or entry.user_id not in [p.id for p in UserProfile.query.all()]:
                        # Link to the default user's profile
                        default_profile = UserProfile.query.filter_by(user_id=default_user.id).first()
                        if default_profile:
                            conn.execute(text("UPDATE mood_entries SET user_id = :profile_id WHERE id = :entry_id"), 
                                        {"profile_id": default_profile.id, "entry_id": entry.id})
                conn.commit()
            
            # Update patterns cache to use user profile ID
            print("Updating patterns cache...")
            with db.engine.connect() as conn:
                patterns_cache = conn.execute(text("SELECT * FROM patterns_cache")).fetchall()
                for entry in patterns_cache:
                    # Check if this entry needs to be updated
                    if entry.user_id is None or entry.user_id not in [p.id for p in UserProfile.query.all()]:
                        # Link to the default user's profile
                        default_profile = UserProfile.query.filter_by(user_id=default_user.id).first()
                        if default_profile:
                            conn.execute(text("UPDATE patterns_cache SET user_id = :profile_id WHERE id = :entry_id"), 
                                        {"profile_id": default_profile.id, "entry_id": entry.id})
                conn.commit()
            
            db.session.commit()
            print("Authentication migration completed successfully!")
            print("\nDefault login credentials:")
            print("Username: default_user")
            print("Password: [Set via DEFAULT_USER_PASSWORD environment variable]")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    migrate_auth()
