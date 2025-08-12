# Admin Login Troubleshooting Guide

## 🔍 **Problem Description**
When entering admin username and password and verifying reCAPTCHA in production, the page refreshes, clears entries, and presents a new login screen again.

## 🎯 **Root Causes & Solutions**

### **1. reCAPTCHA Configuration Issues**

#### **Problem**: reCAPTCHA keys not properly configured
- **Symptoms**: Page refreshes without error message
- **Check**: Visit `/api/recaptcha-status` endpoint
- **Solution**: Set environment variables:
  ```bash
  RECAPTCHA_SITE_KEY=your_site_key_here
  RECAPTCHA_SECRET_KEY=your_secret_key_here
  RECAPTCHA_ENABLED=true
  ```

#### **Problem**: Invalid reCAPTCHA keys
- **Symptoms**: "Security verification failed" error
- **Check**: Verify keys in Google reCAPTCHA console
- **Solution**: Generate new keys and update environment variables

### **2. Admin User Issues**

#### **Problem**: Admin user doesn't exist in production database
- **Symptoms**: "Invalid username or password" error
- **Check**: Verify admin user exists:
  ```sql
  SELECT id, username, is_admin, is_active FROM users WHERE is_admin = true;
  ```
- **Solution**: Create admin user manually or run initialization script

#### **Problem**: Wrong admin password
- **Symptoms**: "Invalid username or password" error
- **Check**: Verify password in environment variables:
  ```bash
  ADMIN_USERNAME=ki.wellness
  ADMIN_PASSWORD=InfiniteAbundance$369
  ```
- **Solution**: Reset admin password or update environment variable

### **3. Session Management Issues**

#### **Problem**: Session not persisting
- **Symptoms**: Login appears successful but redirects back to login
- **Check**: Verify session configuration in production
- **Solution**: Ensure proper session configuration:
  ```python
  app.config['SECRET_KEY'] = 'your-secret-key'
  app.config['SESSION_COOKIE_SECURE'] = True  # For HTTPS
  app.config['SESSION_COOKIE_HTTPONLY'] = True
  ```

### **4. Database Connection Issues**

#### **Problem**: Database connection failing
- **Symptoms**: Generic error messages or timeouts
- **Check**: Verify database connection string and credentials
- **Solution**: Check `DATABASE_URL` environment variable

## 🛠️ **Diagnostic Steps**

### **Step 1: Check reCAPTCHA Status**
```bash
curl https://kiwellness.org/api/recaptcha-status
```

Expected response:
```json
{
  "enabled": true,
  "is_localhost": false,
  "keys_configured": true,
  "site_key_present": true,
  "secret_key_present": true
}
```

### **Step 2: Test Admin Login Flow**
```bash
# Run the diagnostic script
python tests/test_admin_login_production.py
```

### **Step 3: Check Production Logs**
Look for these log messages:
- `🔍 Login attempt for username: ki.wellness`
- `🔍 Login: reCAPTCHA enabled: true`
- `🔍 Login: User found - ID: X, Admin: true, Active: true`
- `✅ Login: Password verification successful`
- `🔍 Login: Session user_id set: X`

### **Step 4: Verify Environment Variables**
```bash
# Check these environment variables are set:
echo $RECAPTCHA_SITE_KEY
echo $RECAPTCHA_SECRET_KEY
echo $RECAPTCHA_ENABLED
echo $ADMIN_USERNAME
echo $ADMIN_PASSWORD
echo $SECRET_KEY
```

## 🔧 **Quick Fixes**

### **Fix 1: Disable reCAPTCHA Temporarily**
```bash
RECAPTCHA_ENABLED=false
```

### **Fix 2: Reset Admin Password**
```python
# In production database
from werkzeug.security import generate_password_hash
new_password_hash = generate_password_hash('InfiniteAbundance$369')
# Update admin user password
```

### **Fix 3: Create Admin User**
```python
# Run this in production
from app.main import create_admin_account
create_admin_account()
```

## 📋 **Production Checklist**

- [ ] `RECAPTCHA_SITE_KEY` is set and valid
- [ ] `RECAPTCHA_SECRET_KEY` is set and valid
- [ ] `RECAPTCHA_ENABLED=true` in production
- [ ] `ADMIN_USERNAME=ki.wellness` is set
- [ ] `ADMIN_PASSWORD=InfiniteAbundance$369` is set
- [ ] `SECRET_KEY` is set and secure
- [ ] Admin user exists in production database
- [ ] Admin user has `is_admin=true` and `is_active=true`
- [ ] Database connection is working
- [ ] Session configuration is correct

## 🚨 **Emergency Access**

If admin login is completely broken:

1. **Temporarily disable reCAPTCHA**:
   ```bash
   RECAPTCHA_ENABLED=false
   ```

2. **Access via direct database**:
   ```sql
   -- Check admin user
   SELECT * FROM users WHERE is_admin = true;
   
   -- Reset admin password if needed
   UPDATE users SET password_hash = 'new_hash' WHERE username = 'ki.wellness';
   ```

3. **Use development environment** for admin tasks temporarily

## 📞 **Support**

If issues persist:
1. Check production logs for specific error messages
2. Run diagnostic script: `python tests/test_admin_login_production.py`
3. Verify all environment variables are set correctly
4. Test reCAPTCHA keys manually in Google console

## 🔄 **Prevention**

- Regularly test admin login in production
- Monitor reCAPTCHA configuration
- Keep admin credentials secure
- Use strong, unique passwords
- Enable logging for login attempts
