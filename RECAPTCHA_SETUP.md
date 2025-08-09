# reCAPTCHA Setup Guide

## 🔒 Overview

KI Wellness now uses Google reCAPTCHA v2 to protect login and registration forms from bots and automated attacks. This guide will help you set up reCAPTCHA for your application.

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

1. Run the setup script:
   ```bash
   python setup_recaptcha.py
   ```

2. Follow the prompts to enter your reCAPTCHA keys
3. Restart your Flask application

### Option 2: Manual Setup

1. Get reCAPTCHA keys from Google
2. Create a `.env` file in your project root
3. Add your keys to the `.env` file
4. Restart your Flask application

## 📋 Step-by-Step Instructions

### 1. Get reCAPTCHA Keys

1. Visit [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
2. Click "Create" to register a new site
3. Choose "reCAPTCHA v2" > "I'm not a robot" Checkbox
4. Add your domains:
   - **Development**: `localhost`, `127.0.0.1`
   - **Production**: Your actual domain (e.g., `example.com`)
5. Accept the terms and click "Submit"
6. Copy the "Site Key" and "Secret Key"

### 2. Configure Environment Variables

Create a `.env` file in your project root:

```bash
# reCAPTCHA Configuration
RECAPTCHA_PUBLIC_KEY=your_site_key_here
RECAPTCHA_PRIVATE_KEY=your_secret_key_here
RECAPTCHA_ENABLED=true
```

### 3. Restart Application

After setting up your keys, restart your Flask application:

```bash
# Stop the current application (Ctrl+C)
# Then restart it
python run.py
```

## 🧪 Development Mode

For development and testing, the application includes:

- **Test Keys**: Automatically uses Google's test keys if no environment variables are set
- **Development Mode**: Shows a warning when using test keys
- **Disable Option**: Can disable reCAPTCHA entirely for testing

### Test Keys (Development Only)

If you don't have real keys yet, the application will use these test keys:

- **Site Key**: `6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI`
- **Secret Key**: `6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe`

⚠️ **Important**: Test keys only work on `localhost` and `127.0.0.1`. They will show a warning message.

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RECAPTCHA_PUBLIC_KEY` | Your reCAPTCHA site key | Test key | Yes (for production) |
| `RECAPTCHA_PRIVATE_KEY` | Your reCAPTCHA secret key | Test key | Yes (for production) |
| `RECAPTCHA_ENABLED` | Enable/disable reCAPTCHA | `true` | No |

### Disable reCAPTCHA

To disable reCAPTCHA for testing, set:

```bash
RECAPTCHA_ENABLED=false
```

## 🎯 Testing

### Test reCAPTCHA Functionality

1. Start your Flask application
2. Visit `/login` or `/register`
3. Verify the reCAPTCHA widget appears
4. Complete the reCAPTCHA challenge
5. Submit the form
6. Check that the form submits successfully

### Test Keys Behavior

When using test keys:
- The reCAPTCHA widget will show a warning message
- Any non-empty response will be accepted
- The widget will work on `localhost` and `127.0.0.1`

## 🚨 Troubleshooting

### Common Issues

1. **"Error for site owner: invalid key"**
   - Solution: Replace placeholder keys with real keys from Google
   - Or use the test keys for development

2. **reCAPTCHA widget not appearing**
   - Check that `RECAPTCHA_ENABLED=true`
   - Verify the site key is correct
   - Check browser console for JavaScript errors

3. **Form submission fails**
   - Ensure reCAPTCHA is completed
   - Check server logs for validation errors
   - Verify the secret key is correct

4. **reCAPTCHA not working on production**
   - Ensure you're using HTTPS (required for reCAPTCHA)
   - Add your production domain to reCAPTCHA settings
   - Verify the domain matches exactly

### Debug Mode

For debugging, you can:

1. Check browser console for JavaScript errors
2. Look at Flask application logs
3. Verify environment variables are loaded correctly

## 🔗 Useful Links

- [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
- [reCAPTCHA Documentation](https://developers.google.com/recaptcha)
- [Test Keys Documentation](https://developers.google.com/recaptcha/docs/faq#id-like-to-run-automated-tests-with-recaptcha-v2-what-should-i-do)

## 🎉 Success!

Once configured, your application will have:

- ✅ Bot protection on login and registration forms
- ✅ User-friendly "I'm not a robot" checkbox
- ✅ Secure server-side validation
- ✅ Development-friendly test mode
- ✅ Production-ready configuration

Your KI Wellness application is now protected with industry-standard reCAPTCHA security!
