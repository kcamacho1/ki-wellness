#!/usr/bin/env python3
"""
Database Reset Script for Render
================================

This script resets your Render PostgreSQL database by dropping all tables.
Your application will recreate the schema when it restarts.

Author: Ki Wellness Team
Version: 1.0
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text

def reset_database():
    """Reset the database by dropping all tables"""
    
    print("🗄️  Database Reset for Render")
    print("=============================")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # Get database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not found")
        print("💡 Please set the DATABASE_URL environment variable")
        return False
    
    print(f"🗄️  Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful")
            
            # Get all table names
            print("🔍 Getting list of tables...")
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            
            tables = [row[0] for row in result]
            
            if not tables:
                print("ℹ️  No tables found - database is already empty")
                return True
            
            print(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
            print()
            
            # Confirm reset
            response = input("⚠️  This will delete ALL tables and data. Continue? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("❌ Reset cancelled by user")
                return False
            
            print()
            print("🗑️  Dropping all tables...")
            
            # Disable foreign key checks temporarily
            conn.execute(text("SET session_replication_role = replica;"))
            
            # Drop all tables
            for table in tables:
                print(f"   🗑️  Dropping table: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            # Re-enable foreign key checks
            conn.execute(text("SET session_replication_role = DEFAULT;"))
            conn.commit()
            
            print()
            print("✅ Database reset completed successfully!")
            print("💡 Your application will recreate the schema when it restarts.")
            return True
            
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    if success:
        print()
        print("🎉 Database reset completed!")
        print("🔄 Restart your application to recreate the schema.")
        sys.exit(0)
    else:
        print()
        print("💥 Database reset failed!")
        sys.exit(1)
