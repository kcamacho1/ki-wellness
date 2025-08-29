#!/usr/bin/env python3
"""
SQL-based migration script to add last_login field to User model
Uses psql command directly to avoid psycopg2 compatibility issues
"""

import os
import subprocess
import sys
from urllib.parse import urlparse

def run_sql_command(database_url, sql_command):
    """Run SQL command using psql directly"""
    try:
        # Parse the database URL
        parsed = urlparse(database_url)
        
        # Build psql command
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        cmd = [
            'psql',
            '-h', parsed.hostname,
            '-p', str(parsed.port or 5432),
            '-U', parsed.username,
            '-d', parsed.path[1:],  # Remove leading /
            '-c', sql_command
        ]
        
        print(f"🔄 Running: {sql_command}")
        
        # Run the command
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ SQL command executed successfully")
            if result.stdout.strip():
                print(f"📋 Output: {result.stdout.strip()}")
            return True
        else:
            error_msg = result.stderr.strip()
            if 'already exists' in error_msg.lower() or 'duplicate column' in error_msg.lower():
                print("✅ Column already exists")
                return True
            else:
                print(f"❌ SQL Error: {error_msg}")
                return False
                
    except subprocess.TimeoutExpired:
        print("❌ SQL command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running SQL command: {e}")
        return False

def add_last_login_field():
    """Add last_login field to User table using direct SQL"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    print(f"🔄 Connecting to PostgreSQL database...")
    
    # SQL command to add the column
    sql_command = 'ALTER TABLE "user" ADD COLUMN last_login TIMESTAMP;'
    
    # Try to add the column
    success = run_sql_command(database_url, sql_command)
    
    if success:
        # Verify the column was added
        verify_sql = 'SELECT column_name FROM information_schema.columns WHERE table_name = \'user\' AND column_name = \'last_login\';'
        print("🔍 Verifying column was added...")
        verify_success = run_sql_command(database_url, verify_sql)
        return verify_success
    
    return success

if __name__ == '__main__':
    print("🔄 Adding last_login field to User model using direct SQL...")
    print("📍 Working directory:", os.getcwd())
    print("📁 Script location:", os.path.dirname(os.path.abspath(__file__)))
    
    # Check if psql is available
    try:
        subprocess.run(['psql', '--version'], capture_output=True, check=True)
        print("✅ psql command found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ psql command not found. This script requires PostgreSQL client tools.")
        sys.exit(1)
    
    success = add_last_login_field()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
