# Production Deployment Guide - Ki Wellness Human Help Feature

## 🚀 Render Deployment Setup

### Environment Variables Required

Add these to your Render service environment variables:

#### **Stripe Configuration (Required)**
```bash
STRIPE_SECRET_KEY=sk_live_your_live_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

#### **Database Configuration (Already set)**
```bash
DATABASE_URL=postgresql://your_render_postgres_url
```

#### **App Configuration (Already set)**
```bash
SECRET_KEY=your_secret_key
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
ADMIN_EMAIL=your_admin_email
```

### Stripe Production Setup

1. **Switch to Live Mode**:
   - Go to Stripe Dashboard → Toggle to "Live" mode
   - Get your live API keys (not test keys)

2. **Set Up Production Webhook**:
   - Go to Stripe Dashboard → Developers → Webhooks
   - Add endpoint: `https://your-app-name.onrender.com/stripe-webhook`
   - Select events: `payment_intent.succeeded`
   - Copy the webhook secret

3. **Update Payment Links** (if using specific products):
   - Create live products in Stripe Dashboard
   - Update environment variables with live price IDs

### Calendly Production Setup

1. **Verify Calendly Link**:
   - Ensure your Calendly event is set to "Public"
   - Test the booking flow
   - Update admin dashboard with correct link

### Database Migration

The migration will run automatically on deployment, but you can verify:

```bash
# Check if PaymentSession table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'payment_session'
);
```

### Testing Production

1. **Test Payment Flow**:
   - Visit your live site: `https://your-app-name.onrender.com/human-help`
   - Try a test payment with Stripe test card: `4242 4242 4242 4242`
   - Verify payment success page and Calendly redirect

2. **Test Admin Dashboard**:
   - Log in as admin
   - Verify payment settings are working
   - Test switching between payment types

### Security Checklist

- [ ] Using live Stripe keys (not test keys)
- [ ] Webhook signature verification enabled
- [ ] HTTPS enabled (automatic on Render)
- [ ] Environment variables secured
- [ ] Database connection encrypted

### Monitoring

1. **Stripe Dashboard**:
   - Monitor payments and webhooks
   - Check for failed payments
   - Review customer data

2. **Render Logs**:
   - Monitor application logs
   - Check for errors
   - Monitor performance

### Backup Strategy

- Database backups (automatic on Render)
- Payment session data in database
- Stripe provides payment backup

## 🎯 Go Live Checklist

- [ ] Environment variables configured
- [ ] Stripe live keys set
- [ ] Webhook endpoint configured
- [ ] Calendly link verified
- [ ] Test payment successful
- [ ] Admin dashboard working
- [ ] Database migration complete
- [ ] SSL certificate active
- [ ] Performance monitoring enabled

## 📞 Support

If you encounter issues:
1. Check Render logs
2. Verify environment variables
3. Test Stripe webhook delivery
4. Check database connectivity
