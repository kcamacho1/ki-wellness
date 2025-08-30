#!/usr/bin/env python3
"""
Diagnose Payment Issue
Quick script to check user subscription status and payment history
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User, Subscription, StripeCustomer, StripeSubscription, WebhookEvent

def diagnose_payment_issue():
    """Diagnose why premium features aren't unlocked after payment"""
    
    with app.app_context():
        print("🔍 Ki Wellness Payment Diagnosis")
        print("=================================")
        
        # Check database setup
        print("\n📊 Database Status:")
        try:
            users_count = User.query.count()
            print(f"✅ User table accessible: {users_count} users")
        except Exception as e:
            print(f"❌ User table error: {e}")
            
        try:
            legacy_subs = Subscription.query.count()
            print(f"📋 Legacy subscriptions: {legacy_subs}")
        except Exception as e:
            print(f"❌ Legacy subscription table error: {e}")
            
        try:
            stripe_customers = StripeCustomer.query.count()
            print(f"🏢 Stripe customers: {stripe_customers}")
        except Exception as e:
            print(f"❌ StripeCustomer table missing: {e}")
            print("💡 Migration needed!")
            
        try:
            stripe_subs = StripeSubscription.query.count()
            print(f"💳 Stripe subscriptions: {stripe_subs}")
        except Exception as e:
            print(f"❌ StripeSubscription table missing: {e}")
            print("💡 Migration needed!")
            
        try:
            webhook_events = WebhookEvent.query.count()
            print(f"📨 Webhook events: {webhook_events}")
        except Exception as e:
            print(f"❌ WebhookEvent table missing: {e}")
            print("💡 Migration needed!")
        
        # Check specific user (you can modify this)
        print("\n👤 User Analysis:")
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        for user in recent_users:
            print(f"\n📧 {user.email} (ID: {user.id})")
            print(f"   Role: {user.role}")
            print(f"   Premium Access: {user.has_premium_access()}")
            print(f"   Stripe Customer ID: {user.stripe_customer_id}")
            
            # Check legacy subscriptions
            legacy_subs = user.subscriptions
            if legacy_subs:
                for sub in legacy_subs:
                    print(f"   📋 Legacy Sub: {sub.plan_type} - {sub.status}")
            
            # Check new subscriptions (if tables exist)
            try:
                stripe_subs = user.stripe_subscriptions
                if stripe_subs:
                    for sub in stripe_subs:
                        print(f"   💳 Stripe Sub: {sub.status} - {sub.current_period_end}")
                else:
                    print("   📭 No Stripe subscriptions found")
            except:
                print("   ❌ Stripe subscription table not available")
        
        # Environment check
        print(f"\n🌍 Environment:")
        database_url = os.getenv('DATABASE_URL', '')
        if 'postgresql' in database_url:
            print("✅ PostgreSQL database (production)")
        else:
            print("🔧 SQLite database (development)")
            
        stripe_key = os.getenv('STRIPE_SECRET_KEY', '')
        if stripe_key.startswith('sk_live_'):
            print("🔴 Stripe LIVE mode")
        elif stripe_key.startswith('sk_test_'):
            print("🟡 Stripe TEST mode")
        else:
            print("⚪ Stripe not configured")
            
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        if webhook_secret:
            print(f"🔗 Webhook secret configured: {webhook_secret[:20]}...")
        else:
            print("❌ No webhook secret configured")

if __name__ == '__main__':
    try:
        diagnose_payment_issue()
        
        print("\n💡 Recommendations:")
        print("1. If tables are missing: Run migration")
        print("2. If webhook events = 0: Configure webhooks in Stripe Dashboard")
        print("3. If user has no Stripe subscriptions: Webhooks aren't working")
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
