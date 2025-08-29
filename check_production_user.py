#!/usr/bin/env python3
"""
Check for user in production database using direct SQL
"""

import os
import subprocess
from urllib.parse import urlparse

def check_user_in_production(email):
    """Check if user exists in production database"""
    
    # Production database URL
    database_url = "postgresql://ki_wellness_db_user:VWjyj6At5tflp2AfpJf2uDRlIZkz7wNK@dpg-d2hlcq24d50c739i5usg-a.oregon-postgres.render.com/ki_wellness_db"
    
    print(f"🔍 Checking for user: {email}")
    print("🔗 Connecting to production database...")
    
    try:
        # Query to find user
        sql_query = f"""
        SELECT 
            id, username, email, name, role, email_verified, created_at, last_login
        FROM "user" 
        WHERE email = '{email}';
        """
        
        # Run psql command
        result = subprocess.run([
            'psql', database_url, '-c', sql_query
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if '(0 rows)' in output:
                print(f"❌ User '{email}' not found in production database")
            else:
                print(f"✅ User found in production database:")
                print(output)
        else:
            print(f"❌ Error querying database: {result.stderr}")
            
        # Also check total user count
        count_query = 'SELECT COUNT(*) as total_users FROM "user";'
        result2 = subprocess.run([
            'psql', database_url, '-c', count_query
        ], capture_output=True, text=True, timeout=10)
        
        if result2.returncode == 0:
            print(f"\n📊 Total users in production database:")
            print(result2.stdout.strip())
        
        # Check recent users
        recent_query = '''
        SELECT email, created_at 
        FROM "user" 
        ORDER BY created_at DESC 
        LIMIT 5;
        '''
        result3 = subprocess.run([
            'psql', database_url, '-c', recent_query
        ], capture_output=True, text=True, timeout=10)
        
        if result3.returncode == 0:
            print(f"\n🕐 Recent users in production database:")
            print(result3.stdout.strip())
            
    except subprocess.TimeoutExpired:
        print("❌ Database query timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    check_user_in_production('stephaniecamacho1@gmail.com')
