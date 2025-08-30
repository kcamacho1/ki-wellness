#!/usr/bin/env python3
"""
Link a Stripe subscription to a specific user
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
    # Get command line arguments
    if len(sys.argv) != 3:
        print("Usage: python link_subscription_to_user.py <username_or_email> <stripe_subscription_id>")
        print("\nRecent subscription: sub_1S1a1M6d7DUvK3X60abVCUP9")
        return
    
    user_identifier = sys.argv[1]
    subscription_id = sys.argv[2]
    
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
        link_subscription(user_identifier, subscription_id)

def link_subscription(user_identifier, subscription_id):
    """Link subscription to user"""
    try:
        # Find user by username or email
        user = User.query.filter(
            (User.username == user_identifier) | (User.email == user_identifier)
        ).first()
        
        if not user:
            print(f"❌ User not found: {user_identifier}")
            return
        
        print(f"👤 Found user: {user.username} ({user.email})")
        
        # Get Stripe subscription details
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        customer = stripe.Customer.retrieve(stripe_sub.customer)
        
        print(f"💳 Stripe subscription: {subscription_id}")
        print(f"   Status: {stripe_sub.status}")
        print(f"   Customer: {customer.email} ({stripe_sub.customer})")
        
        # Link customer to user
        if not user.stripe_customer_id:
            user.stripe_customer_id = stripe_sub.customer
            print(f"🔗 Linked customer {stripe_sub.customer} to user")
        
        # Check if subscription already exists
        existing_sub = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if existing_sub:
            print(f"⚠️ Subscription already exists in database")
            return
        
        # Create subscription record
        subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id=subscription_id,
            stripe_customer_id=stripe_sub.customer,
            plan_type='premium',
            status=stripe_sub.status,
            current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end) if stripe_sub.current_period_end else None
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        print(f"✅ Successfully linked subscription to {user.username}")
        print(f"🎉 Premium access activated: {user.has_premium_access()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
