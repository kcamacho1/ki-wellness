# 🏗️ Industry-Standard Stripe Integration Guide

## 🎯 Overview

This guide covers the complete industry-standard Stripe integration for Ki Wellness, featuring:

- **Environment Auto-Detection** (Test/Live mode)
- **Webhook-First Architecture** (Backend source of truth)
- **Proper Separation of Concerns** (Frontend/Backend responsibilities)
- **Comprehensive Testing** (Unit/Integration tests)
- **Database Best Practices** (Separate tables for different concerns)

## 📊 Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Stripe        │
│  (Checkout)     │    │  (Webhooks)     │    │  (Source)       │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Create Session  │───▶│ Validate User   │───▶│ Create Session  │
│ Redirect User   │    │ Store Minimal   │    │ Process Payment │
│ Show Success    │    │ Return URL      │    │ Send Webhooks   │
│                 │    │                 │◀───│                 │
│ ❌ Never        │    │ ✅ Update DB    │    │ ✅ Single       │
│ Assumes Success │    │ Unlock Features │    │ Source of Truth │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Setup

### 1. Environment Configuration

Update your `.env` file:

```bash
# Auto-detected environment (use sk_test_ for dev, sk_live_ for prod)
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Price IDs for different environments
STRIPE_TEST_PREMIUM_PRICE_ID=price_test_123
STRIPE_LIVE_PREMIUM_PRICE_ID=price_live_456
```

### 2. Run Migration

```bash
cd /path/to/ki_wellness
python migrations/migrate_stripe_industry_standard.py
```

### 3. Configure Webhooks

In your Stripe Dashboard:

1. Go to **Developers → Webhooks**
2. Add endpoint: `https://kiwellness.org/webhook/stripe`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated` 
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.created`

### 4. Test the Integration

```bash
python tests/test_stripe_industry_standard.py
```

## 📋 Database Schema

### New Industry-Standard Tables

#### `stripe_customer`
- **Purpose**: Maps Stripe customers to app users
- **Key Fields**: `user_id`, `stripe_customer_id`, `email`

#### `stripe_subscription` 
- **Purpose**: Tracks subscription lifecycle
- **Key Fields**: `user_id`, `stripe_subscription_id`, `status`, `current_period_end`

#### `stripe_invoice`
- **Purpose**: Records all payments for accounting
- **Key Fields**: `user_id`, `stripe_invoice_id`, `amount_paid`, `status`

#### `webhook_event`
- **Purpose**: Idempotency and debugging
- **Key Fields**: `stripe_event_id`, `event_type`, `processed`, `processing_result`

### Legacy Tables (Preserved)
- `subscription` - Backward compatibility
- `payment_session` - Human coaching payments

## 🔄 Payment Flow

### Frontend Flow
```javascript
// 1. User clicks "Upgrade to Premium"
fetch('/api/create-checkout-session', {method: 'POST'})
.then(response => response.json())
.then(data => {
    // 2. Redirect to Stripe Checkout
    window.location.href = data.checkout_url;
});

// 3. User completes payment
// 4. Redirected to success page
// ❌ SUCCESS PAGE DOES NOT MEAN PAYMENT SUCCEEDED
// ✅ Only webhook confirmation activates premium features
```

### Backend Flow (Webhook-Driven)
```python
# 1. checkout.session.completed
→ Link customer to user
→ Update stripe_customer_id

# 2. customer.subscription.created  
→ Create StripeSubscription record
→ Set status='active', plan_type='premium'
→ 🎉 Premium features unlocked!

# 3. invoice.payment_succeeded
→ Record StripeInvoice for accounting
→ Confirm payment processed

# 4. Ongoing: customer.subscription.updated
→ Handle renewals, cancellations
→ Update subscription status
```

## 🔒 Security Features

### Webhook Signature Verification
```python
stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
```

### Idempotency Protection
```python
# Every webhook event processed only once
if self._is_event_processed(event['id']):
    return {'status': 'already_processed'}
```

### Environment Isolation
```python
# Auto-detects test vs live mode
if stripe_secret_key.startswith('sk_live_'):
    mode = 'live'
elif stripe_secret_key.startswith('sk_test_'):
    mode = 'test'
```

## 🧪 Testing Strategy

### Unit Tests
```bash
# Test webhook handlers
python -m pytest tests/test_stripe_industry_standard.py::test_webhook_signature_verification

# Test subscription logic  
python -m pytest tests/test_stripe_industry_standard.py::test_subscription_expiry_logic

# Test premium access
python -m pytest tests/test_stripe_industry_standard.py::test_admin_ff_users_premium_access
```

### Integration Tests
```bash
# Test full payment flow
python -m pytest tests/test_stripe_industry_standard.py::test_checkout_session_completed_webhook

# Test subscription creation
python -m pytest tests/test_stripe_industry_standard.py::test_subscription_created_webhook
```

### Stripe CLI Testing (Development)
```bash
# Forward webhooks to local development
stripe listen --forward-to localhost:5000/webhook/stripe

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.created
```

## 🎯 Premium Access Logic

### Enhanced `has_premium_access()` Method
```python
def has_premium_access(self):
    # 1. Admin/FF users → Always premium
    if self.is_admin_role() or self.is_ff_role():
        return True
    
    # 2. Regular users → Check active subscription
    if self.is_regular_user():
        # Check new StripeSubscription table
        active_sub = next((sub for sub in self.stripe_subscriptions 
                          if sub.status == 'active'), None)
        
        if active_sub and active_sub.current_period_end:
            return datetime.utcnow() <= active_sub.current_period_end
        
        # Fallback to legacy subscription table
        # ... backward compatibility logic
    
    return False
```

## 📊 Admin Dashboard Integration

### Enhanced User Display
The admin dashboard now shows:
- **Subscription Status**: Active/Expired with renewal dates
- **Payment History**: Invoice records and amounts
- **Environment Info**: Test vs Live mode indicators
- **Smart Renewal Display**: Days until renewal with visual urgency

### Example Display
```
John Doe (john@example.com)
├── Role: User
├── Subscription: 🟢 Premium
│   ├── Renews March 15, 2025 • $5/month
│   └── Stripe: cus_abc123...
└── Environment: 🧪 Test Mode
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "Payment system not available"
```bash
# Check environment variables
echo $STRIPE_SECRET_KEY
echo $STRIPE_WEBHOOK_SECRET

# Verify mode detection
python -c "from app import app; print(app.config['STRIPE_MODE'])"
```

#### 2. "Webhook signature verification failed"
```bash
# Ensure webhook secret matches Stripe Dashboard
# Check endpoint URL: https://kiwellness.org/webhook/stripe
```

#### 3. "User paid but no premium access"
```bash
# Check webhook events in Stripe Dashboard
# Verify webhook endpoint is receiving events
# Check WebhookEvent table for processing results
```

### Debug Commands

```python
# Check user's subscription status
from database import User, StripeSubscription
user = User.query.filter_by(email='user@example.com').first()
print(f"Premium access: {user.has_premium_access()}")
print(f"Subscriptions: {user.stripe_subscriptions}")

# Check webhook processing
from database import WebhookEvent
events = WebhookEvent.query.order_by(WebhookEvent.created_at.desc()).limit(10).all()
for event in events:
    print(f"{event.event_type}: {event.processed}")
```

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Update `.env` with production Stripe keys
- [ ] Run migration script on production
- [ ] Configure webhook endpoint in Stripe Dashboard
- [ ] Test webhook delivery to production URL

### Post-Deployment  
- [ ] Verify environment auto-detection logs
- [ ] Test small payment end-to-end
- [ ] Check webhook events are being processed
- [ ] Verify premium features unlock correctly

### Monitoring
- [ ] Monitor webhook delivery in Stripe Dashboard
- [ ] Check `webhook_event` table for processing results
- [ ] Monitor application logs for Stripe errors
- [ ] Set up alerts for failed webhook processing

## 💡 Best Practices

### Security
1. **Never trust frontend** - Always verify via webhooks
2. **Verify signatures** - Prevent spoofed requests
3. **Use idempotency** - Handle webhook retries safely
4. **Separate environments** - Test vs Live isolation

### Performance
1. **Database-first** - Check local DB, not Stripe API
2. **Minimal API calls** - Only when absolutely necessary
3. **Efficient queries** - Index on stripe_customer_id, stripe_subscription_id
4. **Background processing** - Webhooks handle heavy lifting

### Maintainability
1. **Single responsibility** - Frontend creates sessions, backend processes webhooks
2. **Proper logging** - Detailed logs for debugging
3. **Error handling** - Graceful degradation
4. **Testing coverage** - Unit and integration tests

## 🎉 Benefits of Industry-Standard Implementation

### Reliability
- ✅ Webhook-driven (handles failures, retries)
- ✅ Idempotent processing (no duplicate charges)
- ✅ Database source of truth (not dependent on API)

### Scalability  
- ✅ Minimal Stripe API calls (better rate limits)
- ✅ Async processing (doesn't block user experience)
- ✅ Efficient database queries (indexed properly)

### Maintainability
- ✅ Clear separation of concerns
- ✅ Comprehensive testing framework
- ✅ Detailed logging and monitoring

### Security
- ✅ Signature verification (prevents spoofing)
- ✅ Environment isolation (test/live separation)
- ✅ Proper error handling (no sensitive data leaks)

---

## 📞 Support

If you encounter issues:

1. **Check the logs** - Look for Stripe-related errors
2. **Verify webhooks** - Ensure events are being delivered
3. **Test environment** - Use Stripe test mode first
4. **Run tests** - Execute the test suite to verify functionality

The industry-standard implementation provides a robust, scalable, and maintainable foundation for subscription payments! 🚀
