"""
Payment and subscription routes
Handles Stripe checkout, customer portal, subscription status, and payment webhooks
"""
from flask import Blueprint, request, jsonify, redirect, url_for, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime
import stripe
import json

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
        
        # Create or get customer
        if not current_user.stripe_customer_id:
            customer = stripe_client.create_customer(
                email=current_user.email,
                name=current_user.name or current_user.username,
                user_id=current_user.id
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session
        success_url = url_for('payment_success', _external=True)
        cancel_url = url_for('dashboard.profile', _external=True)
        
        checkout_session = stripe_client.create_checkout_session(
            customer_id=current_user.stripe_customer_id,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
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


@payments_bp.route('/payment-success')
def payment_success():
    """Payment success page"""
    return render_template('payment_success.html')
