"""
Ki Wellness - Subscription Routes
=================================

This module contains subscription and payment-related routes
including Stripe integration for session credits and subscriptions.

Author: Ki Wellness Team
Version: 2.0
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime
from ..models import db, User, UserSubscription, SessionCredits, TokenUsage
from ..services import UserService
from ..decorators import login_required
from ..config import get_stripe_config, STRIPE_AVAILABLE

# Create blueprint
subscription_bp = Blueprint('subscription', __name__)


@subscription_bp.route('/subscription/status')
@login_required
def subscription_status():
    """Get user's subscription status and usage information"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        subscription_info = UserService.get_user_subscription_info(current_user.id)
        if not subscription_info:
            return jsonify({'success': False, 'error': 'Unable to retrieve subscription information'}), 500
        
        can_use_ai = UserService.can_user_use_ai(current_user.id)
        
        return jsonify({
            'success': True,
            'data': {
                'subscription_info': subscription_info,
                'can_use_ai': can_use_ai
            }
        })
    except Exception as e:
        print(f"❌ Error getting subscription status: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@subscription_bp.route('/subscription/purchase-credits', methods=['POST'])
@login_required
def purchase_session_credits():
    """Handle session credit purchase (redirect to Stripe)"""
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        if quantity < 1 or quantity > 1000:  # Increased limit for bulk purchases
            return jsonify({'success': False, 'error': 'Invalid quantity (1-1000)'}), 400
        
        # Use the new Stripe link that allows custom quantities
        # The link will handle the quantity parameter and calculate total price
        stripe_url = "https://buy.stripe.com/bJe14naFxdDVdGB9ZY3Je06"
        
        # Add user metadata to track the purchase
        current_user = UserService.get_current_user()
        if current_user:
            # Store pending purchase in database for tracking
            pending_purchase = SessionCredits(
                user_id=current_user.id,
                credits_purchased=quantity,
                credits_used=0,
                credits_remaining=0,  # Will be updated after payment
                payment_amount_usd=quantity,  # $1 per credit
                payment_status='pending',
                stripe_payment_intent_id=None  # Will be updated after payment
            )
            db.session.add(pending_purchase)
            db.session.commit()
            
            print(f"📝 Created pending purchase record: {quantity} credits for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'redirect_url': stripe_url,
            'message': f'Redirecting to purchase {quantity} session credit(s) for ${quantity:.2f}',
            'quantity': quantity,
            'total_cost': quantity
        })
    except Exception as e:
        print(f"❌ Error processing credit purchase: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@subscription_bp.route('/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_to_subscription():
    """Handle subscription upgrade (redirect to Stripe)"""
    try:
        # Redirect to Stripe checkout for $10/month subscription
        stripe_url = "https://buy.stripe.com/aFadR92917fx9qlgom3Je05"
        
        return jsonify({
            'success': True,
            'redirect_url': stripe_url,
            'message': 'Redirecting to monthly subscription for $10/month'
        })
    except Exception as e:
        print(f"❌ Error processing subscription upgrade: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@subscription_bp.route('/api/stripe/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session for session credits"""
    if not STRIPE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stripe not available'}), 503
    
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        if quantity < 1 or quantity > 1000:
            return jsonify({'success': False, 'error': 'Invalid quantity (1-1000)'}), 400
        
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get current Stripe configuration
        stripe_config = get_stripe_config()
        if not stripe_config:
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 503
        
        import stripe
        # Update Stripe API key if needed
        if stripe.api_key != stripe_config['secret_key']:
            stripe.api_key = stripe_config['secret_key']
        
        # Create or get Stripe customer
        customer = None
        if current_user.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(current_user.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
        
        if not customer:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session for session credits
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Ki Wellness Session Credits',
                        'description': f'{quantity} AI-powered wellness session credits',
                    },
                    'unit_amount': 100,  # $1.00 in cents
                },
                'quantity': quantity,
            }],
            mode='payment',
            success_url=request.host_url + 'subscription?success=true',
            cancel_url=request.host_url + 'subscription?canceled=true',
            customer=customer.id,
            metadata={
                'user_id': current_user.id,
                'type': 'session_credits',
                'quantity': quantity
            }
        )
        
        return jsonify({
            'success': True,
            'session_id': checkout_session.id,
            'checkout_url': checkout_session.url
        })
        
    except Exception as e:
        print(f"❌ Error creating checkout session: {e}")
        return jsonify({'success': False, 'error': 'Failed to create checkout session'}), 500


@subscription_bp.route('/api/stripe/create-subscription', methods=['POST'])
@login_required
def create_subscription():
    """Create a Stripe subscription"""
    if not STRIPE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stripe not available'}), 503
    
    try:
        # Create customer if doesn't exist
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get current Stripe configuration
        stripe_config = get_stripe_config()
        if not stripe_config:
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 503
        
        import stripe
        # Update Stripe API key if needed
        if stripe.api_key != stripe_config['secret_key']:
            stripe.api_key = stripe_config['secret_key']
        
        # Create or get Stripe customer
        customer = None
        if current_user.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(current_user.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
        
        if not customer:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session for subscription
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'recurring': {
                        'interval': 'month',
                    },
                    'product_data': {
                        'name': 'Ki Wellness Monthly Subscription',
                        'description': 'Unlimited AI-powered wellness sessions',
                    },
                    'unit_amount': 1000,  # $10.00 in cents
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription?success=true',
            cancel_url=request.host_url + 'subscription?canceled=true',
            customer=customer.id,
            metadata={
                'user_id': current_user.id,
                'type': 'subscription'
            }
        )
        
        return jsonify({
            'success': True,
            'session_id': checkout_session.id,
            'checkout_url': checkout_session.url
        })
        
    except Exception as e:
        print(f"❌ Error creating subscription: {e}")
        return jsonify({'success': False, 'error': 'Failed to create subscription'}), 500


@subscription_bp.route('/api/stripe/create-portal-session', methods=['POST'])
@login_required
def create_portal_session():
    """Create a Stripe customer portal session for billing management"""
    if not STRIPE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stripe not available'}), 503
    
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get current Stripe configuration
        stripe_config = get_stripe_config()
        if not stripe_config:
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 503
        
        import stripe
        # Update Stripe API key if needed
        if stripe.api_key != stripe_config['secret_key']:
            stripe.api_key = stripe_config['secret_key']
        
        # Get or create Stripe customer
        customer = None
        if current_user.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(current_user.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
        
        if not customer:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=request.host_url + 'subscription'
        )
        
        return jsonify({
            'success': True,
            'portal_url': portal_session.url
        })
        
    except Exception as e:
        print(f"❌ Error creating portal session: {e}")
        return jsonify({'success': False, 'error': 'Failed to create portal session'}), 500


@subscription_bp.route('/subscription/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for payment events"""
    if not STRIPE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stripe not available'}), 503
    
    try:
        # Get webhook data
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        # Get Stripe configuration
        stripe_config = get_stripe_config()
        if not stripe_config or not stripe_config['webhook_secret']:
            return jsonify({'success': False, 'error': 'Webhook secret not configured'}), 503
        
        import stripe
        stripe.api_key = stripe_config['secret_key']
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, stripe_config['webhook_secret']
            )
        except ValueError as e:
            print(f"❌ Invalid payload: {e}")
            return jsonify({'success': False, 'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            print(f"❌ Invalid signature: {e}")
            return jsonify({'success': False, 'error': 'Invalid signature'}), 400
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_checkout_completed(session)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            handle_invoice_payment_succeeded(invoice)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            handle_subscription_deleted(subscription)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return jsonify({'success': False, 'error': 'Webhook processing failed'}), 500


def handle_checkout_completed(session):
    """Handle completed checkout session"""
    try:
        user_id = session['metadata'].get('user_id')
        session_type = session['metadata'].get('type')
        
        if not user_id:
            print("❌ No user_id in session metadata")
            return
        
        user = User.query.get(user_id)
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        if session_type == 'session_credits':
            quantity = int(session['metadata'].get('quantity', 1))
            
            # Update or create session credits
            credits = SessionCredits.query.filter_by(user_id=user_id).first()
            if not credits:
                credits = SessionCredits(user_id=user_id)
                db.session.add(credits)
            
            credits.credits_purchased += quantity
            credits.credits_remaining += quantity
            credits.payment_amount_usd += session['amount_total'] / 100  # Convert from cents
            credits.payment_status = 'completed'
            credits.stripe_payment_intent_id = session['payment_intent']
            
            db.session.commit()
            print(f"✅ Added {quantity} credits for user {user_id}")
            
        elif session_type == 'subscription':
            # Create or update subscription
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription:
                subscription = UserSubscription(user_id=user_id)
                db.session.add(subscription)
            
            subscription.stripe_subscription_id = session['subscription']
            subscription.stripe_customer_id = session['customer']
            subscription.is_active = True
            subscription.billing_cycle_start = datetime.utcnow()
            
            db.session.commit()
            print(f"✅ Created subscription for user {user_id}")
            
    except Exception as e:
        print(f"❌ Error handling checkout completed: {e}")
        db.session.rollback()


def handle_invoice_payment_succeeded(invoice):
    """Handle successful invoice payment"""
    try:
        # This would handle recurring subscription payments
        # For now, just log the event
        print(f"✅ Invoice payment succeeded: {invoice['id']}")
        
    except Exception as e:
        print(f"❌ Error handling invoice payment: {e}")


def handle_subscription_deleted(subscription):
    """Handle subscription deletion"""
    try:
        # Find and deactivate the subscription
        user_subscription = UserSubscription.query.filter_by(
            stripe_subscription_id=subscription['id']
        ).first()
        
        if user_subscription:
            user_subscription.is_active = False
            db.session.commit()
            print(f"✅ Deactivated subscription for user {user_subscription.user_id}")
        
    except Exception as e:
        print(f"❌ Error handling subscription deletion: {e}")
        db.session.rollback()


@subscription_bp.route('/subscription')
@login_required
def subscription_page():
    """Subscription management page"""
    return render_template('subscription.html')
