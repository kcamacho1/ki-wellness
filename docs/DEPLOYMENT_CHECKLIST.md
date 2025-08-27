# 🚀 Production Deployment Checklist

## Pre-Deployment Setup

### 1. Stripe Production Setup
- [ ] Switch Stripe Dashboard to "Live" mode
- [ ] Get live API keys (not test keys)
- [ ] Create production webhook endpoint
- [ ] Test webhook delivery
- [ ] Update payment links if using specific products

### 2. Environment Variables
- [ ] `STRIPE_SECRET_KEY` (live key)
- [ ] `STRIPE_PUBLISHABLE_KEY` (live key)
- [ ] `STRIPE_WEBHOOK_SECRET` (from webhook)
- [ ] Verify existing variables are set

### 3. Calendly Setup
- [ ] Ensure Calendly event is public
- [ ] Test booking flow
- [ ] Verify link: `https://calendly.com/ki-wellness/human-health-coach`

## Render Deployment Steps

### 1. Code Preparation
- [ ] All files committed to git
- [ ] No sensitive data in code
- [ ] Build script executable (`chmod +x build.sh`)

### 2. Render Service Configuration
- [ ] Connect GitHub repository
- [ ] Set build command: `chmod +x build.sh && ./build.sh`
- [ ] Set start command: `gunicorn app:app`
- [ ] Configure environment variables

### 3. Database Setup
- [ ] PostgreSQL database provisioned
- [ ] Database URL configured
- [ ] Migration will run automatically

## Post-Deployment Testing

### 1. Basic Functionality
- [ ] Home page loads
- [ ] User registration/login works
- [ ] Dashboard loads
- [ ] Navigation includes "Human Coach" link

### 2. Human Help Feature
- [ ] `/human-help` page loads
- [ ] Profile image displays correctly
- [ ] Payment form renders
- [ ] Stripe Elements load
- [ ] Payment type selection works

### 3. Payment Testing
- [ ] Test payment with Stripe test card
- [ ] Payment success page loads
- [ ] Calendly link works
- [ ] Database records payment session

### 4. Admin Dashboard
- [ ] Admin can log in
- [ ] Payment settings visible
- [ ] Can switch payment types
- [ ] Can update Calendly link

### 5. Security
- [ ] HTTPS enabled
- [ ] Environment variables secure
- [ ] No sensitive data in logs
- [ ] Webhook signature verification

## Monitoring Setup

### 1. Stripe Dashboard
- [ ] Monitor live payments
- [ ] Check webhook delivery
- [ ] Review customer data

### 2. Render Monitoring
- [ ] Application logs
- [ ] Performance metrics
- [ ] Error tracking

### 3. Database Monitoring
- [ ] Connection health
- [ ] Payment session data
- [ ] Backup verification

## Go Live Steps

1. **Final Testing**
   - [ ] Complete end-to-end test
   - [ ] Verify all features work
   - [ ] Check mobile responsiveness

2. **Announcement**
   - [ ] Update any marketing materials
   - [ ] Notify existing users
   - [ ] Social media announcement

3. **Monitoring**
   - [ ] Watch for errors
   - [ ] Monitor payment success rate
   - [ ] Track user engagement

## Emergency Rollback Plan

If issues arise:
1. Disable human help feature in admin dashboard
2. Update navigation to remove link
3. Monitor Stripe for any pending payments
4. Investigate and fix issues
5. Re-enable when resolved

## Success Metrics

Track these after launch:
- [ ] Number of human help page visits
- [ ] Payment conversion rate
- [ ] Calendly booking rate
- [ ] User feedback and satisfaction
- [ ] Revenue generated

---

**Ready to deploy?** ✅

Follow this checklist step by step to ensure a smooth production launch!
