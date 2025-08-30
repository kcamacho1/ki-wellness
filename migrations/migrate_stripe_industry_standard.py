#!/usr/bin/env python3
"""
Industry-Standard Stripe Database Migration
Creates new tables for proper separation of concerns and webhook handling
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User, Subscription, StripeCustomer, StripeSubscription, StripeInvoice, WebhookEvent

def migrate_industry_standard_stripe():
    """Migrate to industry-standard Stripe database schema"""
    
    with app.app_context():
        print("🔄 Starting industry-standard Stripe migration...")
        
        try:
            # Create new tables
            print("📊 Creating new industry-standard tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            # Migrate existing subscription data
            print("🔄 Migrating existing subscription data...")
            migrate_existing_subscriptions()
            
            # Create customer records for users with stripe_customer_id
            print("👥 Creating customer mapping records...")
            migrate_customer_records()
            
            print("🎉 Migration completed successfully!")
            print("\n📋 Next steps:")
            print("1. Update your webhook endpoint in Stripe Dashboard to: /webhook/stripe")
            print("2. Configure webhook events: customer.subscription.created, customer.subscription.updated, etc.")
            print("3. Test with a small payment to ensure webhooks work")
            print("4. The old subscription table is preserved for backward compatibility")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

def migrate_existing_subscriptions():
    """Migrate data from legacy subscription table to new StripeSubscription table"""
    legacy_subscriptions = Subscription.query.filter(
        Subscription.stripe_subscription_id.isnot(None)
    ).all()
    
    migrated_count = 0
    
    for legacy_sub in legacy_subscriptions:
        # Check if already migrated
        existing = StripeSubscription.query.filter_by(
            stripe_subscription_id=legacy_sub.stripe_subscription_id
        ).first()
        
        if existing:
            print(f"⚠️ Subscription {legacy_sub.stripe_subscription_id} already exists in new table")
            continue
        
        # Create new StripeSubscription record
        new_subscription = StripeSubscription(
            user_id=legacy_sub.user_id,
            stripe_subscription_id=legacy_sub.stripe_subscription_id,
            stripe_customer_id=legacy_sub.stripe_customer_id,
            stripe_price_id='price_1S1Wjb6d7DUvK3X6cz3XoG97',  # Default price ID
            status=legacy_sub.status,
            current_period_start=legacy_sub.current_period_start,
            current_period_end=legacy_sub.current_period_end,
            cancel_at_period_end=legacy_sub.cancel_at_period_end,
            created_at=legacy_sub.created_at,
            updated_at=legacy_sub.updated_at
        )
        
        db.session.add(new_subscription)
        migrated_count += 1
        
        print(f"✅ Migrated subscription for user {legacy_sub.user_id}: {legacy_sub.stripe_subscription_id}")
    
    if migrated_count > 0:
        db.session.commit()
        print(f"📊 Migrated {migrated_count} subscriptions to new table")
    else:
        print("ℹ️ No subscriptions to migrate")

def migrate_customer_records():
    """Create StripeCustomer records for users with stripe_customer_id"""
    users_with_customers = User.query.filter(
        User.stripe_customer_id.isnot(None)
    ).all()
    
    migrated_count = 0
    
    for user in users_with_customers:
        # Check if already exists
        existing = StripeCustomer.query.filter_by(user_id=user.id).first()
        
        if existing:
            print(f"⚠️ Customer record for user {user.id} already exists")
            continue
        
        # Create new StripeCustomer record
        stripe_customer = StripeCustomer(
            user_id=user.id,
            stripe_customer_id=user.stripe_customer_id,
            email=user.email
        )
        
        db.session.add(stripe_customer)
        migrated_count += 1
        
        print(f"✅ Created customer record for user {user.id}: {user.stripe_customer_id}")
    
    if migrated_count > 0:
        db.session.commit()
        print(f"👥 Created {migrated_count} customer records")
    else:
        print("ℹ️ No customer records to create")

def verify_migration():
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    with app.app_context():
        # Count records in each table
        stripe_customers = StripeCustomer.query.count()
        stripe_subscriptions = StripeSubscription.query.count()
        webhook_events = WebhookEvent.query.count()
        legacy_subscriptions = Subscription.query.count()
        
        print(f"📊 Migration Results:")
        print(f"   StripeCustomer records: {stripe_customers}")
        print(f"   StripeSubscription records: {stripe_subscriptions}")
        print(f"   WebhookEvent records: {webhook_events}")
        print(f"   Legacy Subscription records: {legacy_subscriptions} (preserved)")
        
        # Check for users with premium access
        users_with_premium = 0
        for user in User.query.all():
            if user.has_premium_access():
                users_with_premium += 1
        
        print(f"   Users with premium access: {users_with_premium}")

def main():
    """Main migration function"""
    try:
        migrate_industry_standard_stripe()
        verify_migration()
        
        print("\n✅ Migration completed successfully!")
        print("\n🎯 Your Stripe integration is now industry-standard!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("💡 Please check the error and try again")
        return False

if __name__ == '__main__':
    print("🚀 Industry-Standard Stripe Migration")
    print("=====================================")
    
    # Check for auto-confirm environment variable (for production)
    auto_confirm = os.getenv('MIGRATION_AUTO_CONFIRM', '').lower() == 'true'
    
    if auto_confirm:
        print("✅ Auto-confirm enabled - proceeding with migration...")
        response = 'y'
    else:
        # Confirm before proceeding
        response = input("\nThis will create new Stripe tables and migrate existing data.\nContinue? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        sys.exit(0)
    
    success = main()
    sys.exit(0 if success else 1)
