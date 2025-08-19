#!/usr/bin/env python3
"""
Migration script to add PaymentSession table for human help payments
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Run the migration to add PaymentSession table"""
    
    # Database configuration
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Normalize old Heroku-style URLs
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
    else:
        # Development - SQLite fallback
        db_url = 'sqlite:///ki_wellness.db'
    
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # Check if PaymentSession table already exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'payment_session'
                );
            """))
            
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ PaymentSession table already exists. Skipping migration.")
                return
            
            # Create PaymentSession table
            conn.execute(text("""
                CREATE TABLE payment_session (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id INTEGER REFERENCES "user"(id),
                    email VARCHAR(120) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    payment_type VARCHAR(50) NOT NULL,
                    stripe_payment_intent_id VARCHAR(255),
                    amount INTEGER NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    calendly_link_sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Add indexes for better performance
            conn.execute(text("""
                CREATE INDEX idx_payment_session_user_id ON payment_session(user_id);
                CREATE INDEX idx_payment_session_status ON payment_session(status);
                CREATE INDEX idx_payment_session_payment_intent ON payment_session(stripe_payment_intent_id);
            """))
            
            conn.commit()
            print("✅ PaymentSession table created successfully!")
            
    except Exception as e:
        print(f"❌ Error creating PaymentSession table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔄 Running migration: Add PaymentSession table...")
    run_migration()
    print("✅ Migration completed successfully!")
