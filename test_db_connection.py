#!/usr/bin/env python3
"""
Test database connection script for Render deployment
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app, db

def test_connection():
    """Test database connection"""
    with app.app_context():
        try:
            # Test the connection
            result = db.session.execute('SELECT version()')
            version = result.fetchone()[0]
            print(f"✅ Database connection successful!")
            print(f"📊 PostgreSQL version: {version}")
            
            # Test if tables exist
            tables = db.engine.table_names()
            print(f"📋 Found {len(tables)} tables: {', '.join(tables) if tables else 'None'}")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    test_connection()
