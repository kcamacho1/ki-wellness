#!/usr/bin/env python3
"""
Migration script to add subscription system tables to existing databases.
This script adds UserSubscription, SessionCredits, and AIUsageSession tables.
"""

import sqlite3
import os
import sys
from datetime import datetime

def migrate_subscription_system():
    """Add subscription system tables to database"""
    
    # Get the database path
    db_path = 'ki_wellness.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starting subscription system migration...")
        
        # Create UserSubscription table
        print("➕ Creating UserSubscription table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                subscription_type VARCHAR(20) NOT NULL DEFAULT 'subscription',
                stripe_subscription_id VARCHAR(100),
                stripe_customer_id VARCHAR(100),
                monthly_fee_usd REAL DEFAULT 10.0,
                sessions_per_month INTEGER DEFAULT 600,
                sessions_used_this_month INTEGER DEFAULT 0,
                billing_cycle_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create SessionCredits table
        print("➕ Creating SessionCredits table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                credits_purchased INTEGER DEFAULT 0,
                credits_used INTEGER DEFAULT 0,
                credits_remaining INTEGER DEFAULT 0,
                stripe_payment_intent_id VARCHAR(100),
                payment_amount_usd REAL DEFAULT 0.0,
                payment_status VARCHAR(20) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create AIUsageSession table
        print("➕ Creating AIUsageSession table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_type VARCHAR(50) NOT NULL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                model_used VARCHAR(50),
                subscription_used BOOLEAN DEFAULT 1,
                credit_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (credit_id) REFERENCES session_credits (id)
            )
        """)
        
        # Create indexes for better performance
        print("🔍 Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_credits_user_id ON session_credits(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_sessions_user_id ON ai_usage_sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_sessions_created_at ON ai_usage_sessions(created_at)")
        
        # Initialize subscription records for existing users
        print("👥 Initializing subscriptions for existing users...")
        cursor.execute("SELECT id FROM users")
        existing_users = cursor.fetchall()
        
        for user_id in existing_users:
            user_id = user_id[0]
            
            # Check if subscription already exists
            cursor.execute("SELECT id FROM user_subscriptions WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                # Create default subscription
                cursor.execute("""
                    INSERT INTO user_subscriptions (
                        user_id, subscription_type, monthly_fee_usd, 
                        sessions_per_month, billing_cycle_start, is_active
                    ) VALUES (?, 'subscription', 10.0, 600, ?, 1)
                """, (user_id, datetime.utcnow().isoformat()))
                print(f"✅ Created subscription for user {user_id}")
            
            # Check if session credits record exists
            cursor.execute("SELECT id FROM session_credits WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                # Create default session credits record
                cursor.execute("""
                    INSERT INTO session_credits (
                        user_id, credits_purchased, credits_used, credits_remaining
                    ) VALUES (?, 0, 0, 0)
                """, (user_id,))
                print(f"✅ Created session credits record for user {user_id}")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        print("\n✅ Subscription system migration completed successfully!")
        print(f"📊 Database now has {len(tables)} tables")
        
        # Show subscription status for existing users
        cursor.execute("SELECT COUNT(*) FROM user_subscriptions")
        total_subscriptions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM session_credits")
        total_credit_records = cursor.fetchone()[0]
        
        print(f"\n📈 Subscription Status:")
        print(f"   Total Subscriptions: {total_subscriptions}")
        print(f"   Total Credit Records: {total_credit_records}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Subscription System Migration Script")
    print("=" * 50)
    
    success = migrate_subscription_system()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("Users now have subscription and session credit tracking.")
        print("New users will automatically get default subscription settings.")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)
