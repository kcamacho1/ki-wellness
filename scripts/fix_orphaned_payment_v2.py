#!/usr/bin/env python3
"""
Fix Orphaned Payment - Version 2
Fixed bug with subscription items access
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User, StripeCustomer, StripeSubscription
from services.stripe_service_v2 import get_stripe_service
import stripe
from datetime import datetime

def fix_cassie_payment():
    """Fix Cassie's specific payment with known details"""
    
    with app.app_context():
        print("🔧 Fixing Cassie's Payment (v2)")
        print("===============================")
        
        # Get the user
        user = User.query.filter_by(email='cassie.camacho@gmail.com').first()
        if not user:
            print("❌ User not found")
            return False
            
        print(f"👤 Found user: {user.email} (ID: {user.id})")
        
        # Known details from the output
        stripe_customer_id = "cus_SxqfuheBGbNitI"
        stripe_subscription_id = "sub_1S1uyX6d7DUvK3X64wh1l0Ez"
        
        try:
            print(f"\n🔗 Linking known customer {stripe_customer_id} to user {user.id}")
            
            # Update user's stripe_customer_id
            user.stripe_customer_id = stripe_customer_id
            
            # Create StripeCustomer record
            stripe_customer_record = StripeCustomer.query.filter_by(user_id=user.id).first()
            if not stripe_customer_record:
                stripe_customer_record = StripeCustomer(
                    user_id=user.id,
                    stripe_customer_id=stripe_customer_id,
                    email=user.email
                )
                db.session.add(stripe_customer_record)
                print("✅ Created new StripeCustomer record")
            else:
                stripe_customer_record.stripe_customer_id = stripe_customer_id
                stripe_customer_record.updated_at = datetime.utcnow()
                print("✅ Updated existing StripeCustomer record")
            
            # Get full subscription details from Stripe
            print(f"\n📋 Getting subscription details: {stripe_subscription_id}")
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            print(f"   Status: {subscription.status}")
            print(f"   Period: {datetime.fromtimestamp(subscription.current_period_start)} - {datetime.fromtimestamp(subscription.current_period_end)}")
            
            # Get price ID from subscription
            if subscription.items and len(subscription.items.data) > 0:
                price_id = subscription.items.data[0].price.id
                print(f"   Price ID: {price_id}")
            else:
                # Fallback to our known price ID
                price_id = "price_1S1Wjb6d7DUvK3X6cz3XoG97"  # Your premium price ID
                print(f"   Using fallback price ID: {price_id}")
            
            # Create StripeSubscription record
            existing_stripe_sub = StripeSubscription.query.filter_by(
                stripe_subscription_id=stripe_subscription_id
            ).first()
            
            if not existing_stripe_sub:
                stripe_subscription_record = StripeSubscription(
                    user_id=user.id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_customer_id=stripe_customer_id,
                    stripe_price_id=price_id,
                    status=subscription.status,
                    current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                    current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                    cancel_at_period_end=subscription.cancel_at_period_end if hasattr(subscription, 'cancel_at_period_end') else False
                )
                
                db.session.add(stripe_subscription_record)
                print("✅ Created StripeSubscription record")
            else:
                print("ℹ️ StripeSubscription record already exists")
            
            # Commit all changes
            db.session.commit()
            
            # Check premium access
            print(f"\n🎉 Checking premium access...")
            user_refreshed = User.query.get(user.id)  # Refresh from DB
            premium_access = user_refreshed.has_premium_access()
            print(f"   Premium access now: {premium_access}")
            
            if premium_access:
                print("\n🎉 SUCCESS! Payment successfully linked!")
                print("✅ Customer linked to user")
                print("✅ Subscription record created") 
                print("✅ Premium access granted")
                return True
            else:
                print("\n⚠️ Records created but premium access still False")
                print("💡 Check User.has_premium_access() method")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = fix_cassie_payment()
    
    if success:
        print("\n🎉 Payment fix completed successfully!")
    else:
        print("\n❌ Payment fix failed - check logs above")
