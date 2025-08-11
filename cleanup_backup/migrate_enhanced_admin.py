#!/usr/bin/env python3
"""
Migration script for enhanced admin dashboard functionality.
This script adds the new models: SystemSettings, TokenUsage, and APICosts.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, db, SystemSettings, TokenUsage, APICosts
from sqlalchemy import text

def migrate_enhanced_admin():
    """Add new models for enhanced admin functionality"""
    with app.app_context():
        try:
            print("🔄 Starting enhanced admin dashboard migration...")
            
            # Check if new tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'system_settings' not in existing_tables:
                print("📝 Creating system_settings table...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE system_settings (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            key VARCHAR(100) UNIQUE NOT NULL,
                            value TEXT,
                            description TEXT,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_by INTEGER,
                            FOREIGN KEY (updated_by) REFERENCES users (id)
                        )
                    """))
                    conn.commit()
                print("✅ system_settings table created successfully!")
            else:
                print("ℹ️  system_settings table already exists")
            
            # Check if token_usage table exists
            if 'token_usage' not in existing_tables:
                print("📝 Creating token_usage table...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE token_usage (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            month VARCHAR(7) NOT NULL,
                            tokens_used INTEGER DEFAULT 0,
                            cost_usd REAL DEFAULT 0.0,
                            model_used VARCHAR(50),
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    """))
                    conn.commit()
                print("✅ token_usage table created successfully!")
            else:
                print("ℹ️  token_usage table already exists")
            
            # Check if api_costs table exists
            if 'api_costs' not in existing_tables:
                print("📝 Creating api_costs table...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE api_costs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            model_name VARCHAR(50) NOT NULL,
                            input_cost_per_1k REAL NOT NULL,
                            output_cost_per_1k REAL NOT NULL,
                            is_active BOOLEAN DEFAULT 1,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_by INTEGER,
                            FOREIGN KEY (updated_by) REFERENCES users (id)
                        )
                    """))
                    conn.commit()
                print("✅ api_costs table created successfully!")
            else:
                print("ℹ️  api_costs table already exists")
            
            # Initialize default system settings
            print("🔄 Initializing default system settings...")
            default_settings = [
                ('new_accounts_enabled', 'true', 'Allow new user registrations'),
                ('openai_api_enabled', 'true', 'Enable OpenAI API calls'),
                ('emergency_stop_active', 'false', 'Emergency stop for OpenAI API'),
                ('monthly_token_limit', '1000000', 'Monthly token usage limit')
            ]
            
            for key, value, description in default_settings:
                setting = SystemSettings.query.filter_by(key=key).first()
                if not setting:
                    setting = SystemSettings(key=key, value=value, description=description)
                    db.session.add(setting)
                    print(f"   ✅ Added setting: {key}")
                else:
                    print(f"   ℹ️  Setting already exists: {key}")
            
            # Initialize default API costs
            print("🔄 Initializing default API costs...")
            default_api_costs = [
                ('gpt-4', 0.03, 0.06),
                ('gpt-4-turbo', 0.01, 0.03),
                ('gpt-3.5-turbo', 0.0015, 0.002)
            ]
            
            for model_name, input_cost, output_cost in default_api_costs:
                api_cost = APICosts.query.filter_by(model_name=model_name).first()
                if not api_cost:
                    api_cost = APICosts(
                        model_name=model_name,
                        input_cost_per_1k=input_cost,
                        output_cost_per_1k=output_cost
                    )
                    db.session.add(api_cost)
                    print(f"   ✅ Added API cost: {model_name}")
                else:
                    print(f"   ℹ️  API cost already exists: {model_name}")
            
            db.session.commit()
            print("✅ Default settings and API costs initialized successfully!")
            
            # Verify the migration
            settings_count = SystemSettings.query.count()
            api_costs_count = APICosts.query.count()
            token_usage_count = TokenUsage.query.count()
            
            print(f"📊 Migration verification:")
            print(f"   System settings: {settings_count}")
            print(f"   API costs: {api_costs_count}")
            print(f"   Token usage records: {token_usage_count}")
            
            print("✅ Enhanced admin dashboard migration completed successfully!")
            return True
                
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Enhanced Admin Dashboard Migration Script")
    print("=" * 50)
    
    success = migrate_enhanced_admin()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now use the enhanced admin dashboard with:")
        print("• Emergency OpenAI controls")
        print("• Account creation management")
        print("• Token usage tracking")
        print("• Financial analytics")
        print("• API cost management")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
        sys.exit(1)
