#!/usr/bin/env python3
"""
Stripe Client for Ki Wellness Payment System
Handles payment processing, subscriptions, and customer management
"""

import os
import stripe
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Stripe configuration will be set when client is initialized
STRIPE_PUBLISHABLE_KEY = None

class StripeClient:
    def __init__(self):
        # Set Stripe API key
        self.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable is required")
        
        # Configure Stripe
        stripe.api_key = self.api_key
        
        # Set publishable key
        global STRIPE_PUBLISHABLE_KEY
        STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
        
        # Product and price IDs for subscription plans
        self.free_plan_price_id = None
        self.premium_plan_price_id = None
        
        # Don't initialize products during construction - do it lazily
        self._products_initialized = False
    
    def setup_products_and_prices(self):
        """Setup or retrieve existing products and prices for subscription plans"""
        if self._products_initialized:
            return
            
        try:
            # Ensure Stripe API key is set before proceeding
            if not stripe.api_key:
                stripe.api_key = self.api_key
            
            # Verify Stripe is properly configured before proceeding
            if not hasattr(stripe, 'api_key') or not stripe.api_key:
                print("⚠️ Stripe API key not configured")
                return
                
            # Get or create the main product
            products = stripe.Product.list(limit=100)
            ki_wellness_product = None
            
            for product in products.data:
                if product.name == "Ki Wellness Premium":
                    ki_wellness_product = product
                    break
            
            if not ki_wellness_product:
                ki_wellness_product = stripe.Product.create(
                    name="Ki Wellness Premium",
                    description="Access to AI Health Coach and premium features",
                    metadata={
                        "app": "ki_wellness",
                        "type": "subscription"
                    }
                )
            
            # Get or create the premium plan price ($5/month)
            prices = stripe.Price.list(
                product=ki_wellness_product.id,
                limit=100
            )
            
            premium_price = None
            for price in prices.data:
                if (price.unit_amount == 500 and  # $5.00 in cents
                    price.currency == 'usd' and
                    price.recurring and
                    price.recurring.interval == 'month'):
                    premium_price = price
                    break
            
            if not premium_price:
                premium_price = stripe.Price.create(
                    product=ki_wellness_product.id,
                    unit_amount=500,  # $5.00 in cents
                    currency='usd',
                    recurring={'interval': 'month'},
                    metadata={
                        "plan_type": "premium",
                        "features": "ai_coach,premium_content"
                    }
                )
            
            self.premium_plan_price_id = premium_price.id
            self._products_initialized = True
            
            print(f"✅ Stripe products and prices configured")
            print(f"   Premium Plan Price ID: {self.premium_plan_price_id}")
            
        except Exception as e:
            print(f"❌ Error setting up Stripe products: {e}")
            # Don't raise here - just log the error and continue
            print("⚠️ Stripe products not configured - payment features will be limited")
    
    def create_customer(self, email: str, name: str, user_id: int) -> Dict[str, Any]:
        """Create a new Stripe customer"""
        try:
            # Verify Stripe is configured
            if not hasattr(stripe, 'api_key') or not stripe.api_key:
                raise Exception("Stripe API key not configured")
                
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "user_id": str(user_id),
                    "app": "ki_wellness"
                }
            )
            return customer
        except Exception as e:
            print(f"❌ Error creating Stripe customer: {e}")
            raise
    
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a Stripe customer"""
        try:
            # Verify Stripe is configured
            if not hasattr(stripe, 'api_key') or not stripe.api_key:
                raise Exception("Stripe API key not configured")
                
            return stripe.Customer.retrieve(customer_id)
        except Exception as e:
            print(f"❌ Error retrieving Stripe customer: {e}")
            return None
    
    def create_checkout_session(
        self, 
        customer_id: str, 
        success_url: str, 
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription upgrade"""
        try:
            # Verify Stripe is configured
            if not hasattr(stripe, 'api_key') or not stripe.api_key:
                raise Exception("Stripe API key not configured")
                
            # Ensure products are set up
            self.setup_products_and_prices()
            
            if not self.premium_plan_price_id:
                raise Exception("Premium plan price not configured")
                
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': self.premium_plan_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "app": "ki_wellness",
                    "subscription_type": "premium_monthly"
                }
            )
            return checkout_session
        except Exception as e:
            print(f"❌ Error creating checkout session: {e}")
            raise
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a subscription"""
        try:
            # Verify Stripe is configured
            if not hasattr(stripe, 'api_key') or not stripe.api_key:
                raise Exception("Stripe API key not configured")
                
            return stripe.Subscription.retrieve(subscription_id)
        except Exception as e:
            print(f"❌ Error retrieving subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription at period end"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return subscription
        except Exception as e:
            print(f"❌ Error canceling subscription: {e}")
            raise
    
    def reactivate_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Reactivate a canceled subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return subscription
        except Exception as e:
            print(f"❌ Error reactivating subscription: {e}")
            raise
    
    def create_customer_portal_session(
        self, 
        customer_id: str, 
        return_url: str
    ) -> Dict[str, Any]:
        """Create a customer portal session for subscription management"""
        try:
            # Verify Stripe is configured
            if not hasattr(stripe, 'api_key') or not stripe.api_key:
                raise Exception("Stripe API key not configured")
                
            session = stripe.billing_portal.Session.create(
                customer_id=customer_id,
                return_url=return_url
            )
            return session
        except Exception as e:
            print(f"❌ Error creating customer portal session: {e}")
            raise
    
    def get_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get payment methods for a customer"""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            return payment_methods.data
        except Exception as e:
            print(f"❌ Error retrieving payment methods: {e}")
            return []
    
    def handle_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event_type = event_data.get('type')
            event_id = event_data.get('id')
            
            print(f"📨 Processing Stripe webhook: {event_type} (ID: {event_id})")
            
            if event_type == 'customer.subscription.created':
                return self.handle_subscription_created(event_data)
            elif event_type == 'customer.subscription.updated':
                return self.handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                return self.handle_subscription_deleted(event_data)
            elif event_type == 'invoice.payment_succeeded':
                return self.handle_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                return self.handle_payment_failed(event_data)
            elif event_type == 'payment_intent.succeeded':
                return self.handle_payment_intent_succeeded(event_data)
            elif event_type == 'payment_intent.payment_failed':
                return self.handle_payment_intent_failed(event_data)
            elif event_type == 'customer.created':
                return self.handle_customer_created(event_data)
            elif event_type == 'customer.updated':
                return self.handle_customer_updated(event_data)
            elif event_type == 'charge.succeeded':
                return self.handle_charge_succeeded(event_data)
            elif event_type == 'charge.failed':
                return self.handle_charge_failed(event_data)
            elif event_type == 'charge.refunded':
                return self.handle_charge_refunded(event_data)
            else:
                print(f"ℹ️ Unhandled webhook event type: {event_type}")
                return {"status": "ignored", "reason": "unhandled_event_type"}
                
        except Exception as e:
            print(f"❌ Error handling webhook event: {e}")
            return {"status": "error", "error": str(e)}
    
    def handle_subscription_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription creation webhook"""
        subscription = event_data.get('data', {}).get('object', {})
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        
        # Log revenue for analytics
        try:
            from analytics_service import analytics_service
            
            # Get subscription amount
            amount = subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('unit_amount', 0) / 100
            
            # Find user by customer ID
            from database import User
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            
            if user:
                analytics_service.log_revenue(
                    user_id=user.id,
                    revenue_type='subscription',
                    amount=amount,
                    stripe_subscription_id=subscription_id,
                    description=f'Premium subscription - {subscription.get("status", "active")}'
                )
        except Exception as e:
            print(f"⚠️ Could not log subscription revenue: {e}")
        
        print(f"✅ Subscription created: {subscription_id} for customer: {customer_id}")
        return {"status": "success", "action": "subscription_created"}
    
    def handle_subscription_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription update webhook"""
        subscription = event_data.get('data', {}).get('object', {})
        subscription_id = subscription.get('id')
        status = subscription.get('status')
        
        print(f"🔄 Subscription updated: {subscription_id} - Status: {status}")
        return {"status": "success", "action": "subscription_updated"}
    
    def handle_subscription_deleted(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription deletion webhook"""
        subscription = event_data.get('data', {}).get('object', {})
        subscription_id = subscription.get('id')
        
        print(f"🗑️ Subscription deleted: {subscription_id}")
        return {"status": "success", "action": "subscription_deleted"}
    
    def handle_payment_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook"""
        invoice = event_data.get('data', {}).get('object', {})
        subscription_id = invoice.get('subscription')
        amount_paid = invoice.get('amount_paid')
        
        print(f"💰 Payment succeeded: ${amount_paid/100:.2f} for subscription: {subscription_id}")
        return {"status": "success", "action": "payment_succeeded"}
    
    def handle_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook"""
        invoice = event_data.get('data', {}).get('object', {})
        subscription_id = invoice.get('subscription')
        
        print(f"❌ Payment failed for subscription: {subscription_id}")
        return {"status": "success", "action": "payment_failed"}
    
    def handle_payment_intent_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment intent webhook"""
        payment_intent = event_data.get('data', {}).get('object', {})
        customer_id = payment_intent.get('customer')
        amount = payment_intent.get('amount', 0) / 100
        
        print(f"💰 Payment intent succeeded: ${amount:.2f} for customer: {customer_id}")
        return {"status": "success", "action": "payment_intent_succeeded"}
    
    def handle_payment_intent_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment intent webhook"""
        payment_intent = event_data.get('data', {}).get('object', {})
        customer_id = payment_intent.get('customer')
        error_message = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
        
        print(f"❌ Payment intent failed for customer: {customer_id} - {error_message}")
        return {"status": "success", "action": "payment_intent_failed"}
    
    def handle_customer_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer creation webhook"""
        customer = event_data.get('data', {}).get('object', {})
        customer_id = customer.get('id')
        email = customer.get('email')
        
        print(f"✅ New customer created: {email} (ID: {customer_id})")
        return {"status": "success", "action": "customer_created"}
    
    def handle_customer_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer update webhook"""
        customer = event_data.get('data', {}).get('object', {})
        customer_id = customer.get('id')
        email = customer.get('email')
        
        print(f"🔄 Customer updated: {email} (ID: {customer_id})")
        return {"status": "success", "action": "customer_updated"}
    
    def handle_charge_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful charge webhook"""
        charge = event_data.get('data', {}).get('object', {})
        customer_id = charge.get('customer')
        amount = charge.get('amount', 0) / 100
        
        print(f"💰 Charge succeeded: ${amount:.2f} for customer: {customer_id}")
        return {"status": "success", "action": "charge_succeeded"}
    
    def handle_charge_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed charge webhook"""
        charge = event_data.get('data', {}).get('object', {})
        customer_id = charge.get('customer')
        failure_message = charge.get('failure_message', 'Unknown error')
        
        print(f"❌ Charge failed for customer: {customer_id} - {failure_message}")
        return {"status": "success", "action": "charge_failed"}
    
    def handle_charge_refunded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge refund webhook"""
        charge = event_data.get('data', {}).get('object', {})
        customer_id = charge.get('customer')
        refund_amount = charge.get('amount_refunded', 0) / 100
        
        print(f"💰 Charge refunded: ${refund_amount:.2f} for customer: {customer_id}")
        return {"status": "success", "action": "charge_refunded"}
    
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured"""
        # Basic configuration check - API key must be present
        basic_config = (
            self.api_key is not None and 
            self.api_key.strip() != '' and
            hasattr(stripe, 'api_key') and 
            stripe.api_key
        )
        
        # If basic config is not met, return False
        if not basic_config:
            return False
        
        # If products are initialized, we're fully configured
        if self._products_initialized:
            return True
        
        # If basic config is met but products aren't initialized yet,
        # we can still work (products will be initialized when needed)
        return True
    
    def is_payment_ready(self) -> bool:
        """Check if Stripe is ready to process payments"""
        return (
            self.is_configured() and 
            self._products_initialized and
            self.premium_plan_price_id is not None
        )

# Global Stripe client instance
stripe_client = None

def get_stripe_client() -> StripeClient:
    """Get or create the global Stripe client instance"""
    global stripe_client
    if stripe_client is None:
        try:
            stripe_client = StripeClient()
        except ValueError as e:
            print(f"❌ Stripe client initialization failed: {e}")
            print("⚠️ Stripe features will be disabled. Please check your STRIPE_SECRET_KEY environment variable.")
            return None
        except Exception as e:
            print(f"❌ Unexpected error initializing Stripe client: {e}")
            return None
    return stripe_client
