#!/usr/bin/env python3
"""
Industry-Standard Stripe Service for Ki Wellness
Follows separation of concerns and webhook-first architecture
"""

import os
import stripe
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from flask import current_app
from database import db, User, StripeCustomer, StripeSubscription, StripeInvoice, WebhookEvent

class StripeService:
    """Industry-standard Stripe service with environment auto-detection"""
    
    def __init__(self):
        self.api_key = None
        self.webhook_secret = None
        self.publishable_key = None
        self.mode = 'disabled'
        self.environment = 'disabled'
        self._initialize_from_config()
    
    def _initialize_from_config(self):
        """Initialize Stripe configuration from Flask app config"""
        if not current_app:
            return
            
        self.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        self.webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        self.publishable_key = current_app.config.get('STRIPE_PUBLISHABLE_KEY')
        self.mode = current_app.config.get('STRIPE_MODE', 'disabled')
        self.environment = current_app.config.get('STRIPE_ENV', 'disabled')
        
        if self.api_key:
            stripe.api_key = self.api_key
    
    def is_enabled(self) -> bool:
        """Check if Stripe is properly configured"""
        return self.mode != 'disabled' and bool(self.api_key)
    
    def is_live_mode(self) -> bool:
        """Check if running in live mode"""
        return self.mode == 'live'
    
    def is_test_mode(self) -> bool:
        """Check if running in test mode"""
        return self.mode == 'test'
    
    # Frontend-only methods (separation of concerns)
    def create_checkout_session(self, user_id: int, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """
        Create checkout session - Frontend responsibility only
        Backend never assumes success until webhook confirms
        """
        if not self.is_enabled():
            raise Exception("Stripe not configured")
        
        user = User.query.get(user_id)
        if not user:
            raise Exception("User not found")
        
        # Get or create price ID based on environment
        price_id = self._get_premium_price_id()
        
        try:
            session = stripe.checkout.Session.create(
                customer_email=user.email,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "app": "ki_wellness",
                    "user_id": str(user_id),
                    "email": user.email,
                    "environment": self.environment
                }
            )
            
            current_app.logger.info(f"✅ Checkout session created: {session.id} for user {user_id}")
            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url
            }
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"❌ Stripe error creating checkout: {e}")
            raise Exception(f"Payment system error: {e}")
    
    # Webhook handlers (backend source of truth)
    def handle_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """
        Industry-standard webhook handling with signature verification
        """
        if not self.webhook_secret:
            raise Exception("Webhook secret not configured")
        
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
        except ValueError:
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise Exception("Invalid signature")
        
        # Idempotency check
        if self._is_event_processed(event['id']):
            return {'status': 'already_processed', 'event_id': event['id']}
        
        # Process event
        result = self._process_webhook_event(event)
        
        # Record processing result
        self._record_webhook_processing(event['id'], event['type'], result)
        
        return result
    
    def _process_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook events with proper error handling"""
        event_type = event['type']
        event_data = event['data']['object']
        
        current_app.logger.info(f"📨 Processing webhook: {event_type}")
        
        try:
            if event_type == 'checkout.session.completed':
                return self._handle_checkout_completed(event_data)
            elif event_type == 'customer.subscription.created':
                return self._handle_subscription_created(event_data)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event_data)
            elif event_type == 'invoice.payment_succeeded':
                return self._handle_invoice_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_invoice_payment_failed(event_data)
            elif event_type == 'customer.created':
                return self._handle_customer_created(event_data)
            else:
                return {'status': 'ignored', 'reason': 'unhandled_event_type'}
                
        except Exception as e:
            current_app.logger.error(f"❌ Error processing webhook {event_type}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _handle_checkout_completed(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful checkout completion"""
        user_id = session_data['metadata'].get('user_id')
        customer_id = session_data['customer']
        
        if not user_id:
            return {'status': 'error', 'error': 'No user_id in metadata'}
        
        user = User.query.get(int(user_id))
        if not user:
            return {'status': 'error', 'error': 'User not found'}
        
        # Create or update customer mapping
        stripe_customer = StripeCustomer.query.filter_by(user_id=user.id).first()
        if not stripe_customer:
            stripe_customer = StripeCustomer(
                user_id=user.id,
                stripe_customer_id=customer_id,
                email=user.email
            )
            db.session.add(stripe_customer)
        else:
            stripe_customer.stripe_customer_id = customer_id
            stripe_customer.updated_at = datetime.utcnow()
        
        # Update user's stripe_customer_id for backward compatibility
        user.stripe_customer_id = customer_id
        
        db.session.commit()
        
        current_app.logger.info(f"✅ Checkout completed for user {user_id}, customer {customer_id}")
        return {'status': 'success', 'action': 'checkout_completed'}
    
    def _handle_customer_created(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer creation webhook"""
        customer_id = customer_data['id']
        email = customer_data['email']
        
        # Try to find user by email if not linked yet
        user = User.query.filter_by(email=email).first()
        if user and not user.stripe_customer_id:
            user.stripe_customer_id = customer_id
            
            # Also create StripeCustomer record
            stripe_customer = StripeCustomer.query.filter_by(user_id=user.id).first()
            if not stripe_customer:
                stripe_customer = StripeCustomer(
                    user_id=user.id,
                    stripe_customer_id=customer_id,
                    email=email
                )
                db.session.add(stripe_customer)
            
            db.session.commit()
            current_app.logger.info(f"✅ Customer {customer_id} linked to user {user.id}")
        
        return {'status': 'success', 'action': 'customer_created'}
    
    def _handle_subscription_created(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription creation - unlocks premium features"""
        subscription_id = subscription_data['id']
        customer_id = subscription_data['customer']
        price_id = subscription_data['items']['data'][0]['price']['id']
        
        # Find user by customer ID
        stripe_customer = StripeCustomer.query.filter_by(stripe_customer_id=customer_id).first()
        if not stripe_customer:
            # Fallback: find by user.stripe_customer_id for backward compatibility
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if not user:
                return {'status': 'error', 'error': 'Customer not found'}
        else:
            user = stripe_customer.user
        
        # Check if subscription already exists
        existing_subscription = StripeSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if existing_subscription:
            current_app.logger.info(f"ℹ️ Subscription {subscription_id} already exists")
            return {'status': 'success', 'action': 'subscription_already_exists'}
        
        # Create subscription record
        subscription = StripeSubscription(
            user_id=user.id,
            stripe_subscription_id=subscription_id,
            stripe_customer_id=customer_id,
            stripe_price_id=price_id,
            status=subscription_data['status'],
            current_period_start=datetime.fromtimestamp(subscription_data['current_period_start']),
            current_period_end=datetime.fromtimestamp(subscription_data['current_period_end']),
            trial_start=datetime.fromtimestamp(subscription_data['trial_start']) if subscription_data.get('trial_start') else None,
            trial_end=datetime.fromtimestamp(subscription_data['trial_end']) if subscription_data.get('trial_end') else None,
            cancel_at_period_end=subscription_data.get('cancel_at_period_end', False)
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        current_app.logger.info(f"🎉 Premium subscription activated for user {user.id}")
        return {'status': 'success', 'action': 'subscription_created', 'user_id': user.id}
    
    def _handle_subscription_updated(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates"""
        subscription_id = subscription_data['id']
        
        # Find existing subscription
        subscription = StripeSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if not subscription:
            current_app.logger.warning(f"⚠️ Subscription {subscription_id} not found for update")
            return {'status': 'error', 'error': 'Subscription not found'}
        
        # Update subscription fields
        subscription.status = subscription_data['status']
        subscription.current_period_start = datetime.fromtimestamp(subscription_data['current_period_start'])
        subscription.current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
        subscription.cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)
        
        if subscription_data.get('canceled_at'):
            subscription.canceled_at = datetime.fromtimestamp(subscription_data['canceled_at'])
        
        subscription.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"🔄 Subscription {subscription_id} updated - Status: {subscription_data['status']}")
        return {'status': 'success', 'action': 'subscription_updated'}
    
    def _handle_subscription_deleted(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription deletion"""
        subscription_id = subscription_data['id']
        
        # Find existing subscription
        subscription = StripeSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'canceled'
            subscription.canceled_at = datetime.utcnow()
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"🗑️ Subscription {subscription_id} marked as canceled")
        
        return {'status': 'success', 'action': 'subscription_deleted'}
    
    def _handle_invoice_payment_succeeded(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful invoice payment - confirms premium access"""
        invoice_id = invoice_data['id']
        customer_id = invoice_data['customer']
        subscription_id = invoice_data.get('subscription')
        
        # Find user
        stripe_customer = StripeCustomer.query.filter_by(stripe_customer_id=customer_id).first()
        if not stripe_customer:
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if not user:
                return {'status': 'error', 'error': 'Customer not found'}
        else:
            user = stripe_customer.user
        
        # Check if invoice already recorded
        existing_invoice = StripeInvoice.query.filter_by(stripe_invoice_id=invoice_id).first()
        if existing_invoice:
            current_app.logger.info(f"ℹ️ Invoice {invoice_id} already recorded")
            return {'status': 'success', 'action': 'invoice_already_recorded'}
        
        # Record invoice
        invoice = StripeInvoice(
            user_id=user.id,
            stripe_invoice_id=invoice_id,
            stripe_subscription_id=subscription_id,
            stripe_customer_id=customer_id,
            amount_paid=invoice_data['amount_paid'],
            amount_due=invoice_data['amount_due'],
            currency=invoice_data['currency'],
            status=invoice_data['status'],
            invoice_date=datetime.fromtimestamp(invoice_data['created']),
            due_date=datetime.fromtimestamp(invoice_data['due_date']) if invoice_data.get('due_date') else None,
            paid_at=datetime.fromtimestamp(invoice_data['status_transitions']['paid_at']) if invoice_data['status_transitions'].get('paid_at') else None
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        current_app.logger.info(f"💰 Invoice payment recorded: ${invoice_data['amount_paid']/100:.2f} for user {user.id}")
        return {'status': 'success', 'action': 'invoice_payment_recorded'}
    
    def _handle_invoice_payment_failed(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed invoice payment"""
        invoice_id = invoice_data['id']
        subscription_id = invoice_data.get('subscription')
        
        current_app.logger.warning(f"❌ Invoice payment failed: {invoice_id} for subscription: {subscription_id}")
        return {'status': 'success', 'action': 'invoice_payment_failed'}
    
    # Helper methods
    def _get_premium_price_id(self) -> str:
        """Get price ID based on environment"""
        if self.is_test_mode():
            return os.getenv('STRIPE_TEST_PREMIUM_PRICE_ID', 'price_1S1Wjb6d7DUvK3X6cz3XoG97')
        else:
            return os.getenv('STRIPE_LIVE_PREMIUM_PRICE_ID', 'price_1S1Wjb6d7DUvK3X6cz3XoG97')
    
    def _is_event_processed(self, event_id: str) -> bool:
        """Check if webhook event was already processed (idempotency)"""
        return WebhookEvent.query.filter_by(stripe_event_id=event_id, processed=True).first() is not None
    
    def _record_webhook_processing(self, event_id: str, event_type: str, result: Dict[str, Any]):
        """Record webhook processing for debugging and idempotency"""
        webhook_event = WebhookEvent.query.filter_by(stripe_event_id=event_id).first()
        if not webhook_event:
            webhook_event = WebhookEvent(
                stripe_event_id=event_id,
                event_type=event_type,
                processed=True,
                processing_result=json.dumps(result),
                processed_at=datetime.utcnow()
            )
            db.session.add(webhook_event)
        else:
            webhook_event.processed = True
            webhook_event.processing_result = json.dumps(result)
            webhook_event.processed_at = datetime.utcnow()
        
        db.session.commit()
    
    # Customer Portal and Management
    def create_customer_portal_session(self, user_id: int, return_url: str) -> Dict[str, Any]:
        """Create customer portal session for subscription management"""
        if not self.is_enabled():
            raise Exception("Stripe not configured")
        
        user = User.query.get(user_id)
        if not user or not user.stripe_customer_id:
            raise Exception("Customer not found")
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url
            )
            
            return {
                'success': True,
                'portal_url': session.url
            }
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"❌ Error creating portal session: {e}")
            raise Exception(f"Portal creation error: {e}")

# Global service instance
stripe_service = None

def get_stripe_service():
    """Get or create the global Stripe service instance"""
    global stripe_service
    if stripe_service is None:
        stripe_service = StripeService()
    return stripe_service
