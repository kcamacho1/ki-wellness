"""
Migration to add password reset fields to User table
"""
import os
import psycopg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_database_url():
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if not database_url:
        print("DATABASE_URL environment variable not set")
        return None
    
    return database_url

def migrate():
    """Add password reset fields to User table"""
    database_url = get_database_url()
    
    if not database_url:
        print("Cannot proceed without DATABASE_URL")
        return
    
    try:
        conn = psycopg.connect(database_url, autocommit=True)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' AND table_schema = 'public'
        """)
        columns = [column[0] for column in cursor.fetchall()]
        
        # Add reset_token column if it doesn't exist
        if 'reset_token' not in columns:
            cursor.execute("ALTER TABLE \"user\" ADD COLUMN reset_token TEXT")
            print("Added reset_token column to user table")
        
        # Add reset_token_expires column if it doesn't exist
        if 'reset_token_expires' not in columns:
            cursor.execute("ALTER TABLE \"user\" ADD COLUMN reset_token_expires TIMESTAMP")
            print("Added reset_token_expires column to user table")
        
        print("Password reset migration completed successfully")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate()
