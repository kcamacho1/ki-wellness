#!/usr/bin/env python3
"""
Industry-Standard Stripe Testing Framework
Tests webhook handling, idempotency, and premium access logic
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User, StripeCustomer, StripeSubscription, StripeInvoice, WebhookEvent
from services.stripe_service_v2 import StripeService

class TestStripeIndustryStandard:
    """Test industry-standard Stripe implementation"""
    
    @pytest.fixture
    def client(self):
        """Create test client with test database"""
        app.config['TESTING'] = True
        app.config['STRIPE_MODE'] = 'test'
        app.config['STRIPE_SECRET_KEY'] = 'sk_test_fake_key'
        app.config['STRIPE_WEBHOOK_SECRET'] = 'whsec_fake_secret'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='fake_hash',
            name='Test User',
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    def test_stripe_service_initialization(self):
        """Test StripeService initializes correctly"""
        with app.app_context():
            service = StripeService()
            assert service.mode == 'test'
            assert service.is_test_mode()
            assert not service.is_live_mode()
            assert service.is_enabled()
    
    def test_checkout_session_creation(self, client, test_user):
        """Test checkout session creation"""
        with app.app_context():
            service = StripeService()
            
            with patch('stripe.checkout.Session.create') as mock_create:
                mock_session = MagicMock()
                mock_session.id = 'cs_test_123'
                mock_session.url = 'https://checkout.stripe.com/test'
                mock_create.return_value = mock_session
                
                result = service.create_checkout_session(
                    user_id=test_user.id,
                    success_url='http://test.com/success',
                    cancel_url='http://test.com/cancel'
                )
                
                assert result['success'] is True
                assert result['session_id'] == 'cs_test_123'
                assert result['checkout_url'] == 'https://checkout.stripe.com/test'
    
    def test_webhook_signature_verification(self, client):
        """Test webhook signature verification"""
        payload = json.dumps({
            'id': 'evt_test_123',
            'type': 'customer.created',
            'data': {'object': {'id': 'cus_test_123', 'email': 'test@example.com'}}
        })
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = ValueError("Invalid payload")
            
            response = client.post('/webhook/stripe',
                                 data=payload,
                                 headers={'Stripe-Signature': 'invalid_sig'})
            
            assert response.status_code == 400
            assert 'Invalid payload' in response.get_json()['error']
    
    def test_checkout_session_completed_webhook(self, client, test_user):
        """Test checkout.session.completed webhook processing"""
        with app.app_context():
            payload = {
                'id': 'evt_test_123',
                'type': 'checkout.session.completed',
                'data': {
                    'object': {
                        'id': 'cs_test_123',
                        'customer': 'cus_test_123',
                        'metadata': {
                            'user_id': str(test_user.id)
                        }
                    }
                }
            }
            
            with patch('stripe.Webhook.construct_event', return_value=payload):
                response = client.post('/webhook/stripe',
                                     data=json.dumps(payload),
                                     headers={'Stripe-Signature': 'test_sig'})
                
                assert response.status_code == 200
                
                # Check customer was linked
                test_user = User.query.get(test_user.id)
                assert test_user.stripe_customer_id == 'cus_test_123'
                
                # Check StripeCustomer record was created
                customer_record = StripeCustomer.query.filter_by(user_id=test_user.id).first()
                assert customer_record is not None
                assert customer_record.stripe_customer_id == 'cus_test_123'
    
    def test_subscription_created_webhook(self, client, test_user):
        """Test customer.subscription.created webhook unlocks premium"""
        with app.app_context():
            # First create customer record
            customer = StripeCustomer(
                user_id=test_user.id,
                stripe_customer_id='cus_test_123',
                email=test_user.email
            )
            db.session.add(customer)
            db.session.commit()
            
            payload = {
                'id': 'evt_test_456',
                'type': 'customer.subscription.created',
                'data': {
                    'object': {
                        'id': 'sub_test_123',
                        'customer': 'cus_test_123',
                        'status': 'active',
                        'current_period_start': int(datetime.now().timestamp()),
                        'current_period_end': int((datetime.now() + timedelta(days=30)).timestamp()),
                        'items': {
                            'data': [{
                                'price': {'id': 'price_test_123'}
                            }]
                        },
                        'cancel_at_period_end': False
                    }
                }
            }
            
            with patch('stripe.Webhook.construct_event', return_value=payload):
                response = client.post('/webhook/stripe',
                                     data=json.dumps(payload),
                                     headers={'Stripe-Signature': 'test_sig'})
                
                assert response.status_code == 200
                
                # Check subscription was created
                subscription = StripeSubscription.query.filter_by(
                    stripe_subscription_id='sub_test_123'
                ).first()
                assert subscription is not None
                assert subscription.status == 'active'
                
                # Check premium access is now enabled
                test_user = User.query.get(test_user.id)
                assert test_user.has_premium_access() is True
    
    def test_invoice_payment_succeeded_webhook(self, client, test_user):
        """Test invoice.payment_succeeded webhook records payment"""
        with app.app_context():
            # Create customer and subscription first
            customer = StripeCustomer(
                user_id=test_user.id,
                stripe_customer_id='cus_test_123',
                email=test_user.email
            )
            db.session.add(customer)
            db.session.commit()
            
            payload = {
                'id': 'evt_test_789',
                'type': 'invoice.payment_succeeded',
                'data': {
                    'object': {
                        'id': 'in_test_123',
                        'customer': 'cus_test_123',
                        'subscription': 'sub_test_123',
                        'amount_paid': 500,
                        'amount_due': 500,
                        'currency': 'usd',
                        'status': 'paid',
                        'created': int(datetime.now().timestamp()),
                        'due_date': int((datetime.now() + timedelta(days=7)).timestamp()),
                        'status_transitions': {
                            'paid_at': int(datetime.now().timestamp())
                        }
                    }
                }
            }
            
            with patch('stripe.Webhook.construct_event', return_value=payload):
                response = client.post('/webhook/stripe',
                                     data=json.dumps(payload),
                                     headers={'Stripe-Signature': 'test_sig'})
                
                assert response.status_code == 200
                
                # Check invoice was recorded
                invoice = StripeInvoice.query.filter_by(
                    stripe_invoice_id='in_test_123'
                ).first()
                assert invoice is not None
                assert invoice.amount_paid == 500
                assert invoice.status == 'paid'
    
    def test_webhook_idempotency(self, client, test_user):
        """Test webhook events are processed only once (idempotency)"""
        with app.app_context():
            payload = {
                'id': 'evt_test_duplicate',
                'type': 'customer.created',
                'data': {
                    'object': {
                        'id': 'cus_test_456',
                        'email': test_user.email
                    }
                }
            }
            
            with patch('stripe.Webhook.construct_event', return_value=payload):
                # First request
                response1 = client.post('/webhook/stripe',
                                      data=json.dumps(payload),
                                      headers={'Stripe-Signature': 'test_sig'})
                assert response1.status_code == 200
                
                # Second request with same event ID
                response2 = client.post('/webhook/stripe',
                                      data=json.dumps(payload),
                                      headers={'Stripe-Signature': 'test_sig'})
                assert response2.status_code == 200
                assert 'already_processed' in response2.get_json()['status']
                
                # Check only one webhook event record exists
                webhook_events = WebhookEvent.query.filter_by(
                    stripe_event_id='evt_test_duplicate'
                ).all()
                assert len(webhook_events) == 1
    
    def test_subscription_expiry_logic(self, test_user):
        """Test subscription expiry affects premium access"""
        with app.app_context():
            # Create expired subscription
            expired_subscription = StripeSubscription(
                user_id=test_user.id,
                stripe_subscription_id='sub_expired',
                stripe_customer_id='cus_test_123',
                stripe_price_id='price_test_123',
                status='active',
                current_period_start=datetime.now() - timedelta(days=35),
                current_period_end=datetime.now() - timedelta(days=5)  # Expired 5 days ago
            )
            db.session.add(expired_subscription)
            db.session.commit()
            
            # Check premium access is denied for expired subscription
            test_user = User.query.get(test_user.id)
            assert test_user.has_premium_access() is False
            
            # Update to valid subscription
            expired_subscription.current_period_end = datetime.now() + timedelta(days=25)
            db.session.commit()
            
            # Check premium access is now granted
            test_user = User.query.get(test_user.id)
            assert test_user.has_premium_access() is True
    
    def test_admin_ff_users_premium_access(self):
        """Test admin and ff users always have premium access"""
        with app.app_context():
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash='fake_hash',
                name='Admin User',
                role='admin'
            )
            db.session.add(admin_user)
            
            # Create ff user
            ff_user = User(
                username='ff_user',
                email='ff@example.com',
                password_hash='fake_hash',
                name='FF User',
                role='ff'
            )
            db.session.add(ff_user)
            db.session.commit()
            
            # Both should have premium access without subscriptions
            assert admin_user.has_premium_access() is True
            assert ff_user.has_premium_access() is True
    
    def test_stripe_environment_detection(self):
        """Test Stripe environment auto-detection"""
        with app.app_context():
            # Test with test key
            app.config['STRIPE_SECRET_KEY'] = 'sk_test_fake_key'
            service = StripeService()
            service._initialize_from_config()
            assert service.is_test_mode()
            assert not service.is_live_mode()
            
            # Test with live key
            app.config['STRIPE_SECRET_KEY'] = 'sk_live_fake_key'
            service = StripeService()
            service._initialize_from_config()
            assert service.is_live_mode()
            assert not service.is_test_mode()
            
            # Test with no key
            app.config['STRIPE_SECRET_KEY'] = None
            service = StripeService()
            service._initialize_from_config()
            assert not service.is_enabled()

def run_tests():
    """Run all Stripe tests"""
    print("🧪 Running Industry-Standard Stripe Tests")
    print("==========================================")
    
    # Run pytest
    pytest.main([__file__, '-v'])

if __name__ == '__main__':
    run_tests()
