# Email Setup Guide for Password Reset

Since Google is deprecating app passwords, here are your best options for email functionality.

## 🔥 **Recommended: SendGrid (FREE)**

SendGrid is the easiest and most reliable option:
- ✅ **Free tier**: 100 emails/day
- ✅ **No Gmail setup needed**
- ✅ **Professional delivery**
- ✅ **Works immediately**

### SendGrid Setup (5 minutes)

1. **Sign up for SendGrid**: https://signup.sendgrid.com/
2. **Verify your email** and complete setup
3. **Create API Key**:
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Choose "Restricted Access"
   - Enable "Mail Send" permissions
   - Copy the API key

4. **Update your .env file**:
   ```bash
   cp env_template .env
   ```
   
   Edit `.env`:
   ```bash
   # SendGrid Configuration
   SENDGRID_API_KEY=SG.your-api-key-here
   FROM_EMAIL=your-email@gmail.com
   FROM_NAME=Ki Wellness
   APP_URL=http://localhost:5000
   ```

5. **Test it**:
   ```bash
   python scripts/test_email_config.py
   ```

**That's it!** ✨ Your password reset emails will work immediately.

---

## 📧 **Alternative Options**

### Option 2: Mailgun (Also Great)
- Free tier: 100 emails/day
- Similar to SendGrid
- Sign up at https://www.mailgun.com/

### Option 3: Gmail OAuth2 (Complex)
Requires OAuth2 implementation - more complex but most secure:
- Need to set up Google Cloud Console
- Implement OAuth2 flow
- More development time required

### Option 4: Different Email Provider
Use a provider that still supports app passwords:
- Outlook/Hotmail (still works as of 2024)
- Yahoo Mail
- Custom business email servers

### Option 5: Local Development Only
For testing only - prints emails to console:
```python
# Add to your .env for development
EMAIL_BACKEND=console
```

---

## 🚀 **Quick Setup: SendGrid**

Here's the complete setup for SendGrid:

1. **Get SendGrid API Key** (free account)
2. **Create .env file**:
   ```bash
   DATABASE_URL=your-database-url
   SENDGRID_API_KEY=SG.your-sendgrid-api-key
   FROM_EMAIL=your-email@gmail.com
   FROM_NAME=Ki Wellness
   APP_URL=http://localhost:5000
   SECRET_KEY=your-secret-key
   ```

3. **Test configuration**:
   ```bash
   python scripts/test_email_config.py
   ```

4. **Start your app**:
   ```bash
   python app.py
   ```

The system automatically detects SendGrid and uses it instead of SMTP!

---

## 🔧 **Adding More Email Providers**

If you want to add support for other providers, I can help you implement:

- **Mailgun**: Similar to SendGrid
- **Amazon SES**: AWS Simple Email Service
- **Postmark**: Transaction email specialist
- **Custom SMTP**: Your own email server

Just let me know which one you prefer!

---

## ✅ **Testing Your Setup**

Run this command to test any email configuration:
```bash
python scripts/test_email_config.py
```

Expected output for SendGrid:
```
✅ Email configuration is valid!
   Method: SendGrid
   From Email: your-email@gmail.com
```

---

## 🎯 **Recommendation**

**Go with SendGrid** - it's:
- Free for your needs
- Reliable
- Professional
- Already integrated
- No Gmail complexity

Would you like me to walk you through the SendGrid setup, or would you prefer one of the other options?
