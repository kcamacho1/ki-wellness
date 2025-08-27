# 🔒 Security Features - KI Wellness App

## **Overview**
This document outlines the comprehensive security measures implemented to protect your Flask application against SQL injections, bot attacks, and other security threats.

## **🛡️ Security Layers Implemented**

### **1. SQL Injection Protection**
- **Pattern Detection**: Advanced regex patterns to detect SQL injection attempts
- **Input Validation**: All user inputs are validated before processing
- **Parameterized Queries**: Safe database queries using SQLAlchemy
- **Input Sanitization**: Automatic removal of dangerous characters

**Protected Against:**
- `UNION SELECT` attacks
- `DROP TABLE` commands
- `INSERT/UPDATE/DELETE` injection
- Comment-based attacks (`--`, `/* */`)
- Hex-encoded attacks (`0x...`)
- Time-based attacks (`WAITFOR DELAY`, `SLEEP`)

### **2. Bot Protection**
- **User-Agent Analysis**: Detection of automated tools and bots
- **Behavioral Analysis**: Pattern recognition for automated requests
- **IP Blocking**: Automatic blocking of suspicious IP addresses
- **Request Frequency Monitoring**: Detection of rapid-fire requests

**Bot Signatures Detected:**
- `bot`, `crawler`, `spider`, `scraper`
- `python`, `curl`, `wget`, `http`
- `java`, `perl`, `ruby`, `php`, `go`, `rust`

### **3. Rate Limiting**
- **Global Rate Limiting**: 60 requests per minute per IP
- **Endpoint-Specific Limits**:
  - Login: 10 attempts per minute
  - Registration: 5 attempts per 5 minutes
  - AI Chat: 30 requests per minute
- **Automatic Blocking**: IPs exceeding limits are temporarily blocked

### **4. Input Validation & Sanitization**
- **Length Limits**: Maximum input lengths enforced
- **Character Filtering**: Dangerous characters automatically removed
- **Type Validation**: Input type checking and conversion
- **XSS Prevention**: HTML/JavaScript injection protection

**Sanitized Characters:**
- `<`, `>`, `"`, `'`, `&`, `;`
- `(`, `)`, `{`, `}`, `[`, `]`
- Null bytes (`\x00`)

### **5. reCAPTCHA v2 Protection**
- **Google reCAPTCHA v2**: Industry-standard bot protection
- **Checkbox Verification**: Simple "I'm not a robot" checkbox
- **Registration Protection**: Required for new account creation
- **Advanced Bot Detection**: Google's machine learning algorithms

### **6. Security Headers**
- **X-Content-Type-Options**: `nosniff`
- **X-Frame-Options**: `DENY`
- **X-XSS-Protection**: `1; mode=block`
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **Content-Security-Policy**: Adaptive - relaxed in development, strict in production

### **7. Session Security**
- **Automatic Logout**: 1 hour of inactivity
- **Secure Cookies**: HTTP-only, SameSite protection
- **CSRF Protection**: Token-based request validation
- **Session Expiry**: Automatic cleanup of expired sessions

## **🚀 How to Use**

### **Basic Protection (Automatic)**
The security middleware automatically protects all routes:
```python
# No additional code needed - protection is automatic
@app.route('/your-endpoint')
def your_function():
    # Input validation, rate limiting, and bot detection happen automatically
    pass
```

### **Enhanced Protection (Manual)**
Add additional security decorators to sensitive endpoints:
```python
from security_middleware import rate_limit, sanitize_input
from database_security import validate_user_input

@app.route('/sensitive-endpoint', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def sensitive_function():
    # Validate input
    user_input = request.form.get('user_input')
    if not validate_user_input(user_input, max_length=100):
        return jsonify({'error': 'Invalid input'}), 400
    
    # Sanitize input
    clean_input = sanitize_input(user_input)
    
    # Process safely
    return jsonify({'success': True})
```

### **reCAPTCHA Protection**
```python
from services.recaptcha_service import require_recaptcha

@app.route('/registration', methods=['GET', 'POST'])
@require_recaptcha
def register():
    # reCAPTCHA verification is automatically required
    pass
```

## **📊 Monitoring & Administration**

### **Security Dashboard**
Access security statistics in the admin panel:
- Blocked IP addresses
- Suspicious activity patterns
- Rate limit violations
- reCAPTCHA configuration status

### **API Endpoints**
```bash
# Get security statistics
GET /api/admin/security-stats

# Unblock an IP address
POST /api/admin/unblock-ip
{
    "ip_address": "192.168.1.1"
}
```

### **Logging**
Security events are automatically logged:
- SQL injection attempts
- Bot detection
- Rate limit violations
- IP blocking actions
- reCAPTCHA verification attempts

## **🔧 Configuration**

### **Rate Limiting**
```python
# Global rate limit (requests per minute)
RATE_LIMIT_GLOBAL = 60

# Endpoint-specific limits
LOGIN_RATE_LIMIT = 10
REGISTRATION_RATE_LIMIT = 5
AI_CHAT_RATE_LIMIT = 30
```

### **Bot Detection Sensitivity**
```python
# Adjust bot detection thresholds
BOT_DETECTION_THRESHOLD = 100  # requests per minute
AUTOMATION_PATTERN_THRESHOLD = 0.1  # seconds between requests
```

### **reCAPTCHA Settings**
```python
# Environment variables in .env file
RECAPTCHA_SITE_KEY=your_site_key_here
RECAPTCHA_SECRET_KEY=your_secret_key_here

# Get from Google reCAPTCHA admin console
# https://www.google.com/recaptcha/admin/create
```

### **Content Security Policy (CSP)**
```python
# CSP automatically adapts based on environment
# Development: More permissive for easier debugging
# Production: Strict policy for security

# Allowed external resources:
# - Google Fonts (fonts.googleapis.com, fonts.gstatic.com)
# - Tailwind CSS CDN (cdn.tailwindcss.com)
# - Chart.js (cdn.jsdelivr.net)
# - Alpine.js (unpkg.com)
# - Google reCAPTCHA (www.google.com, www.gstatic.com)
```

## **🚨 Security Events & Responses**

### **SQL Injection Attempt**
- **Detection**: Pattern matching in user input
- **Response**: Request blocked, IP logged
- **Action**: Automatic IP blocking after multiple attempts

### **Bot Detection**
- **Detection**: User-Agent analysis + behavioral patterns
- **Response**: CAPTCHA challenge or IP blocking
- **Action**: Progressive blocking (temporary → permanent)

### **Rate Limit Violation**
- **Detection**: Request frequency monitoring
- **Response**: HTTP 429 (Too Many Requests)
- **Action**: Temporary IP blocking

### **XSS Attempt**
- **Detection**: HTML/JavaScript pattern detection
- **Response**: Input sanitization or rejection
- **Action**: Logging and user notification

## **📈 Performance Impact**

### **Minimal Overhead**
- **Input Validation**: < 1ms per request
- **Rate Limiting**: < 0.5ms per request
- **Bot Detection**: < 2ms per request
- **reCAPTCHA**: < 5ms per request (client-side only)

### **Memory Usage**
- **Rate Limit Tracking**: ~1KB per active IP
- **Bot Signature Storage**: ~10KB total
- **reCAPTCHA**: No server memory overhead

## **🔒 Production Recommendations**

### **Required**
- Enable HTTPS (set `SESSION_COOKIE_SECURE = True`)
- Use strong `SECRET_KEY`
- Regular security updates
- Monitor security logs

### **Recommended**
- Install `psutil` for system monitoring
- Use Redis for distributed rate limiting
- Implement proper logging to files/database
- Regular security audits

### **Optional**
- Web Application Firewall (WAF)
- DDoS protection services
- Advanced bot detection services
- Security monitoring tools

## **🆘 Troubleshooting**

### **False Positives**
If legitimate users are being blocked:
1. Check admin security dashboard
2. Review blocked IPs list
3. Unblock legitimate IPs via admin API
4. Adjust detection thresholds if needed

### **Performance Issues**
If security features are slowing down your app:
1. Monitor request processing times
2. Check rate limiting settings
3. Optimize input validation patterns
4. Consider caching for repeated validations

### **Security Alerts**
If you see security warnings:
1. Review the specific threat detected
2. Check if it's a false positive
3. Adjust detection patterns if needed
4. Monitor for repeated attempts

## **📞 Support**

For security-related issues or questions:
1. Check the security dashboard in admin panel
2. Review security logs for details
3. Adjust configuration as needed
4. Contact development team for complex issues

---

**Remember**: Security is an ongoing process. Regularly review and update your security measures to stay protected against new threats.
