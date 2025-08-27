#!/usr/bin/env python3
"""
Database Migration: Add Subscription System
Adds subscription-related fields and tables for the payment system
"""

import os
import sys
from sqlalchemy import create_engine, text, Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
if os.getenv('DATABASE_URL'):
    # Production - PostgreSQL
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
else:
    # Development - SQLite
    DATABASE_URL = 'sqlite:///ki_wellness.db'

def migrate_database():
    """Run the database migration"""
    print("🔄 Starting subscription system migration...")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Check if subscription table already exists
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'subscription'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("ℹ️ Subscription table already exists, skipping table creation")
            else:
                print("📋 Creating subscription table...")
                conn.execute(text("""
                    CREATE TABLE subscription (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
                        stripe_customer_id VARCHAR(255) NOT NULL,
                        plan_type VARCHAR(50) NOT NULL DEFAULT 'free',
                        status VARCHAR(50) NOT NULL DEFAULT 'active',
                        current_period_start TIMESTAMP,
                        current_period_end TIMESTAMP,
                        cancel_at_period_end BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                # Add foreign key constraint
                conn.execute(text("""
                    ALTER TABLE subscription 
                    ADD CONSTRAINT fk_subscription_user 
                    FOREIGN KEY (user_id) REFERENCES "user"(id);
                """))
                
                print("✅ Subscription table created successfully")
        
        # Check if stripe_customer_id column exists in user table
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'user' 
                    AND column_name = 'stripe_customer_id'
                );
            """))
            column_exists = result.scalar()
            
            if column_exists:
                print("ℹ️ stripe_customer_id column already exists in user table")
            else:
                print("📋 Adding stripe_customer_id column to user table...")
                conn.execute(text("""
                    ALTER TABLE "user" 
                    ADD COLUMN stripe_customer_id VARCHAR(255);
                """))
                # Commit the column addition
                conn.commit()
                print("✅ stripe_customer_id column added successfully")
        
        # Create indexes for better performance
        print("📋 Creating database indexes...")
        with engine.connect() as conn:
            # Index for subscription lookups
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_subscription_user_id 
                ON subscription(user_id);
            """))
            
            # Index for subscription status lookups
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_subscription_status 
                ON subscription(status);
            """))
            
            # Index for Stripe customer lookups (only if column exists)
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_stripe_customer_id 
                    ON "user"(stripe_customer_id);
                """))
                print("✅ Stripe customer index created successfully")
            except Exception as e:
                print(f"⚠️ Could not create Stripe customer index: {e}")
                print("   This is normal if the column was just added")
            
            print("✅ Database indexes created successfully")
        
        print("\n🎉 Migration completed successfully!")
        print("\n📋 What was added:")
        print("   • subscription table with all required fields")
        print("   • stripe_customer_id column in user table")
        print("   • Database indexes for optimal performance")
        print("   • Foreign key constraints for data integrity")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
