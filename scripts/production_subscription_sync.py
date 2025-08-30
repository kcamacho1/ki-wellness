#!/usr/bin/env python3
"""
Production-safe subscription sync script
Works with the main Flask app context to avoid database connection issues
"""

import os
import sys
from datetime import datetime

def main():
    # Import within the production environment
    try:
        from app import app, db
        from database import User, Subscription
        import stripe
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        return

    # Set Stripe API key
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEY not found in environment")
        return

    print("🔄 Syncing recent Stripe subscriptions (production-safe)...")

    with app.app_context():
        try:
            # Get recent subscriptions (last 4 hours to be safe)
            import time
            four_hours_ago = int(time.time()) - (4 * 3600)
            
            subscriptions = stripe.Subscription.list(
                created={'gte': four_hours_ago},
                limit=20
            )
            
            print(f"📋 Found {len(subscriptions.data)} recent subscription(s)")
            
            for stripe_sub in subscriptions.data:
                print(f"\n🔍 Processing subscription: {stripe_sub.id}")
                print(f"   Customer: {stripe_sub.customer}")
                print(f"   Status: {stripe_sub.status}")
                
                # Get customer details
                customer = stripe.Customer.retrieve(stripe_sub.customer)
                email = customer.email
                
                print(f"   Email: {email}")
                
                # Check if subscription already exists in database
                existing_sub = Subscription.query.filter_by(
                    stripe_subscription_id=stripe_sub.id
                ).first()
                
                if existing_sub:
                    print(f"   ℹ️ Subscription already exists in database")
                    continue
                
                # Find user by email
                user = User.query.filter_by(email=email).first()
                if not user:
                    print(f"   ⚠️ No user found with email: {email}")
                    
                    # Try to find user by checking all users (in case email differs)
                    print("   🔍 Checking all users...")
                    all_users = User.query.all()
                    for u in all_users:
                        print(f"      - {u.username} ({u.email})")
                    
                    # For now, let's link to the first admin user if only one user exists
                    if len(all_users) == 1:
                        user = all_users[0]
                        print(f"   🎯 Linking to only user: {user.username} ({user.email})")
                    else:
                        print(f"   ❌ Multiple users found, skipping auto-link")
                        continue
                
                print(f"   👤 Found user: {user.username} (ID: {user.id})")
                
                # Link customer to user if not already linked
                if not user.stripe_customer_id:
                    user.stripe_customer_id = stripe_sub.customer
                    print(f"   🔗 Linked customer {stripe_sub.customer} to user {user.id}")
                
                # Create subscription record
                subscription = Subscription(
                    user_id=user.id,
                    stripe_subscription_id=stripe_sub.id,
                    stripe_customer_id=stripe_sub.customer,
                    plan_type='premium',
                    status=stripe_sub.status,
                    current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end) if stripe_sub.current_period_end else None
                )
                
                db.session.add(subscription)
                db.session.commit()
                
                print(f"   ✅ Created subscription record for user {user.username}")
                print(f"   🎉 User now has premium access: {user.has_premium_access()}")
                
            print(f"\n🎯 Sync complete!")
            
        except Exception as e:
            print(f"❌ Error syncing subscriptions: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
