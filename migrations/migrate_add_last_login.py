#!/usr/bin/env python3
"""
Migration script to add last_login field to User model
"""

import os
import sys
from datetime import datetime

# Add the parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from app import app, db, User
    from sqlalchemy import text
except ImportError:
    # Fallback for different import structures
    try:
        import app as flask_app
        app = flask_app.app
        db = flask_app.db
        User = flask_app.User
        from sqlalchemy import text
    except ImportError:
        # Last resort - direct import
        from database import db, User
        from flask import Flask
        from dotenv import load_dotenv
        from sqlalchemy import text
        
        load_dotenv()
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
        
        # Database configuration
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # Use external database URL
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        else:
            # Use local database file
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'ki_wellness_dev.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)

def add_last_login_field():
    """Add last_login field to User table"""
    with app.app_context():
        try:
            # Check if we're using PostgreSQL or SQLite
            db_url = str(db.engine.url.drivername)
            
            if 'postgresql' in db_url:
                # PostgreSQL version with quoted table name
                sql = '''
                    ALTER TABLE "user" 
                    ADD COLUMN last_login TIMESTAMP
                '''
            else:
                # SQLite version
                sql = '''
                    ALTER TABLE user 
                    ADD COLUMN last_login DATETIME
                '''
            
            # Add last_login column to User table
            with db.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print("✅ Successfully added last_login field to User table")
            
        except Exception as e:
            print(f"❌ Error adding last_login field: {e}")
            # Check if column already exists
            try:
                with db.engine.connect() as conn:
                    if 'postgresql' in db_url:
                        result = conn.execute(text('SELECT last_login FROM "user" LIMIT 1'))
                    else:
                        result = conn.execute(text('SELECT last_login FROM user LIMIT 1'))
                print("✅ last_login field already exists")
            except:
                print("❌ Column does not exist and could not be created")
                return False
        
        return True

if __name__ == '__main__':
    print("🔄 Adding last_login field to User model...")
    success = add_last_login_field()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
