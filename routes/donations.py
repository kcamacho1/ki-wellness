"""
Donation routes for Ki Wellness
Handles donation processing, tracking, and management
"""

from flask import Blueprint, request, jsonify, redirect, url_for, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime
import stripe
import json
import os

# Import services  
from services.donation_service import get_donation_service
from services.analytics_service import analytics_service

# Import utilities
from utils.decorators import premium_required

# Create blueprint
donations_bp = Blueprint('donations', __name__)


@donations_bp.route('/api/donation-config')
def donation_config():
    """Get donation configuration for frontend"""
    try:
        donation_service = get_donation_service()
        if not donation_service:
            return jsonify({
                'success': False,
                'error': 'Donation service not available',
                'details': 'Stripe configuration required'
            }), 503
        
        config = donation_service.get_donation_config()
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ Error getting donation config: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get donation configuration',
            'details': str(e)
        }), 500


@donations_bp.route('/api/create-donation-session', methods=['POST'])
def create_donation_session():
    """Create a Stripe checkout session for donation"""
    try:
        donation_service = get_donation_service()
        if not donation_service:
            return jsonify({
                'success': False,
                'error': 'Donation service not available',
                'details': 'Stripe configuration required'
            }), 503
        
        data = request.get_json()
        amount = data.get('amount')
        user_email = data.get('email')
        
        # Validate amount
        if not amount or not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({
                'success': False,
                'error': 'Valid amount is required',
                'details': 'Amount must be a positive number'
            }), 400
        
        # Convert to integer if needed
        amount = int(amount)
        
        # Get user info if logged in
        user_id = current_user.id if current_user.is_authenticated else None
        user_email = user_email or (current_user.email if current_user.is_authenticated else None)
        
        # Create success and cancel URLs
        success_url = url_for('donations.donation_success', _external=True)
        cancel_url = url_for('donations.donation_canceled', _external=True)
        
        # Create donation session
        result = donation_service.create_donation_session(
            amount=amount,
            user_id=user_id,
            user_email=user_email,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'Invalid donation amount',
            'details': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"❌ Error creating donation session: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create donation session',
            'details': str(e)
        }), 500


@donations_bp.route('/api/donation-stats')
@login_required
def donation_stats():
    """Get donation statistics for current user"""
    try:
        donation_service = get_donation_service()
        if not donation_service:
            return jsonify({
                'success': False,
                'error': 'Donation service not available'
            }), 503
        
        stats = donation_service.get_donation_stats(user_id=current_user.id)
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ Error getting donation stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get donation statistics',
            'details': str(e)
        }), 500


@donations_bp.route('/webhook/donation', methods=['POST'])
def donation_webhook():
    """Handle donation-related webhook events"""
    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        if not sig_header:
            return jsonify({'error': 'Missing signature'}), 400
        
        # Get donation service
        donation_service = get_donation_service()
        if not donation_service:
            return jsonify({'error': 'Donation service not available'}), 503
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
            )
        except ValueError as e:
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Process webhook event
        result = donation_service.handle_donation_webhook(event)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"❌ Donation webhook error: {e}")
        return jsonify({'error': str(e)}), 400


@donations_bp.route('/donate')
def donate():
    """Donation page"""
    try:
        donation_service = get_donation_service()
        if not donation_service:
            return render_template('pages/static/error.html', 
                                 error_title="Donation Service Unavailable",
                                 error_message="The donation service is currently unavailable. Please try again later.")
        
        config = donation_service.get_donation_config()
        return render_template('pages/donations/donate.html', 
                             donation_config=config,
                             user=current_user if current_user.is_authenticated else None)
        
    except Exception as e:
        current_app.logger.error(f"❌ Error loading donation page: {e}")
        return render_template('pages/static/error.html',
                             error_title="Error Loading Donation Page",
                             error_message="There was an error loading the donation page. Please try again later.")


@donations_bp.route('/donation-success')
def donation_success():
    """Donation success page"""
    try:
        # Get session ID from query params if available
        session_id = request.args.get('session_id')
        
        return render_template('pages/donations/donation_success.html',
                             session_id=session_id,
                             user=current_user if current_user.is_authenticated else None)
        
    except Exception as e:
        current_app.logger.error(f"❌ Error loading donation success page: {e}")
        return render_template('pages/static/error.html',
                             error_title="Error Loading Success Page",
                             error_message="There was an error loading the success page.")


@donations_bp.route('/donation-canceled')
def donation_canceled():
    """Donation canceled page"""
    try:
        return render_template('pages/donations/donation_canceled.html',
                             user=current_user if current_user.is_authenticated else None)
        
    except Exception as e:
        current_app.logger.error(f"❌ Error loading donation canceled page: {e}")
        return render_template('pages/static/error.html',
                             error_title="Error Loading Canceled Page",
                             error_message="There was an error loading the canceled page.")


@donations_bp.route('/api/donation-embed')
def donation_embed():
    """Get donation embed code for external use"""
    try:
        donation_service = get_donation_service()
        if not donation_service:
            return jsonify({
                'success': False,
                'error': 'Donation service not available'
            }), 503
        
        amount = request.args.get('amount', type=int)
        embed_code = donation_service.get_donation_embed_code(amount)
        
        return jsonify({
            'success': True,
            'embed_code': embed_code,
            'donation_url': donation_service.donation_url
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ Error getting donation embed: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get donation embed code',
            'details': str(e)
        }), 500


@donations_bp.route('/api/log-donation-event', methods=['POST'])
@login_required
def log_donation_event():
    """Log donation-related events for analytics"""
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})
        
        if not event_type:
            return jsonify({
                'success': False,
                'error': 'Event type is required'
            }), 400
        
        # Log the event
        analytics_service.log_event(
            user_id=current_user.id,
            event_type=event_type,
            event_data=event_data
        )
        
        return jsonify({
            'success': True,
            'message': f'Logged donation event: {event_type}'
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ Error logging donation event: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to log donation event',
            'details': str(e)
        }), 500
