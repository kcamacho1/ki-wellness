"""
Payment and subscription routes
Handles Stripe checkout, customer portal, subscription status, and payment webhooks
"""
from flask import Blueprint, request, jsonify, redirect, url_for, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime
import stripe
import json
import os

# Import database models
from database import db, User, Subscription, PaymentSession

# Import services
from services.stripe_client import get_stripe_client
from services.analytics_service import analytics_service

# Import utilities
from utils.decorators import premium_required

# Create blueprint
payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/api/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        stripe_client = get_stripe_client()
        if not stripe_client:
            return jsonify({
                'success': False, 
                'error': 'Payment system not ready. Please check your Stripe configuration.',
                'details': 'The payment system is initializing. Please try again in a moment.'
            }), 503
        
        # Create or get customer (simplified approach with webhooks)
        customer_id = current_user.stripe_customer_id
        
        if not customer_id:
            try:
                # Create customer only if we need to - let webhooks handle the linking
                customer = stripe_client.create_customer(
                    email=current_user.email,
                    name=current_user.name or current_user.username,
                    user_id=current_user.id
                )
                if not customer or not hasattr(customer, 'id'):
                    raise Exception("Failed to create Stripe customer - invalid response")
                
                customer_id = customer.id
                # Don't save to database yet - let the webhook handle it for consistency
                current_app.logger.info(f"Created Stripe customer {customer_id} for user {current_user.id}")
                
            except Exception as e:
                current_app.logger.error(f"Failed to create Stripe customer for user {current_user.id}: {e}")
                
                # Fallback: Try to create checkout session without customer
                # Stripe will create customer automatically during checkout
                customer_id = None
                current_app.logger.info(f"Will create checkout session without pre-existing customer for user {current_user.id}")
        
        # If we still don't have a customer_id, let Stripe create one during checkout
        if not customer_id:
            # Create checkout session without customer - Stripe will create customer
            try:
                checkout_session = stripe_client.create_checkout_session_without_customer(
                    customer_email=current_user.email,
                    success_url=url_for('payments.payment_success', _external=True),
                    cancel_url=url_for('dashboard.profile', _external=True),
                    user_id=current_user.id
                )
            except Exception as e:
                current_app.logger.error(f"Failed to create checkout session for user {current_user.id}: {e}")
                return jsonify({
                    'success': False, 
                    'error': 'Failed to create payment session. Please try again later.',
                    'details': 'Checkout session creation failed'
                }), 500
        else:
            # Create checkout session with existing customer
            try:
                checkout_session = stripe_client.create_checkout_session(
                    customer_id=customer_id,
                    success_url=url_for('payments.payment_success', _external=True),
                    cancel_url=url_for('dashboard.profile', _external=True)
                )
            except Exception as e:
                current_app.logger.error(f"Failed to create checkout session for user {current_user.id}: {e}")
                return jsonify({
                    'success': False, 
                    'error': 'Failed to create payment session. Please try again later.',
                    'details': 'Checkout session creation failed'
                }), 500
        
        # At this point, checkout_session should be created already
        # Just validate it exists
        
        if checkout_session:
            # Store payment session in database
            payment_session = PaymentSession(
                user_id=current_user.id,
                stripe_session_id=checkout_session.id,
                status='pending'
            )
            db.session.add(payment_session)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'session_id': checkout_session.id,
                'checkout_url': checkout_session.url
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create payment session'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error creating checkout session: {e}")
        return jsonify({'success': False, 'error': 'Failed to create payment session'}), 500


@payments_bp.route('/api/customer-portal', methods=['POST'])
@login_required
def customer_portal():
    """Create Stripe customer portal session"""
    try:
        stripe_client = get_stripe_client()
        if not stripe_client:
            return jsonify({
                'success': False, 
                'error': 'Payment system not ready. Please check your Stripe configuration.',
                'details': 'The payment system is initializing. Please try again in a moment.'
            }), 503
        
        return_url = url_for('dashboard.profile', _external=True)
        
        session = stripe_client.create_customer_portal_session(
            customer_id=current_user.stripe_customer_id,
            return_url=return_url
        )
        
        if session:
            return jsonify({
                'success': True,
                'portal_url': session.url
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create customer portal session'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error creating customer portal session: {e}")
        return jsonify({'success': False, 'error': 'Failed to create customer portal session'}), 500


@payments_bp.route('/api/subscription-status')
@login_required
def subscription_status():
    """Get current user's subscription status"""
    try:
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        # Check if user has premium access (includes admin/ff users)
        has_premium = current_user.has_premium_access()
        
        if subscription:
            return jsonify({
                'success': True,
                'subscription': {
                    'id': subscription.id,
                    'status': subscription.status,
                    'stripe_subscription_id': subscription.stripe_subscription_id,
                    'plan_name': subscription.plan_name,
                    'is_premium': subscription.is_premium,
                    'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                    'created_at': subscription.created_at.isoformat() if subscription.created_at else None
                },
                'is_premium': has_premium
            })
        else:
            return jsonify({
                'success': True,
                'subscription': None,
                'is_premium': has_premium
            })
            
    except Exception as e:
        current_app.logger.error(f"Error getting subscription status: {e}")
        return jsonify({'success': False, 'error': 'Failed to get subscription status'}), 500


@payments_bp.route('/api/log-health-coaching-revenue', methods=['POST'])
@login_required
def log_health_coaching_revenue():
    """Log health coaching session revenue"""
    try:
        data = request.get_json()
        
        # Validate required fields
        amount = data.get('amount')  # Amount in cents
        session_type = data.get('session_type', '30min_session')
        
        if not amount:
            return jsonify({'success': False, 'error': 'Amount is required'}), 400
        
        # Log the revenue with analytics service
        revenue_data = {
            'user_id': current_user.id,
            'amount_cents': int(amount),
            'session_type': session_type,
            'service_type': 'health_coaching',
            'timestamp': datetime.utcnow()
        }
        
        # Record revenue
        analytics_service.record_revenue(
            user_id=current_user.id,
            amount=int(amount) / 100,  # Convert cents to dollars
            revenue_type='health_coaching'
        )
        
        return jsonify({
            'success': True,
            'message': f'Logged health coaching revenue: ${int(amount) / 100:.2f}'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error logging health coaching revenue: {e}")
        return jsonify({'success': False, 'error': 'Failed to log revenue'}), 500


@payments_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        # Get webhook secret from environment
        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET') or os.getenv('STRIPE_WEBHOOK_SECRET')
        if not webhook_secret:
            current_app.logger.error("STRIPE_WEBHOOK_SECRET not configured")
            return jsonify({'error': 'Webhook secret not configured'}), 400
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError:
            current_app.logger.error("Invalid payload in webhook")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            current_app.logger.error("Invalid signature in webhook")
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Get Stripe client
        stripe_client = get_stripe_client()
        if not stripe_client:
            current_app.logger.warning("Stripe client not configured, skipping webhook processing")
            return jsonify({'status': 'ignored', 'reason': 'stripe_not_configured'}), 200
        
        # Handle the event
        result = stripe_client.handle_webhook_event(event)
        
        # Update local database based on webhook events
        event_type = event.get('type')
        event_data = event.get('data', {}).get('object', {})
        
        current_app.logger.info(f"📨 Processing webhook: {event_type}")
        
        if event_type == 'customer.subscription.created':
            handle_subscription_created_webhook(event_data)
        elif event_type == 'customer.subscription.updated':
            handle_subscription_updated_webhook(event_data)
        elif event_type == 'customer.subscription.deleted':
            handle_subscription_deleted_webhook(event_data)
        elif event_type == 'invoice.payment_succeeded':
            handle_invoice_payment_succeeded_webhook(event_data)
        elif event_type == 'invoice.payment_failed':
            handle_invoice_payment_failed_webhook(event_data)
        elif event_type == 'payment_intent.succeeded':
            handle_payment_intent_succeeded_webhook(event_data)
        elif event_type == 'payment_intent.payment_failed':
            handle_payment_intent_failed_webhook(event_data)
        elif event_type == 'customer.created':
            handle_customer_created_webhook(event_data)
        elif event_type == 'customer.updated':
            handle_customer_updated_webhook(event_data)
        elif event_type == 'charge.succeeded':
            handle_charge_succeeded_webhook(event_data)
        elif event_type == 'charge.failed':
            handle_charge_failed_webhook(event_data)
        elif event_type == 'charge.refunded':
            handle_charge_refunded_webhook(event_data)
        else:
            current_app.logger.info(f"ℹ️ Unhandled webhook event: {event_type}")
        
        return jsonify({'success': True, 'result': result}), 200
        
    except Exception as e:
        current_app.logger.error(f"❌ Error handling webhook: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def handle_subscription_created_webhook(subscription_data):
    """Handle subscription creation webhook"""
    try:
        customer_id = subscription_data.get('customer')
        subscription_id = subscription_data.get('id')
        status = subscription_data.get('status')
        current_period_end = subscription_data.get('current_period_end')
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            current_app.logger.warning(f"User not found for customer_id: {customer_id}")
            return
        
        # Create or update subscription
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            stripe_subscription_id=subscription_id
        ).first()
        
        if not subscription:
            subscription = Subscription(
                user_id=user.id,
                stripe_subscription_id=subscription_id,
                status=status,
                plan_name='premium',
                is_premium=True,
                current_period_end=datetime.fromtimestamp(current_period_end) if current_period_end else None,
                created_at=datetime.utcnow()
            )
            db.session.add(subscription)
        else:
            subscription.status = status
            subscription.is_premium = True
            subscription.current_period_end = datetime.fromtimestamp(current_period_end) if current_period_end else None
        
        db.session.commit()
        current_app.logger.info(f"✅ Subscription created for user {user.id}: {subscription_id}")
        
        # Log revenue
        try:
            items = subscription_data.get('items', {}).get('data', [])
            if items:
                amount = items[0].get('price', {}).get('unit_amount', 0) / 100
                analytics_service.record_revenue(
                    user_id=user.id,
                    amount=amount,
                    revenue_type='subscription'
                )
        except Exception as e:
            current_app.logger.warning(f"Could not log subscription revenue: {e}")
            
    except Exception as e:
        current_app.logger.error(f"Error handling subscription created webhook: {e}")
        db.session.rollback()


def handle_subscription_updated_webhook(subscription_data):
    """Handle subscription update webhook"""
    try:
        customer_id = subscription_data.get('customer')
        subscription_id = subscription_data.get('id')
        status = subscription_data.get('status')
        current_period_end = subscription_data.get('current_period_end')
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            current_app.logger.warning(f"User not found for customer_id: {customer_id}")
            return
        
        # Update subscription
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = status
            subscription.is_premium = status == 'active'
            subscription.current_period_end = datetime.fromtimestamp(current_period_end) if current_period_end else None
            db.session.commit()
            current_app.logger.info(f"✅ Subscription updated for user {user.id}: {subscription_id} - {status}")
        else:
            current_app.logger.warning(f"Subscription not found for user {user.id}: {subscription_id}")
            
    except Exception as e:
        current_app.logger.error(f"Error handling subscription updated webhook: {e}")
        db.session.rollback()


def handle_subscription_deleted_webhook(subscription_data):
    """Handle subscription deletion webhook"""
    try:
        customer_id = subscription_data.get('customer')
        subscription_id = subscription_data.get('id')
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            current_app.logger.warning(f"User not found for customer_id: {customer_id}")
            return
        
        # Update subscription status
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'cancelled'
            subscription.is_premium = False
            db.session.commit()
            current_app.logger.info(f"✅ Subscription cancelled for user {user.id}: {subscription_id}")
        else:
            current_app.logger.warning(f"Subscription not found for user {user.id}: {subscription_id}")
            
    except Exception as e:
        current_app.logger.error(f"Error handling subscription deleted webhook: {e}")
        db.session.rollback()


def handle_invoice_payment_succeeded_webhook(invoice_data):
    """Handle successful invoice payment webhook"""
    try:
        customer_id = invoice_data.get('customer')
        subscription_id = invoice_data.get('subscription')
        amount_paid = invoice_data.get('amount_paid', 0) / 100
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            current_app.logger.warning(f"User not found for customer_id: {customer_id}")
            return
        
        # Log revenue
        analytics_service.record_revenue(
            user_id=user.id,
            amount=amount_paid,
            revenue_type='subscription'
        )
        
        current_app.logger.info(f"💰 Payment succeeded: ${amount_paid:.2f} for user {user.id}")
        
    except Exception as e:
        current_app.logger.error(f"Error handling invoice payment succeeded webhook: {e}")


def handle_invoice_payment_failed_webhook(invoice_data):
    """Handle failed invoice payment webhook"""
    try:
        customer_id = invoice_data.get('customer')
        subscription_id = invoice_data.get('subscription')
        
        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            current_app.logger.warning(f"User not found for customer_id: {customer_id}")
            return
        
        current_app.logger.warning(f"❌ Payment failed for user {user.id}, subscription: {subscription_id}")
        
    except Exception as e:
        current_app.logger.error(f"Error handling invoice payment failed webhook: {e}")


def handle_payment_intent_succeeded_webhook(payment_intent_data):
    """Handle successful payment intent webhook"""
    try:
        customer_id = payment_intent_data.get('customer')
        amount = payment_intent_data.get('amount', 0) / 100
        
        if customer_id:
            # Find user by Stripe customer ID
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                current_app.logger.info(f"💰 Payment intent succeeded: ${amount:.2f} for user {user.id}")
            
    except Exception as e:
        current_app.logger.error(f"Error handling payment intent succeeded webhook: {e}")


def handle_payment_intent_failed_webhook(payment_intent_data):
    """Handle failed payment intent webhook"""
    try:
        customer_id = payment_intent_data.get('customer')
        
        if customer_id:
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                current_app.logger.warning(f"❌ Payment intent failed for user {user.id}")
            
    except Exception as e:
        current_app.logger.error(f"Error handling payment intent failed webhook: {e}")


def handle_customer_created_webhook(customer_data):
    """Handle customer creation webhook"""
    try:
        customer_id = customer_data.get('id')
        email = customer_data.get('email')
        user_id = customer_data.get('metadata', {}).get('user_id')
        
        if user_id:
            user = User.query.get(int(user_id))
            if user and not user.stripe_customer_id:
                user.stripe_customer_id = customer_id
                db.session.commit()
                current_app.logger.info(f"✅ Customer created and linked: {email} (ID: {customer_id})")
        
    except Exception as e:
        current_app.logger.error(f"Error handling customer created webhook: {e}")
        db.session.rollback()


def handle_customer_updated_webhook(customer_data):
    """Handle customer update webhook"""
    try:
        customer_id = customer_data.get('id')
        email = customer_data.get('email')
        current_app.logger.info(f"🔄 Customer updated: {email} (ID: {customer_id})")
        
    except Exception as e:
        current_app.logger.error(f"Error handling customer updated webhook: {e}")


def handle_charge_succeeded_webhook(charge_data):
    """Handle successful charge webhook"""
    try:
        customer_id = charge_data.get('customer')
        amount = charge_data.get('amount', 0) / 100
        
        if customer_id:
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                current_app.logger.info(f"💰 Charge succeeded: ${amount:.2f} for user {user.id}")
        
    except Exception as e:
        current_app.logger.error(f"Error handling charge succeeded webhook: {e}")


def handle_charge_failed_webhook(charge_data):
    """Handle failed charge webhook"""
    try:
        customer_id = charge_data.get('customer')
        failure_message = charge_data.get('failure_message', 'Unknown error')
        
        if customer_id:
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                current_app.logger.warning(f"❌ Charge failed for user {user.id}: {failure_message}")
        
    except Exception as e:
        current_app.logger.error(f"Error handling charge failed webhook: {e}")


def handle_charge_refunded_webhook(charge_data):
    """Handle charge refund webhook"""
    try:
        customer_id = charge_data.get('customer')
        refund_amount = charge_data.get('amount_refunded', 0) / 100
        
        if customer_id:
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                current_app.logger.info(f"💰 Charge refunded: ${refund_amount:.2f} for user {user.id}")
        
    except Exception as e:
        current_app.logger.error(f"Error handling charge refunded webhook: {e}")


@payments_bp.route('/payment-success')
def payment_success():
    """Payment success page"""
    return render_template('payment_success.html')
