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
    """Create Stripe checkout session for subscription - PURE WEBHOOK APPROACH"""
    try:
        # Get environment variables directly - no Stripe client needed
        stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe_secret_key:
            return jsonify({
                'success': False, 
                'error': 'Payment system not configured.',
                'details': 'STRIPE_SECRET_KEY not found'
            }), 503
        
        # Set Stripe API key directly
        stripe.api_key = stripe_secret_key
        
        # Use environment variable or fallback price ID
        price_id = os.getenv('STRIPE_PREMIUM_PRICE_ID')
        if not price_id or price_id.strip() == '':
            price_id = 'price_1S1Wjb6d7DUvK3X6cz3XoG97'  # Your actual Ki Wellness Premium price ID
            current_app.logger.warning(f"Using fallback price ID: {price_id}")
        
        # Create checkout session without any customer management
        # Let Stripe handle EVERYTHING - webhooks will do the rest
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,  # Just provide email, Stripe creates customer
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('payments.payment_success', _external=True),
            cancel_url=url_for('dashboard.profile', _external=True),
            metadata={
                "app": "ki_wellness",
                "user_id": str(current_user.id),
                "email": current_user.email,
                "username": current_user.username or "unknown"
            }
        )
        
        # Store minimal payment session info
        payment_session = PaymentSession(
            session_id=checkout_session.id,
            user_id=current_user.id,
            email=current_user.email,
            name=current_user.name or current_user.username,
            payment_type='subscription',
            amount=500,  # $5.00 in cents
            status='pending'
        )
        db.session.add(payment_session)
        db.session.commit()
        
        current_app.logger.info(f"✅ Pure webhook checkout session created for user {current_user.id}: {checkout_session.id}")
        
        return jsonify({
            'success': True,
            'session_id': checkout_session.id,
            'checkout_url': checkout_session.url
        })
            
    except stripe.error.AuthenticationError as e:
        current_app.logger.error(f"Stripe authentication error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Payment system authentication failed.',
            'details': 'Invalid Stripe API key'
        }), 503
    except stripe.error.InvalidRequestError as e:
        current_app.logger.error(f"Stripe invalid request: {e}")
        return jsonify({
            'success': False, 
            'error': 'Invalid payment configuration.',
            'details': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error creating checkout session: {e}")
        return jsonify({
            'success': False, 
            'error': 'Failed to create payment session.',
            'details': 'Internal server error'
        }), 500


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
        elif event_type == 'checkout.session.completed':
            handle_checkout_session_completed_webhook(event_data)
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
                stripe_customer_id=customer_id,
                plan_type='premium',
                status=status,
                current_period_end=datetime.fromtimestamp(current_period_end) if current_period_end else None
            )
            db.session.add(subscription)
        else:
            subscription.status = status
            subscription.plan_type = 'premium'
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
            subscription.plan_type = 'premium' if status == 'active' else 'free'
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
            subscription.plan_type = 'free'
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
    """Handle customer creation webhook - PURE WEBHOOK APPROACH"""
    try:
        customer_id = customer_data.get('id')
        email = customer_data.get('email')
        
        # Find user by email since we don't have user_id in customer metadata yet
        user = User.query.filter_by(email=email).first()
        if user and not user.stripe_customer_id:
            user.stripe_customer_id = customer_id
            db.session.commit()
            current_app.logger.info(f"✅ Customer created and linked via email: {email} → User {user.id} (Customer ID: {customer_id})")
        elif not user:
            current_app.logger.warning(f"⚠️ Customer created but no user found with email: {email}")
        else:
            current_app.logger.info(f"ℹ️ Customer already linked: {email} → {user.stripe_customer_id}")
        
    except Exception as e:
        current_app.logger.error(f"Error handling customer created webhook: {e}")
        db.session.rollback()


def handle_checkout_session_completed_webhook(session_data):
    """Handle checkout session completion webhook - PURE WEBHOOK APPROACH"""
    try:
        session_id = session_data.get('id')
        customer_id = session_data.get('customer')
        subscription_id = session_data.get('subscription')
        metadata = session_data.get('metadata', {})
        
        # Get user from metadata or customer email
        user_id = metadata.get('user_id')
        email = metadata.get('email')
        
        user = None
        if user_id:
            user = User.query.get(int(user_id))
        elif email:
            user = User.query.filter_by(email=email).first()
        elif customer_id:
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if not user:
            current_app.logger.warning(f"⚠️ Checkout completed but no user found: session {session_id}")
            return
        
        # Link customer if not already linked
        if customer_id and not user.stripe_customer_id:
            user.stripe_customer_id = customer_id
            current_app.logger.info(f"✅ Customer linked via checkout: User {user.id} → Customer {customer_id}")
        
        # Update payment session status
        payment_session = PaymentSession.query.filter_by(
            session_id=session_id,
            user_id=user.id
        ).first()
        
        if payment_session:
            payment_session.status = 'completed'
            current_app.logger.info(f"✅ Payment session completed: {session_id} for user {user.id}")
        
        db.session.commit()
        current_app.logger.info(f"✅ Checkout session completed for user {user.id}: {session_id}")
        
    except Exception as e:
        current_app.logger.error(f"Error handling checkout session completed webhook: {e}")
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
