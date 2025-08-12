# reCAPTCHA v2 Setup Guide

## 🚀 Phase 1: Immediate Replacements Complete!

We've successfully replaced Cloudflare Turnstile with Google reCAPTCHA v2 checkbox and added comprehensive bot protection.

## 🔑 Required Configuration

### **Environment Variables**
Add these to your `.env` file:

```bash
# Google reCAPTCHA v2 Configuration
RECAPTCHA_SITE_KEY=your_recaptcha_site_key_here
RECAPTCHA_SECRET_KEY=your_recaptcha_secret_key_here
RECAPTCHA_ENABLED=true
```

### **Getting reCAPTCHA Keys**

1. **Go to [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)**
2. **Click "Create" to add a new site**
3. **Choose reCAPTCHA v2**
4. **Add your domains:**
   - `localhost` (for development)
   - `kiwellness.org` (for production)
   - Any other domains you use
5. **Copy the Site Key and Secret Key**

## 🛡️ Security Features Implemented

### **1. reCAPTCHA v2**
- **Checkbox verification** - user clicks "I'm not a robot"
- **Simple pass/fail protection** - either verified or not
- **User-friendly interface** - familiar checkbox design
- **Automatic localhost bypass** - disabled in development

### **2. Rate Limiting**
- **Login**: 5 attempts per minute
- **Register**: 3 attempts per hour
- **Reviews**: 5 submissions per hour
- **Contact**: 3 messages per hour

### **3. Honeypot Fields**
- **Hidden fields** that bots fill out but humans don't
- **Multiple field names** for better bot detection
- **Automatic rejection** of suspicious submissions

## 📱 Frontend Changes

### **Login Form**
- Added honeypot field (`website`)
- reCAPTCHA v2 checkbox integration
- Enhanced error handling

### **Register Form**
- Same security features as login
- reCAPTCHA v2 checkbox integration
- Consistent user experience

### **Reviews Form**
- reCAPTCHA v2 checkbox for review submissions
- Honeypot protection
- Rate limiting

### **Contact Form**
- Honeypot validation
- Rate limiting protection

## 🔧 Backend Changes

### **New Functions**
- `verify_recaptcha()` - Replaces Turnstile verification (updated for v2)
- `check_honeypot()` - Bot detection via honeypot fields

### **Updated Routes**
- All forms now use reCAPTCHA v2 checkbox
- Rate limiting applied to sensitive endpoints
- Enhanced logging and debugging

### **Configuration**
- Automatic environment detection
- Localhost bypass for development
- Production enforcement for live sites

## 🧪 Testing

### **Development Mode**
- reCAPTCHA automatically disabled on localhost
- Rate limiting still active for testing
- Honeypot fields still functional

### **Production Mode**
- reCAPTCHA v2 checkbox fully enabled
- All security measures active
- Comprehensive logging

## 📊 Monitoring

### **Backend Logs**
- reCAPTCHA verification results
- Honeypot detections
- Rate limit violations
- Detailed error information

### **Frontend Console**
- reCAPTCHA loading status
- Verification execution
- Error handling and user feedback

## 🚨 Troubleshooting

### **Common Issues**

1. **"reCAPTCHA not available"**
   - Check if running on localhost
   - Verify environment variables are set
   - Check browser console for errors

2. **"Verification failed"**
   - Check backend logs for detailed error
   - Verify reCAPTCHA keys are correct
   - Check if checkbox was completed

3. **Rate limiting errors**
   - Wait for the time limit to expire
   - Check if multiple users share same IP
   - Consider adjusting limits if needed

### **Debug Commands**
```bash
# Check reCAPTCHA status
curl http://localhost:5001/api/recaptcha-status

# Test rate limiting
# Try submitting forms multiple times quickly
```

## 🔄 Migration Notes

### **What Was Removed**
- Cloudflare Turnstile integration
- Turnstile JavaScript modules
- Turnstile configuration

### **What Was Added**
- Google reCAPTCHA v2 checkbox
- Rate limiting with Flask-Limiter
- Honeypot field validation
- Enhanced security logging

### **What Was Kept**
- Localhost development bypass
- Environment-based configuration
- Comprehensive error handling
- User-friendly error messages

## 🎯 Next Steps

1. **Set up reCAPTCHA keys** in Google Admin Console
2. **Update environment variables** with your keys
3. **Test on localhost** (should bypass automatically)
4. **Deploy to production** and test verification
5. **Monitor logs** for any issues

## 📞 Support

If you encounter any issues:
1. Check the backend logs for detailed error information
2. Verify your reCAPTCHA keys are correct
3. Test on localhost first (should work without keys)
4. Check browser console for frontend errors

The new system provides the same level of protection as Turnstile but with better integration, more reliable verification, and comprehensive bot detection through multiple layers of security. The v2 checkbox provides a more user-friendly experience compared to v3's invisible verification.
