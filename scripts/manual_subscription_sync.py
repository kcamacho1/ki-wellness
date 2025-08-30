#!/usr/bin/env python3
"""
Manual subscription sync script
Finds recent Stripe subscriptions and syncs them to the database
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db, User, Subscription
from flask import Flask

def main():
    app = Flask(__name__)
    
    # Database configuration
    db_url = os.getenv('DATABASE_URL')
    if db_url and 'postgresql' in db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ki_wellness_dev.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        sync_recent_subscriptions()

def sync_recent_subscriptions():
    """Sync recent Stripe subscriptions to database"""
    try:
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        print("🔄 Syncing recent Stripe subscriptions...")
        
        # Get recent subscriptions (last 2 hours)
        import time
        two_hours_ago = int(time.time()) - (2 * 3600)
        
        subscriptions = stripe.Subscription.list(
            created={'gte': two_hours_ago},
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
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"   ⚠️ No user found with email: {email}")
                continue
            
            print(f"   👤 Found user: {user.username} (ID: {user.id})")
            
            # Check if subscription already exists
            existing_sub = Subscription.query.filter_by(
                stripe_subscription_id=stripe_sub.id
            ).first()
            
            if existing_sub:
                print(f"   ℹ️ Subscription already exists in database")
                continue
            
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
