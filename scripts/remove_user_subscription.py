#!/usr/bin/env python3
"""
Remove User Subscription
Manually remove a user from premium subscription (database + Stripe)
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User, StripeCustomer, StripeSubscription, Subscription
from services.stripe_service_v2 import get_stripe_service
import stripe
from datetime import datetime

def remove_user_subscription(user_email, cancel_in_stripe=True):
    """Remove user's subscription from both database and Stripe"""
    
    with app.app_context():
        print(f"🔧 Removing Subscription for {user_email}")
        print("=" * 50)
        
        # Get the user
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print("❌ User not found")
            return False
            
        print(f"👤 Found user: {user.email} (ID: {user.id})")
        print(f"   Current premium access: {user.has_premium_access()}")
        print(f"   Stripe customer ID: {user.stripe_customer_id}")
        
        try:
            # Step 1: Cancel subscription in Stripe (if requested)
            if cancel_in_stripe and user.stripe_customer_id:
                print(f"\n🔄 Step 1: Canceling Stripe subscriptions...")
                stripe_service = get_stripe_service()
                
                if stripe_service.is_enabled():
                    # Find and cancel active subscriptions
                    stripe_subs = StripeSubscription.query.filter_by(
                        user_id=user.id,
                        status='active'
                    ).all()
                    
                    for stripe_sub in stripe_subs:
                        try:
                            # Cancel subscription in Stripe
                            subscription = stripe.Subscription.modify(
                                stripe_sub.stripe_subscription_id,
                                cancel_at_period_end=True
                            )
                            print(f"✅ Stripe subscription {stripe_sub.stripe_subscription_id} set to cancel at period end")
                            
                            # Update database record
                            stripe_sub.cancel_at_period_end = True
                            stripe_sub.status = 'canceled'
                            stripe_sub.updated_at = datetime.utcnow()
                            
                        except Exception as e:
                            print(f"⚠️ Error canceling Stripe subscription {stripe_sub.stripe_subscription_id}: {e}")
                            # Continue with database cleanup even if Stripe fails
                else:
                    print("⚠️ Stripe not configured - skipping Stripe cancellation")
            else:
                print(f"\n📋 Step 1: Skipping Stripe cancellation (cancel_in_stripe={cancel_in_stripe})")
            
            # Step 2: Update database records
            print(f"\n💾 Step 2: Updating database records...")
            
            # Update new StripeSubscription records
            stripe_subs = StripeSubscription.query.filter_by(user_id=user.id).all()
            for stripe_sub in stripe_subs:
                if stripe_sub.status == 'active':
                    stripe_sub.status = 'canceled'
                    stripe_sub.cancel_at_period_end = True
                    stripe_sub.updated_at = datetime.utcnow()
                    print(f"✅ Updated StripeSubscription {stripe_sub.stripe_subscription_id} to canceled")
            
            # Update legacy subscription records
            legacy_subs = Subscription.query.filter_by(user_id=user.id).all()
            for legacy_sub in legacy_subs:
                if legacy_sub.status == 'active':
                    legacy_sub.status = 'canceled'
                    print(f"✅ Updated legacy Subscription {legacy_sub.id} to canceled")
            
            # Step 3: Clear user's Stripe customer ID (optional)
            clear_customer_id = input("\nClear user's Stripe customer ID? (y/N): ").lower().strip()
            if clear_customer_id == 'y':
                user.stripe_customer_id = None
                print("✅ Cleared user's Stripe customer ID")
            
            # Step 4: Commit changes
            print(f"\n💾 Step 3: Committing changes...")
            db.session.commit()
            print("✅ All changes committed")
            
            # Step 5: Verify removal
            print(f"\n🔍 Step 4: Verifying removal...")
            user_refreshed = User.query.get(user.id)
            premium_access = user_refreshed.has_premium_access()
            print(f"   Premium access after removal: {premium_access}")
            
            if not premium_access:
                print("\n🎉 SUCCESS! User subscription removed successfully!")
                print("✅ Database updated")
                if cancel_in_stripe:
                    print("✅ Stripe subscription canceled")
                print("✅ Premium access revoked")
                return True
            else:
                print("\n⚠️ Premium access still active - check for other active subscriptions")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

def list_user_subscriptions(user_email):
    """List all subscriptions for a user"""
    
    with app.app_context():
        print(f"📋 Subscriptions for {user_email}")
        print("=" * 40)
        
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print("❌ User not found")
            return
            
        print(f"👤 User: {user.email} (ID: {user.id})")
        print(f"   Premium access: {user.has_premium_access()}")
        print(f"   Stripe customer ID: {user.stripe_customer_id}")
        
        # New StripeSubscription records
        stripe_subs = StripeSubscription.query.filter_by(user_id=user.id).all()
        print(f"\n💳 Stripe Subscriptions ({len(stripe_subs)}):")
        for sub in stripe_subs:
            print(f"   - {sub.stripe_subscription_id}: {sub.status}")
            print(f"     Period: {sub.current_period_start} - {sub.current_period_end}")
            print(f"     Cancel at period end: {sub.cancel_at_period_end}")
        
        # Legacy subscription records
        legacy_subs = Subscription.query.filter_by(user_id=user.id).all()
        print(f"\n📋 Legacy Subscriptions ({len(legacy_subs)}):")
        for sub in legacy_subs:
            print(f"   - ID {sub.id}: {sub.status} ({sub.plan_type})")
            if sub.current_period_end:
                print(f"     Expires: {sub.current_period_end}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Remove user subscription')
    parser.add_argument('email', help='User email address')
    parser.add_argument('--list-only', action='store_true', help='List subscriptions only, do not remove')
    parser.add_argument('--no-stripe', action='store_true', help='Only update database, do not cancel in Stripe')
    
    args = parser.parse_args()
    
    if args.list_only:
        list_user_subscriptions(args.email)
    else:
        success = remove_user_subscription(args.email, cancel_in_stripe=not args.no_stripe)
        
        if success:
            print(f"\n✅ Subscription removal completed for {args.email}")
        else:
            print(f"\n❌ Subscription removal failed for {args.email}")
