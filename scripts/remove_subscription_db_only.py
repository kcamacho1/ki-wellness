#!/usr/bin/env python3
"""
Remove Subscription (Database Only)
Quick script to remove premium access from database without touching Stripe
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User, StripeCustomer, StripeSubscription, Subscription
from datetime import datetime

def remove_subscription_db_only(user_email):
    """Remove user's subscription from database only"""
    
    with app.app_context():
        print(f"🔧 Database-Only Subscription Removal")
        print(f"User: {user_email}")
        print("=" * 40)
        
        # Get the user
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print("❌ User not found")
            return False
            
        print(f"👤 Found user: {user.email} (ID: {user.id})")
        print(f"   Current premium access: {user.has_premium_access()}")
        
        try:
            # Update all active StripeSubscription records
            stripe_subs = StripeSubscription.query.filter_by(
                user_id=user.id,
                status='active'
            ).all()
            
            for stripe_sub in stripe_subs:
                stripe_sub.status = 'canceled'
                stripe_sub.cancel_at_period_end = True
                stripe_sub.updated_at = datetime.utcnow()
                print(f"✅ Canceled StripeSubscription {stripe_sub.stripe_subscription_id}")
            
            # Update all active legacy subscription records
            legacy_subs = Subscription.query.filter_by(
                user_id=user.id,
                status='active'
            ).all()
            
            for legacy_sub in legacy_subs:
                legacy_sub.status = 'canceled'
                print(f"✅ Canceled legacy Subscription {legacy_sub.id}")
            
            # Commit changes
            db.session.commit()
            print("✅ Database changes committed")
            
            # Verify removal
            user_refreshed = User.query.get(user.id)
            premium_access = user_refreshed.has_premium_access()
            print(f"\n🔍 Premium access after removal: {premium_access}")
            
            if not premium_access:
                print("\n🎉 SUCCESS! Premium access revoked in database")
                return True
            else:
                print("\n⚠️ Premium access still active - check for other subscriptions")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python remove_subscription_db_only.py <user_email>")
        print("Example: python remove_subscription_db_only.py user@example.com")
        sys.exit(1)
    
    user_email = sys.argv[1]
    success = remove_subscription_db_only(user_email)
    
    if success:
        print(f"\n✅ Database subscription removal completed for {user_email}")
        print("💡 Note: This only updates the database. Stripe subscription remains active.")
    else:
        print(f"\n❌ Database subscription removal failed for {user_email}")
