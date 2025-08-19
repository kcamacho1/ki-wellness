# Human Help Feature Setup Guide

## Overview
The Human Help feature allows users to book 30-minute health coaching sessions with you through Stripe payments and Calendly scheduling.

## Features
- **Payment Processing**: Secure Stripe integration for $20 payments
- **Appointment Scheduling**: Calendly integration for easy booking
- **Admin Controls**: Switch between 30-minute sessions and donations
- **Payment Tracking**: Database storage of all payment sessions
- **User-Friendly**: Works for both logged-in and anonymous users

## Environment Variables Required

Add these to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Optional: Stripe Price IDs (if using specific products)
STRIPE_PRICE_ID_30MIN=price_your_30min_session_price_id
STRIPE_PRICE_ID_DONATION=price_your_donation_price_id
```

## Stripe Setup

1. **Create a Stripe Account**: Sign up at [stripe.com](https://stripe.com)
2. **Get API Keys**: 
   - Go to Stripe Dashboard → Developers → API Keys
   - Copy your publishable and secret keys
3. **Set Up Webhooks** (Optional):
   - Go to Stripe Dashboard → Developers → Webhooks
   - Add endpoint: `https://yourdomain.com/stripe-webhook`
   - Select events: `payment_intent.succeeded`
   - Copy the webhook secret

## Calendly Setup

1. **Create Calendly Account**: Sign up at [calendly.com](https://calendly.com)
2. **Create Event Type**:
   - Name: "30-Minute Health Coaching Session"
   - Duration: 30 minutes
   - Add your video call integration (Zoom, Google Meet, etc.)
3. **Get Your Link**: Copy your Calendly link (e.g., `https://calendly.com/ki-wellness/human-health-coach`)

## Admin Dashboard Configuration

1. **Access Admin Dashboard**: Log in as admin and go to `/admin`
2. **Payment Type Settings**:
   - Choose between "30-Minute Session ($20)" or "Donation"
   - Update the payment type as needed
3. **Calendly Link**:
   - Enter your Calendly scheduling link
   - This will be shown to users after successful payment

## Database Migration

The feature automatically creates the required database table. If you need to run it manually:

```bash
python migrate_add_payment_sessions.py
```

## Testing

Run the test script to verify everything is working:

```bash
python test_human_help.py
```

## User Flow

1. **User visits `/human-help`**
   - Can be logged in or anonymous
   - Sees service description and pricing

2. **User fills payment form**
   - Enters name and email
   - Selects payment type (30-min session or donation)
   - Enters payment information via Stripe

3. **Payment processing**
   - Stripe processes the payment
   - Payment session is stored in database
   - User is redirected to success page

4. **Success page**
   - Shows payment confirmation
   - Provides Calendly link for scheduling (for 30-min sessions)
   - Includes payment details and support information

## Files Added/Modified

### New Files:
- `templates/human_help.html` - Main payment page
- `templates/payment_success.html` - Success page
- `migrate_add_payment_sessions.py` - Database migration
- `test_human_help.py` - Test script
- `HUMAN_HELP_SETUP.md` - This documentation

### Modified Files:
- `app.py` - Added routes and PaymentSession model
- `requirements.txt` - Added Stripe dependency
- `templates/components/navigation.html` - Added Human Coach link
- `templates/admin_dashboard.html` - Added payment settings
- `static/js/admin_dashboard.js` - Added payment settings functionality

## Routes Added

- `GET /human-help` - Human help page
- `POST /create-payment-intent` - Create Stripe payment intent
- `GET /payment-success` - Payment success page
- `POST /stripe-webhook` - Stripe webhook handler

## Security Considerations

- All payments are processed securely through Stripe
- Payment sessions are stored in the database for tracking
- Webhook signature verification ensures data integrity
- User data is handled according to privacy standards

## Support

For issues or questions:
1. Check the test script output
2. Verify environment variables are set correctly
3. Ensure Stripe account is properly configured
4. Check database migration completed successfully

## Future Enhancements

Potential improvements:
- Email notifications for successful payments
- Integration with calendar systems
- Payment analytics and reporting
- Multiple session types and pricing tiers
- Automated follow-up emails
