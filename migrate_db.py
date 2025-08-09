#!/usr/bin/env python3
"""
Database migration script to add avatar column to user_profiles table
"""

import psycopg2
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from config import config

def migrate_database():
    """Add avatar column to user_profiles table"""
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            host=config['development'].POSTGRES_HOST,
            port=config['development'].POSTGRES_PORT,
            user=config['development'].POSTGRES_USER,
            password=config['development'].POSTGRES_PASSWORD,
            database=config['development'].POSTGRES_DB
        )
        cursor = conn.cursor()
        
        # Check if avatar column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'avatar'
        """)
        
        if cursor.fetchone():
            print("✅ Avatar column already exists")
        else:
            # Add avatar column
            cursor.execute("""
                ALTER TABLE user_profiles 
                ADD COLUMN avatar VARCHAR(100) DEFAULT 'default-avatar.png'
            """)
            conn.commit()
            print("✅ Avatar column added successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error migrating database: {e}")
        sys.exit(1)

def main():
    """Main function to run migration"""
    print("🔄 Migrating database to add avatar column...")
    print("=" * 50)
    
    migrate_database()
    
    print("\n✅ Migration completed successfully!")
    print("🚀 You can now run the application with: python run.py")

if __name__ == "__main__":
    main()
