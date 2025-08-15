# Render Database Reset Guide

## Overview
This guide explains how to clear and reset your PostgreSQL database in Render.

## Method 1: Using Render Dashboard (Recommended)

### Step 1: Access Your Database
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Navigate to your PostgreSQL database service
3. Click on your database service name

### Step 2: Reset Database
1. In the database dashboard, go to the **"Settings"** tab
2. Scroll down to find **"Reset Database"** section
3. Click **"Reset Database"** button
4. Confirm the action when prompted

**⚠️ Warning:** This will permanently delete all data in your database.

### Step 3: Update Connection String
After reset, you may need to update your application's `DATABASE_URL` environment variable if it changed.

## Method 2: Using psql Command Line

### Step 1: Get Database Connection Details
From your Render dashboard, get:
- **Host**: Your database host
- **Database Name**: Usually your service name
- **Username**: Your database username
- **Password**: Your database password
- **Port**: Usually 5432

### Step 2: Connect and Reset
```bash
# Connect to your database
psql "postgresql://username:password@host:port/database_name"

# Once connected, drop and recreate the database
DROP DATABASE database_name;
CREATE DATABASE database_name;

# Or if you want to keep the database but clear all tables
\dt  # List all tables
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO username;
```

## Method 3: Using Render CLI

### Step 1: Install Render CLI
```bash
# Install Render CLI
npm install -g @render/cli

# Or using curl
curl -L https://render.com/download-cli/linux | bash
```

### Step 2: Login and Reset
```bash
# Login to Render
render login

# List your services
render ps

# Reset your database service
render ps restart <your-database-service-name>
```

## Method 4: Programmatic Reset (Using Python)

### Create a Reset Script
```python
#!/usr/bin/env python3
"""
Database Reset Script for Render
"""

import os
import sys
from sqlalchemy import create_engine, text

def reset_database():
    """Reset the database by dropping all tables"""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Disable foreign key checks
            conn.execute(text("SET session_replication_role = replica;"))
            
            # Get all table names
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            
            tables = [row[0] for row in result]
            
            # Drop all tables
            for table in tables:
                print(f"🗑️  Dropping table: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            # Re-enable foreign key checks
            conn.execute(text("SET session_replication_role = DEFAULT;"))
            conn.commit()
            
            print("✅ Database reset completed")
            return True
            
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)
```

## Method 5: Complete Database Recreation

### Step 1: Delete and Recreate Service
1. Go to your Render dashboard
2. Select your PostgreSQL database service
3. Go to **"Settings"** tab
4. Scroll to bottom and click **"Delete Service"**
5. Confirm deletion
6. Create a new PostgreSQL service with the same name

### Step 2: Update Environment Variables
Update your application's environment variables with the new database connection string.

## Method 6: Using Database Client

### Using pgAdmin or DBeaver:
1. Connect to your Render database
2. Right-click on your database
3. Select "Drop Database" or "Delete"
4. Create a new database with the same name
5. Your application will recreate tables on next startup

## After Reset

### Step 1: Restart Your Application
Your application will automatically create the database schema when it starts up.

### Step 2: Verify Tables Created
```sql
-- Connect to your database and check tables
\dt

-- Or using SQL
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```

### Step 3: Check Application Logs
Look for messages like:
- "Database schema auto-fixed"
- "Tables created successfully"
- "Database initialization completed"

## Environment Variables

Make sure your application has the correct environment variables:

```bash
# Your database URL should look like:
DATABASE_URL=postgresql+psycopg://username:password@host:port/database_name
```

## Troubleshooting

### If tables aren't created automatically:
1. Check your application logs for errors
2. Ensure your models are properly defined
3. Verify database connection string
4. Check if auto-fix system is working

### If connection fails:
1. Verify database credentials
2. Check if database service is running
3. Ensure network connectivity
4. Check firewall settings

### If you get permission errors:
1. Verify database user permissions
2. Check if user has CREATE TABLE privileges
3. Ensure proper schema access

## Quick Commands

### Reset via Render Dashboard:
1. Go to your database service
2. Settings → Reset Database
3. Confirm action

### Reset via Command Line:
```bash
# Connect and reset
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### Reset via Python:
```bash
# Run the reset script
python reset_database.py
```

## Prevention

To prevent future issues:

1. **Use the auto-fix system** - It's integrated into your application startup
2. **Test locally first** - Always test database changes locally
3. **Use migrations** - Implement proper database migrations
4. **Backup regularly** - Set up automated database backups
5. **Monitor logs** - Watch for database-related errors

## Support

If you encounter issues:

1. Check Render's documentation: https://render.com/docs
2. Review your application logs
3. Verify database connection settings
4. Contact Render support if needed
