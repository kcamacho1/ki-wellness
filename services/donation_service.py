#!/usr/bin/env python3
"""
Donation Service for Ki Wellness
Handles donation processing, tracking, and management
"""

import os
import stripe
from typing import Dict, Any, Optional, List
from datetime import datetime
from config.environment import get_environment_detector
from services.analytics_service import analytics_service

class DonationService:
    """Service for managing donations through Stripe"""
    
    def __init__(self):
        # Get environment detector and Stripe configuration
        self.env_detector = get_environment_detector()
        stripe_config = self.env_detector.get_stripe_config()
        
        # Set Stripe API key
        self.api_key = stripe_config.get('STRIPE_SECRET_KEY')
        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable is required")
        
        # Configure Stripe
        stripe.api_key = self.api_key
        
        # Store environment info
        self.stripe_mode = stripe_config.get('STRIPE_MODE', 'disabled')
        self.stripe_env = stripe_config.get('STRIPE_ENV', 'disabled')
        
        # Donation configuration
        self.donation_url = "https://donate.stripe.com/7sYdR95ld0R9byt8VU3Je02"
        self.donation_amounts = [5, 10, 25, 50, 100]  # Default amounts in dollars
        self.custom_amount_min = 1
        self.custom_amount_max = 1000
        
        # Donation tracking
        self._donations_initialized = False
    
    def setup_donation_tracking(self):
        """Setup donation tracking and analytics"""
        if self._donations_initialized:
            return
            
        try:
            # Initialize donation tracking
            self._donations_initialized = True
            print(f"✅ Donation service initialized in {self.stripe_mode} mode")
            
        except Exception as e:
            print(f"❌ Error setting up donation tracking: {e}")
            print("⚠️ Donation tracking will be limited")
    
    def get_donation_config(self) -> Dict[str, Any]:
        """Get donation configuration for frontend"""
        return {
            'donation_url': self.donation_url,
            'amounts': self.donation_amounts,
            'custom_amount_min': self.custom_amount_min,
            'custom_amount_max': self.custom_amount_max,
            'stripe_mode': self.stripe_mode,
            'stripe_publishable_key': self.env_detector.get_stripe_config().get('STRIPE_PUBLISHABLE_KEY'),
            'currency': 'usd',
            'enabled': self.is_enabled()
        }
    
    def create_donation_session(
        self, 
        amount: int, 
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for donation"""
        try:
            # Verify Stripe is configured
            if not hasattr(stripe, 'api_key') or not stripe.api_key:
                raise Exception("Stripe API key not configured")
            
            # Ensure donation tracking is set up
            self.setup_donation_tracking()
            
            # Validate amount
            if amount < self.custom_amount_min or amount > self.custom_amount_max:
                raise ValueError(f"Amount must be between ${self.custom_amount_min} and ${self.custom_amount_max}")
            
            # Create checkout session for one-time payment
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Ki Wellness Donation',
                            'description': 'Support Ki Wellness development and maintenance',
                            'images': ['https://ki-wellness.com/static/assets/branding/logo.png']
                        },
                        'unit_amount': amount * 100,  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url or f"{self.donation_url}?success=true",
                cancel_url=cancel_url or f"{self.donation_url}?canceled=true",
                metadata={
                    "app": "ki_wellness",
                    "type": "donation",
                    "amount": str(amount),
                    "user_id": str(user_id) if user_id else "anonymous",
                    "user_email": user_email or "anonymous"
                },
                customer_email=user_email,
                allow_promotion_codes=True
            )
            
            # Log donation attempt
            if user_id:
                analytics_service.log_event(
                    user_id=user_id,
                    event_type='donation_initiated',
                    event_data={
                        'amount': amount,
                        'session_id': checkout_session.id,
                        'stripe_mode': self.stripe_mode
                    }
                )
            
            return {
                'success': True,
                'session_id': checkout_session.id,
                'url': checkout_session.url,
                'amount': amount
            }
            
        except stripe.error.InvalidRequestError as e:
            print(f"❌ Stripe Invalid Request Error creating donation session: {e}")
            raise Exception(f"Invalid donation request: {e}")
        except stripe.error.AuthenticationError as e:
            print(f"❌ Stripe Authentication Error creating donation session: {e}")
            raise Exception(f"Stripe authentication failed: {e}")
        except stripe.error.APIConnectionError as e:
            print(f"❌ Stripe API Connection Error creating donation session: {e}")
            raise Exception(f"Stripe connection error: {e}")
        except Exception as e:
            print(f"❌ Error creating donation session: {e}")
            raise
    
    def handle_donation_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle donation-related webhook events"""
        try:
            event_type = event_data.get('type')
            event_id = event_data.get('id')
            
            print(f"📨 Processing donation webhook: {event_type} (ID: {event_id})")
            
            if event_type == 'checkout.session.completed':
                return self.handle_donation_completed(event_data)
            elif event_type == 'payment_intent.succeeded':
                return self.handle_donation_payment_succeeded(event_data)
            elif event_type == 'payment_intent.payment_failed':
                return self.handle_donation_payment_failed(event_data)
            else:
                print(f"ℹ️ Unhandled donation webhook event type: {event_type}")
                return {"status": "ignored", "reason": "unhandled_event_type"}
                
        except Exception as e:
            print(f"❌ Error handling donation webhook: {e}")
            return {"status": "error", "error": str(e)}
    
    def handle_donation_completed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle donation completion webhook"""
        session = event_data.get('data', {}).get('object', {})
        session_id = session.get('id')
        amount_total = session.get('amount_total', 0) / 100  # Convert from cents
        customer_email = session.get('customer_email')
        metadata = session.get('metadata', {})
        
        # Extract user info from metadata
        user_id = metadata.get('user_id')
        donation_amount = metadata.get('amount')
        
        # Log donation success
        if user_id and user_id != 'anonymous':
            try:
                analytics_service.log_revenue(
                    user_id=int(user_id),
                    revenue_type='donation',
                    amount=amount_total,
                    description=f'Donation - ${amount_total:.2f}',
                    metadata={
                        'session_id': session_id,
                        'customer_email': customer_email,
                        'stripe_mode': self.stripe_mode
                    }
                )
            except Exception as e:
                print(f"⚠️ Could not log donation revenue: {e}")
        
        # Log general donation event
        analytics_service.log_event(
            user_id=user_id if user_id and user_id != 'anonymous' else None,
            event_type='donation_completed',
            event_data={
                'amount': amount_total,
                'session_id': session_id,
                'customer_email': customer_email,
                'stripe_mode': self.stripe_mode
            }
        )
        
        print(f"✅ Donation completed: ${amount_total:.2f} (Session: {session_id})")
        return {"status": "success", "action": "donation_completed", "amount": amount_total}
    
    def handle_donation_payment_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful donation payment webhook"""
        payment_intent = event_data.get('data', {}).get('object', {})
        amount = payment_intent.get('amount', 0) / 100
        customer_email = payment_intent.get('receipt_email')
        
        print(f"💰 Donation payment succeeded: ${amount:.2f} (Email: {customer_email})")
        return {"status": "success", "action": "donation_payment_succeeded", "amount": amount}
    
    def handle_donation_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed donation payment webhook"""
        payment_intent = event_data.get('data', {}).get('object', {})
        amount = payment_intent.get('amount', 0) / 100
        error_message = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
        
        print(f"❌ Donation payment failed: ${amount:.2f} - {error_message}")
        return {"status": "success", "action": "donation_payment_failed", "error": error_message}
    
    def get_donation_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get donation statistics"""
        try:
            # This would typically query your database for donation records
            # For now, return basic stats
            return {
                'total_donations': 0,  # Would be calculated from database
                'user_donations': 0,   # Would be calculated from database
                'last_donation': None, # Would be calculated from database
                'donation_url': self.donation_url
            }
        except Exception as e:
            print(f"❌ Error getting donation stats: {e}")
            return {
                'total_donations': 0,
                'user_donations': 0,
                'last_donation': None,
                'donation_url': self.donation_url,
                'error': str(e)
            }
    
    def is_enabled(self) -> bool:
        """Check if donation service is enabled"""
        return (
            self.api_key is not None and 
            self.api_key.strip() != '' and
            hasattr(stripe, 'api_key') and 
            stripe.api_key
        )
    
    def get_donation_embed_code(self, amount: Optional[int] = None) -> str:
        """Get HTML embed code for donation button"""
        if amount:
            return f'<a href="{self.donation_url}" class="donation-button" data-amount="{amount}">Donate ${amount}</a>'
        else:
            return f'<a href="{self.donation_url}" class="donation-button">Support Ki Wellness</a>'

# Global donation service instance
donation_service = None

def get_donation_service() -> DonationService:
    """Get or create the global donation service instance"""
    global donation_service
    if donation_service is None:
        try:
            # Check environment variable before creating service
            stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
            if not stripe_secret_key:
                print("❌ STRIPE_SECRET_KEY environment variable not found")
                print("⚠️ Donation features will be disabled. Please set your STRIPE_SECRET_KEY environment variable.")
                return None
            
            if stripe_secret_key.strip() == '':
                print("❌ STRIPE_SECRET_KEY environment variable is empty")
                print("⚠️ Donation features will be disabled. Please check your STRIPE_SECRET_KEY environment variable.")
                return None
            
            donation_service = DonationService()
            print("✅ Donation service initialized successfully")
            
        except ValueError as e:
            print(f"❌ Donation service initialization failed: {e}")
            print("⚠️ Donation features will be disabled. Please check your STRIPE_SECRET_KEY environment variable.")
            return None
        except Exception as e:
            print(f"❌ Unexpected error initializing donation service: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            return None
    return donation_service
