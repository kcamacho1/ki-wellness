#!/usr/bin/env python3
"""
Database initialization script for Ki Wellness Profile System
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from config import config

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=config['development'].POSTGRES_HOST,
            port=config['development'].POSTGRES_PORT,
            user=config['development'].POSTGRES_USER,
            password=config['development'].POSTGRES_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (config['development'].POSTGRES_DB,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {config["development"].POSTGRES_DB}')
            print(f"Database '{config['development'].POSTGRES_DB}' created successfully!")
        else:
            print(f"Database '{config['development'].POSTGRES_DB}' already exists.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def create_tables():
    """Create the tables using Flask-SQLAlchemy"""
    try:
        from app.main import app, db
        
        with app.app_context():
            db.create_all()
            print("Tables created successfully!")
            
    except Exception as e:
        print(f"Error creating tables: {e}")
        sys.exit(1)

def main():
    """Main function to initialize the database"""
    print("Initializing Ki Wellness Database...")
    
    # Create database
    create_database()
    
    # Create tables
    create_tables()
    
    print("Database initialization completed successfully!")
    print("\nTo start the application, run:")
    print("python app/main.py")

if __name__ == "__main__":
    main()
