#!/usr/bin/env python3
"""
Fix Orphaned Payment
Links existing Stripe payment to the correct user and grants premium access
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User, StripeCustomer, StripeSubscription
from services.stripe_service_v2 import get_stripe_service
import stripe
from datetime import datetime

def fix_orphaned_payment():
    """Find and link the orphaned payment to cassie.camacho@gmail.com"""
    
    with app.app_context():
        print("🔧 Fixing Orphaned Payment")
        print("==========================")
        
        # Get the user
        user = User.query.filter_by(email='cassie.camacho@gmail.com').first()
        if not user:
            print("❌ User not found")
            return False
            
        print(f"👤 Found user: {user.email} (ID: {user.id})")
        print(f"   Current premium access: {user.has_premium_access()}")
        print(f"   Current Stripe customer ID: {user.stripe_customer_id}")
        
        # Initialize Stripe service
        stripe_service = get_stripe_service()
        if not stripe_service.is_enabled():
            print("❌ Stripe not configured")
            return False
            
        print(f"✅ Stripe {stripe_service.mode} mode enabled")
        
        try:
            # Search for customers by email in Stripe
            print(f"\n🔍 Searching Stripe for customers with email: {user.email}")
            customers = stripe.Customer.list(email=user.email, limit=10)
            
            if not customers.data:
                print(f"❌ No Stripe customers found for {user.email}")
                return False
                
            print(f"✅ Found {len(customers.data)} Stripe customer(s)")
            
            for customer in customers.data:
                print(f"\n💳 Customer: {customer.id}")
                print(f"   Email: {customer.email}")
                print(f"   Created: {datetime.fromtimestamp(customer.created)}")
                
                # Get subscriptions for this customer
                subscriptions = stripe.Subscription.list(customer=customer.id, limit=10)
                
                if subscriptions.data:
                    print(f"   📋 Found {len(subscriptions.data)} subscription(s)")
                    
                    for subscription in subscriptions.data:
                        print(f"      Subscription: {subscription.id}")
                        print(f"      Status: {subscription.status}")
                        print(f"      Current period: {datetime.fromtimestamp(subscription.current_period_start)} - {datetime.fromtimestamp(subscription.current_period_end)}")
                        
                        # Link this customer to the user
                        print(f"\n🔗 Linking customer {customer.id} to user {user.id}")
                        
                        # Update user's stripe_customer_id
                        user.stripe_customer_id = customer.id
                        
                        # Create or update StripeCustomer record
                        stripe_customer_record = StripeCustomer.query.filter_by(user_id=user.id).first()
                        if not stripe_customer_record:
                            stripe_customer_record = StripeCustomer(
                                user_id=user.id,
                                stripe_customer_id=customer.id,
                                email=user.email
                            )
                            db.session.add(stripe_customer_record)
                            print("✅ Created new StripeCustomer record")
                        else:
                            stripe_customer_record.stripe_customer_id = customer.id
                            stripe_customer_record.updated_at = datetime.utcnow()
                            print("✅ Updated existing StripeCustomer record")
                        
                        # Create StripeSubscription record if active
                        if subscription.status in ['active', 'trialing']:
                            existing_stripe_sub = StripeSubscription.query.filter_by(
                                stripe_subscription_id=subscription.id
                            ).first()
                            
                            if not existing_stripe_sub:
                                price_id = subscription.items.data[0].price.id
                                
                                stripe_subscription_record = StripeSubscription(
                                    user_id=user.id,
                                    stripe_subscription_id=subscription.id,
                                    stripe_customer_id=customer.id,
                                    stripe_price_id=price_id,
                                    status=subscription.status,
                                    current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                                    current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                                    cancel_at_period_end=subscription.cancel_at_period_end
                                )
                                
                                db.session.add(stripe_subscription_record)
                                print("✅ Created StripeSubscription record")
                            else:
                                print("ℹ️ StripeSubscription record already exists")
                        
                        # Commit changes
                        db.session.commit()
                        
                        # Check premium access
                        print(f"\n🎉 Checking premium access...")
                        print(f"   Premium access now: {user.has_premium_access()}")
                        
                        return True
                else:
                    print("   📭 No subscriptions found for this customer")
            
            return False
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = fix_orphaned_payment()
    
    if success:
        print("\n🎉 Payment successfully linked!")
        print("\n📋 Next steps:")
        print("1. Configure webhooks in Stripe Dashboard")
        print("2. URL: https://kiwellness.org/webhook/stripe")
        print("3. Test with another payment to verify webhooks work")
    else:
        print("\n❌ Could not fix payment automatically")
        print("💡 You may need to manually check Stripe Dashboard for the payment")
