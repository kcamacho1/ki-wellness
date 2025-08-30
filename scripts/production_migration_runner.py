#!/usr/bin/env python3
"""
Production Migration Runner for Render
Runs the Stripe industry-standard migration on production
"""

import os
import sys

# Add the current directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_production_migration():
    """Run the migration in production environment"""
    try:
        print("🔄 Starting production migration...")
        
        # Import and run the migration
        from migrations.migrate_stripe_industry_standard import main as run_migration
        
        # Set environment to skip confirmation prompts
        os.environ['MIGRATION_AUTO_CONFIRM'] = 'true'
        
        print("✅ Running industry-standard Stripe migration...")
        result = run_migration()
        
        if result:
            print("🎉 Production migration completed successfully!")
            return True
        else:
            print("❌ Migration failed")
            return False
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Ki Wellness Production Migration")
    print("====================================")
    
    # Check if we're in production
    database_url = os.getenv('DATABASE_URL')
    if not database_url or 'postgresql' not in database_url:
        print("⚠️ Warning: This doesn't appear to be a production PostgreSQL environment")
        print(f"Database URL: {database_url[:50] if database_url else 'Not set'}...")
    
    success = run_production_migration()
    
    if success:
        print("\n✅ Ready for webhook configuration!")
        print("\n📋 Next steps:")
        print("1. Configure webhook in Stripe Dashboard:")
        print("   URL: https://kiwellness.org/webhook/stripe")
        print("2. Test with a small payment")
        sys.exit(0)
    else:
        print("\n❌ Migration failed - check logs above")
        sys.exit(1)
