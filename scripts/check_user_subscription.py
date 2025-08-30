#!/usr/bin/env python3
"""
Script to check a user's subscription status and manually activate if needed
"""

import os
import sys
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
        # Find test_user
        user = User.query.filter_by(username='test_user').first()
        if not user:
            print("❌ test_user not found")
            return
            
        print(f"👤 User: {user.username} (ID: {user.id})")
        print(f"📧 Email: {user.email}")
        print(f"🎭 Role: {user.role}")
        print(f"💳 Stripe Customer ID: {user.stripe_customer_id}")
        print(f"🏷️ Premium Access: {user.has_premium_access()}")
        
        # Check subscriptions
        subscriptions = Subscription.query.filter_by(user_id=user.id).all()
        if subscriptions:
            print(f"\n📋 Subscriptions ({len(subscriptions)}):")
            for sub in subscriptions:
                print(f"  - ID: {sub.id}")
                print(f"    Stripe Sub ID: {sub.stripe_subscription_id}")
                print(f"    Plan Type: {sub.plan_type}")
                print(f"    Status: {sub.status}")
                print(f"    Customer ID: {sub.stripe_customer_id}")
                print(f"    Period End: {sub.current_period_end}")
                print()
        else:
            print("\n⚠️ No subscriptions found in database")
            print("This means the webhook hasn't processed yet or wasn't received")
            
            # Check if we can find their Stripe customer
            if user.stripe_customer_id:
                print(f"\n🔍 Checking Stripe for customer: {user.stripe_customer_id}")
                check_stripe_subscription(user.stripe_customer_id)
            else:
                print("\n❌ No Stripe customer ID found")

def check_stripe_subscription(customer_id):
    """Check Stripe for active subscriptions"""
    try:
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # Get customer subscriptions
        subscriptions = stripe.Subscription.list(customer=customer_id)
        
        if subscriptions.data:
            print(f"✅ Found {len(subscriptions.data)} Stripe subscription(s):")
            for sub in subscriptions.data:
                print(f"  - Sub ID: {sub.id}")
                print(f"    Status: {sub.status}")
                print(f"    Created: {sub.created}")
                print(f"    Current Period End: {sub.current_period_end}")
                
                if sub.status == 'active':
                    print("🎯 ACTIVE SUBSCRIPTION FOUND - Need to sync to database!")
        else:
            print("❌ No Stripe subscriptions found")
            
    except Exception as e:
        print(f"❌ Error checking Stripe: {e}")

if __name__ == "__main__":
    main()
