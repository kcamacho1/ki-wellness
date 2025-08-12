# Stripe Integration Setup Guide

This guide explains how to set up Stripe payment processing for KI Wellness with both sandbox (testing) and live (production) environments.

## Environment Variables Setup

1. Copy the `env.example` file to `.env`:
   ```bash
   cp env.example .env
   ```

2. Add your Stripe API keys to the `.env` file:

   ### Live Environment (Production)
   ```
   STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key_here
   STRIPE_SECRET_KEY=sk_live_your_live_secret_key_here
   STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret_here
   ```

   ### Sandbox Environment (Testing)
   ```
   STRIPE_SANDBOX_PUBLISHABLE_KEY=pk_test_your_sandbox_publishable_key_here
   STRIPE_SANDBOX_SECRET_KEY=sk_test_your_sandbox_secret_key_here
   STRIPE_SANDBOX_WEBHOOK_SECRET=whsec_your_sandbox_webhook_secret_here
   ```

## Admin Dashboard Configuration

1. Log in to the admin dashboard
2. Navigate to "System & Settings" tab
3. Find the "Payment Testing Mode" section
4. Use the toggle to switch between:
   - **Sandbox (Testing)**: Uses test API keys, no real charges
   - **Live (Production)**: Uses live API keys, real charges

## API Routes

The application now uses proper Stripe API routes instead of direct links:

- **Session Credits Purchase**: `/api/stripe/create-checkout-session`
- **Subscription Creation**: `/api/stripe/create-subscription`
- **Customer Portal**: `/api/stripe/create-portal-session`
- **Webhook Handler**: `/subscription/stripe-webhook`

## Webhook Setup

1. In your Stripe Dashboard, go to Webhooks
2. Add endpoint: `https://yourdomain.com/subscription/stripe-webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
4. Copy the webhook secret to your `.env` file

## Testing

### Sandbox Mode
- Use test card numbers from Stripe documentation
- No real charges will be processed
- Perfect for development and testing

### Live Mode
- Real payments will be processed
- Use only in production environment
- Ensure all security measures are in place

## Security Notes

- Never commit API keys to version control
- Always use environment variables
- Keep webhook secrets secure
- Test thoroughly in sandbox before going live

## Troubleshooting

- Check that Stripe library is installed: `pip install stripe==8.10.0`
- Verify environment variables are loaded correctly
- Check admin dashboard for payment mode status
- Review application logs for Stripe-related errors
