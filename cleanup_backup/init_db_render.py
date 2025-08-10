#!/usr/bin/env python3
"""
Database initialization script for Render deployment
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app, db

def init_database():
    """Initialize the database tables"""
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            sys.exit(1)

if __name__ == "__main__":
    init_database()
