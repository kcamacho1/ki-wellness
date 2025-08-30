#!/usr/bin/env python3
"""
Simple Cassie Payment Fix
Creates database records without needing Stripe API calls
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User, StripeCustomer, StripeSubscription
from datetime import datetime

def fix_cassie_simple():
    """Fix Cassie's payment with known data - no API calls needed"""
    
    with app.app_context():
        print("🔧 Simple Cassie Payment Fix")
        print("============================")
        
        # Get the user
        user = User.query.filter_by(email='cassie.camacho@gmail.com').first()
        if not user:
            print("❌ User not found")
            return False
            
        print(f"👤 Found user: {user.email} (ID: {user.id})")
        print(f"   Current premium access: {user.has_premium_access()}")
        
        # Known details from previous output
        stripe_customer_id = "cus_SxqfuheBGbNitI"
        stripe_subscription_id = "sub_1S1uyX6d7DUvK3X64wh1l0Ez"
        
        try:
            # 1. Update user's stripe_customer_id
            print(f"\n🔗 Step 1: Linking customer {stripe_customer_id} to user")
            user.stripe_customer_id = stripe_customer_id
            
            # 2. Create/update StripeCustomer record (this was already done)
            stripe_customer_record = StripeCustomer.query.filter_by(user_id=user.id).first()
            if stripe_customer_record:
                print("✅ StripeCustomer record already exists")
            else:
                stripe_customer_record = StripeCustomer(
                    user_id=user.id,
                    stripe_customer_id=stripe_customer_id,
                    email=user.email
                )
                db.session.add(stripe_customer_record)
                print("✅ Created StripeCustomer record")
            
            # 3. Create StripeSubscription record with known data
            print(f"\n📋 Step 2: Creating subscription record {stripe_subscription_id}")
            
            existing_stripe_sub = StripeSubscription.query.filter_by(
                stripe_subscription_id=stripe_subscription_id
            ).first()
            
            if not existing_stripe_sub:
                # Use known subscription period: 2025-08-30 to 2025-09-30
                period_start = datetime(2025, 8, 30, 20, 2, 13)
                period_end = datetime(2025, 9, 30, 20, 2, 13)
                
                stripe_subscription_record = StripeSubscription(
                    user_id=user.id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_customer_id=stripe_customer_id,
                    stripe_price_id="price_1S1Wjb6d7DUvK3X6cz3XoG97",  # Your premium price
                    status="active",
                    current_period_start=period_start,
                    current_period_end=period_end,
                    cancel_at_period_end=False
                )
                
                db.session.add(stripe_subscription_record)
                print("✅ Created StripeSubscription record")
                print(f"   Period: {period_start} - {period_end}")
            else:
                print("ℹ️ StripeSubscription record already exists")
            
            # 4. Commit all changes
            print(f"\n💾 Step 3: Saving to database")
            db.session.commit()
            print("✅ All changes committed")
            
            # 5. Test premium access
            print(f"\n🎉 Step 4: Testing premium access")
            user_refreshed = User.query.get(user.id)
            premium_access = user_refreshed.has_premium_access()
            print(f"   Premium access: {premium_access}")
            print(f"   Stripe customer ID: {user_refreshed.stripe_customer_id}")
            
            # Show subscription details
            stripe_subs = user_refreshed.stripe_subscriptions
            print(f"   Stripe subscriptions: {len(stripe_subs)}")
            for sub in stripe_subs:
                print(f"     - {sub.stripe_subscription_id}: {sub.status} until {sub.current_period_end}")
            
            if premium_access:
                print("\n🎉 SUCCESS! Cassie now has premium access!")
                return True
            else:
                print("\n⚠️ Premium access still False - check User.has_premium_access() logic")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = fix_cassie_simple()
    
    if success:
        print("\n🎉 Cassie's payment successfully fixed!")
        print("✅ Customer linked")
        print("✅ Subscription created") 
        print("✅ Premium access granted")
    else:
        print("\n❌ Fix failed - check logs above")
