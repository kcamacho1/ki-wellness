#!/usr/bin/env python3
"""
Migration script to add missing agreement columns to user table
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def add_user_agreement_columns():
    """Add missing agreement columns to user table"""
    
    with app.app_context():
        try:
            print("Adding missing agreement columns to user table...")
            
            # Add missing columns
            columns = [
                "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS agreed_to_terms BOOLEAN DEFAULT FALSE",
                "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS agreed_to_privacy BOOLEAN DEFAULT FALSE", 
                "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS agreed_to_disclaimer BOOLEAN DEFAULT FALSE",
                "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS agreements_date TIMESTAMP"
            ]
            
            for column_sql in columns:
                try:
                    db.session.execute(text(column_sql))
                    print(f"✓ Added column: {column_sql.split('ADD COLUMN IF NOT EXISTS ')[1].split(' ')[0]}")
                except Exception as e:
                    print(f"⚠ Column might already exist: {e}")
            
            db.session.commit()
            print("✓ All agreement columns added successfully!")
            
        except Exception as e:
            print(f"❌ Error adding columns: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    add_user_agreement_columns()
