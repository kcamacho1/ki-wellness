#!/usr/bin/env python3
"""
Migration script to add AI usage tracking and revenue analytics tables
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if not database_url:
        # Fallback to SQLite for local development
        database_url = 'sqlite:///ki_wellness.db'
    
    return database_url

def migrate_database():
    """Add AI usage tracking and revenue analytics tables"""
    print("🔄 Starting analytics system migration...")
    
    try:
        engine = create_engine(get_database_url())
        
        with engine.connect() as conn:
            # Check if ai_usage_log table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'ai_usage_log'
                );
            """))
            
            if not result.scalar():
                print("📊 Creating ai_usage_log table...")
                conn.execute(text("""
                    CREATE TABLE ai_usage_log (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        session_id VARCHAR(255) NOT NULL,
                        model_used VARCHAR(255) NOT NULL,
                        input_tokens INTEGER NOT NULL,
                        output_tokens INTEGER NOT NULL,
                        input_cost NUMERIC(10,6) NOT NULL,
                        output_cost NUMERIC(10,6) NOT NULL,
                        total_cost NUMERIC(10,6) NOT NULL,
                        endpoint VARCHAR(100) NOT NULL,
                        response_time_ms INTEGER,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES "user" (id)
                    );
                """))
                
                # Create indexes for better performance
                conn.execute(text("""
                    CREATE INDEX idx_ai_usage_user_id ON ai_usage_log (user_id);
                    CREATE INDEX idx_ai_usage_created_at ON ai_usage_log (created_at);
                    CREATE INDEX idx_ai_usage_model ON ai_usage_log (model_used);
                    CREATE INDEX idx_ai_usage_endpoint ON ai_usage_log (endpoint);
                """))
                
                print("✅ ai_usage_log table created successfully")
            else:
                print("ℹ️ ai_usage_log table already exists")
            
            # Check if revenue_log table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'revenue_log'
                );
            """))
            
            if not result.scalar():
                print("💰 Creating revenue_log table...")
                conn.execute(text("""
                    CREATE TABLE revenue_log (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        revenue_type VARCHAR(50) NOT NULL,
                        amount NUMERIC(10,2) NOT NULL,
                        currency VARCHAR(3) DEFAULT 'USD',
                        stripe_payment_intent_id VARCHAR(255),
                        stripe_subscription_id VARCHAR(255),
                        description TEXT,
                        status VARCHAR(50) DEFAULT 'completed',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES "user" (id)
                    );
                """))
                
                # Create indexes for better performance
                conn.execute(text("""
                    CREATE INDEX idx_revenue_user_id ON revenue_log (user_id);
                    CREATE INDEX idx_revenue_created_at ON revenue_log (created_at);
                    CREATE INDEX idx_revenue_type ON revenue_log (revenue_type);
                    CREATE INDEX idx_revenue_status ON revenue_log (status);
                """))
                
                print("✅ revenue_log table created successfully")
            else:
                print("ℹ️ revenue_log table already exists")
            
            conn.commit()
            print("\n🎉 Analytics migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
