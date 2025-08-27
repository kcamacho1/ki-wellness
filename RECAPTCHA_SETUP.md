# 🔒 Google reCAPTCHA v2 Setup Guide

## **Overview**
This guide will help you set up Google reCAPTCHA v2 for your KI Wellness application to protect against bot attacks and automated registrations.

## **🚀 Quick Setup**

### **Step 1: Get reCAPTCHA Keys**
1. Go to [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin/create)
2. Click **"+ CREATE"** to add a new site
3. Fill in the form:
   - **Label**: KI Wellness (or your preferred name)
   - **reCAPTCHA type**: Select **"reCAPTCHA v2"**
   - **Checkbox**: Select **"I'm not a robot" Checkbox**
   - **Domains**: Add your domain(s):
     - For development: `localhost`, `127.0.0.1`
     - For production: `yourdomain.com`, `www.yourdomain.com`
   - **Owners**: Add additional email addresses if needed
4. Accept the reCAPTCHA Terms of Service
5. Click **"SUBMIT"**

### **Step 2: Copy Your Keys**
After creating the site, you'll see:
- **Site Key** (public key) - used in frontend HTML
- **Secret Key** (private key) - used in backend verification

### **Step 3: Add Keys to Environment Variables**
Add these to your `.env` file:
```bash
# Google reCAPTCHA v2 Configuration
RECAPTCHA_SITE_KEY=your_site_key_here
RECAPTCHA_SECRET_KEY=your_secret_key_here
```

**⚠️ Security Note**: Never commit the `.env` file to version control. The secret key must remain private.

## **🧪 Testing**

### **Development Testing**
1. Start your Flask application
2. Navigate to the registration page
3. You should see the reCAPTCHA checkbox in the final step
4. Complete the form and test the verification

### **Production Deployment**
1. Update your domain in the reCAPTCHA admin console
2. Deploy with the correct environment variables
3. Test the registration process on your live site

## **🔧 Configuration Options**

### **Environment Variables**
| Variable | Description | Required |
|----------|-------------|----------|
| `RECAPTCHA_SITE_KEY` | Public key for frontend widget | Yes |
| `RECAPTCHA_SECRET_KEY` | Private key for backend verification | Yes |

### **Domains Configuration**
- **Development**: `localhost`, `127.0.0.1`, `0.0.0.0`
- **Production**: `yourdomain.com`, `www.yourdomain.com`
- **Testing**: Add your staging domain if applicable

## **🛡️ Security Features**

### **What reCAPTCHA v2 Protects Against**
- ✅ **Bot Registration**: Prevents automated account creation
- ✅ **Spam Attacks**: Blocks malicious registration attempts
- ✅ **Brute Force**: Limits automated form submissions
- ✅ **Advanced Threats**: Google's ML algorithms detect sophisticated bots

### **How It Works**
1. User clicks "I'm not a robot" checkbox
2. Google analyzes user behavior (mouse movements, timing, etc.)
3. If suspicious, presents image challenges
4. Backend verifies the response with Google's servers
5. Only verified responses are allowed through

## **📊 Monitoring**

### **Admin Dashboard**
Monitor reCAPTCHA status in your admin panel:
- Configuration status (enabled/disabled)
- Site key information
- Verification statistics

### **Google Analytics**
You can view reCAPTCHA analytics in the Google reCAPTCHA admin console:
- Number of verifications
- Challenge solve rates
- Blocked attacks

## **🆘 Troubleshooting**

### **Common Issues**

#### **reCAPTCHA Not Showing**
- Check if `RECAPTCHA_SITE_KEY` is set in environment variables
- Verify the domain is registered in Google reCAPTCHA console
- Check browser console for JavaScript errors

#### **"Invalid Site Key" Error**
- Ensure site key matches the one from Google console
- Verify domain is correctly configured
- Check for typos in the environment variable

#### **"Invalid Secret Key" Error**
- Verify secret key is correct
- Ensure it matches the site configuration
- Check for whitespace or hidden characters

#### **Verification Fails**
- Check network connectivity to Google servers
- Verify request is coming from registered domain
- Ensure POST data includes `g-recaptcha-response`

### **Debug Mode**
If reCAPTCHA is not configured, the system will:
- Show a warning message to users
- Allow registration to proceed (for development)
- Log warnings in console

## **🔧 Advanced Configuration**

### **Custom Themes**
You can customize the reCAPTCHA appearance:
```html
<div class="g-recaptcha" 
     data-sitekey="your_site_key" 
     data-theme="light"
     data-size="normal">
</div>
```

### **Language Support**
reCAPTCHA automatically detects user language, but you can force a specific language:
```html
<script src="https://www.google.com/recaptcha/api.js?hl=es" async defer></script>
```

### **Callback Functions**
Handle reCAPTCHA events:
```javascript
function onRecaptchaSuccess(token) {
    console.log('reCAPTCHA completed:', token);
}

function onRecaptchaExpire() {
    console.log('reCAPTCHA expired');
}
```

## **📈 Performance**

### **Loading Optimization**
- reCAPTCHA script loads asynchronously (`async defer`)
- No impact on initial page load
- Lazy loads only when needed

### **Bandwidth Usage**
- Minimal: ~50KB for script + widget
- Additional ~10KB for verification requests
- No server-side performance impact

## **🔒 Production Checklist**

- [ ] Site and secret keys configured in production environment
- [ ] Production domain added to reCAPTCHA console
- [ ] HTTPS enabled for secure communication
- [ ] Environment variables properly secured
- [ ] reCAPTCHA widget displays correctly
- [ ] Form submission works with verification
- [ ] Error handling tested
- [ ] Admin monitoring configured

## **📞 Support**

### **Google reCAPTCHA Documentation**
- [Official Documentation](https://developers.google.com/recaptcha/docs/v2)
- [Admin Console](https://www.google.com/recaptcha/admin)
- [FAQ](https://developers.google.com/recaptcha/docs/faq)

### **Application Support**
If you encounter issues with the KI Wellness implementation:
1. Check the security logs in admin dashboard
2. Verify environment variables are set
3. Test with different browsers/devices
4. Review console logs for errors

---

**Note**: reCAPTCHA v2 is free for most websites. Google may require verification for high-traffic sites.
