#!/usr/bin/env python3
"""
Migration: Add dynamic_image_url field to Recipe model
Adds support for storing dynamically fetched images from Pexels API
"""

import os
import sys
from sqlalchemy import text

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db
from config.environment import get_environment_detector

def migrate():
    """Add dynamic_image_url field to Recipe table"""
    with app.app_context():
        detector = get_environment_detector()
        
        if detector.is_production:
            # PostgreSQL syntax
            sql = text('ALTER TABLE "recipe" ADD COLUMN dynamic_image_url VARCHAR(500)')
        else:
            # SQLite syntax
            sql = text('ALTER TABLE recipe ADD COLUMN dynamic_image_url VARCHAR(500)')
        
        try:
            db.session.execute(sql)
            db.session.commit()
            print("✅ Added dynamic_image_url field to Recipe table")
            return True
        except Exception as e:
            print(f"❌ Error adding dynamic_image_url field: {e}")
            db.session.rollback()
            return False

def rollback():
    """Remove dynamic_image_url field from Recipe table"""
    with app.app_context():
        detector = get_environment_detector()
        
        if detector.is_production:
            # PostgreSQL syntax
            sql = text('ALTER TABLE "recipe" DROP COLUMN dynamic_image_url')
        else:
            # SQLite doesn't support DROP COLUMN easily, so we'll skip rollback for SQLite
            print("⚠️ SQLite doesn't support DROP COLUMN easily. Manual cleanup may be required.")
            return True
        
        try:
            db.session.execute(sql)
            db.session.commit()
            print("✅ Removed dynamic_image_url field from Recipe table")
            return True
        except Exception as e:
            print(f"❌ Error removing dynamic_image_url field: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate Recipe table to add dynamic_image_url field")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
