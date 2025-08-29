#!/usr/bin/env python3
"""
Script to get or create the correct Stripe price ID for Ki Wellness Premium
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()

def main():
    # Get Stripe API key
    api_key = os.getenv('STRIPE_SECRET_KEY')
    if not api_key:
        print("❌ STRIPE_SECRET_KEY not found in environment variables")
        print("Please set your Stripe secret key in .env file")
        return

    stripe.api_key = api_key
    
    # Determine if using test or live mode
    mode = "TEST" if api_key.startswith('sk_test_') else "LIVE"
    print(f"🔑 Using Stripe {mode} mode")
    
    try:
        print("\n📋 Searching for existing Ki Wellness products...")
        
        # List all products
        products = stripe.Product.list(limit=100)
        ki_product = None
        
        for product in products.data:
            if 'ki wellness' in product.name.lower() or 'premium' in product.name.lower():
                print(f"Found product: {product.name} (ID: {product.id})")
                ki_product = product
                break
        
        if ki_product:
            print(f"\n💰 Searching for prices for product: {ki_product.name}")
            
            # List prices for this product
            prices = stripe.Price.list(product=ki_product.id, limit=100)
            
            for price in prices.data:
                amount = price.unit_amount / 100 if price.unit_amount else 0
                interval = price.recurring.interval if price.recurring else 'one-time'
                active = "✅" if price.active else "❌"
                
                print(f"{active} ${amount:.2f}/{interval} - ID: {price.id}")
                
                # If this looks like our $5/month premium plan
                if price.unit_amount == 500 and price.recurring and price.recurring.interval == 'month' and price.active:
                    print(f"\n🎯 FOUND YOUR PRICE ID: {price.id}")
                    print(f"Set this in your environment: STRIPE_PREMIUM_PRICE_ID={price.id}")
                    return
            
            print(f"\n⚠️ No $5/month price found. Creating one...")
            create_premium_price(ki_product.id)
            
        else:
            print(f"\n⚠️ No Ki Wellness product found. Creating one...")
            create_product_and_price()
            
    except stripe.error.AuthenticationError:
        print("❌ Stripe authentication failed. Check your API key.")
    except Exception as e:
        print(f"❌ Error: {e}")

def create_premium_price(product_id):
    """Create a $5/month premium price"""
    try:
        price = stripe.Price.create(
            product=product_id,
            unit_amount=500,  # $5.00 in cents
            currency='usd',
            recurring={'interval': 'month'},
            nickname='Ki Wellness Premium Monthly'
        )
        
        print(f"✅ Created new price: ${price.unit_amount/100:.2f}/month")
        print(f"🎯 YOUR PRICE ID: {price.id}")
        print(f"Set this in your environment: STRIPE_PREMIUM_PRICE_ID={price.id}")
        
    except Exception as e:
        print(f"❌ Error creating price: {e}")

def create_product_and_price():
    """Create both product and price"""
    try:
        # Create product
        product = stripe.Product.create(
            name="Ki Wellness Premium",
            description="Access to AI Health Coach and premium features",
            metadata={
                "app": "ki_wellness",
                "type": "subscription"
            }
        )
        
        print(f"✅ Created product: {product.name} (ID: {product.id})")
        
        # Create price
        create_premium_price(product.id)
        
    except Exception as e:
        print(f"❌ Error creating product: {e}")

if __name__ == "__main__":
    main()
