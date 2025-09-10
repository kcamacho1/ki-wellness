# 🔒 Content Security Policy (CSP) Troubleshooting Guide

## **Overview**
Content Security Policy (CSP) is a security feature that helps prevent Cross-Site Scripting (XSS) attacks by controlling which resources can be loaded by your web application.

## **Common CSP Errors**

### **1. Refused to load stylesheet**
```
Refused to load the stylesheet 'https://fonts.googleapis.com/css2?family=Quicksand...' because it violates the following Content Security Policy directive: "style-src 'self' 'unsafe-inline'".
```

**Solution**: The external stylesheet domain needs to be added to `style-src` directive.

### **2. Refused to load script**
```
Refused to load the script 'https://cdn.tailwindcss.com' because it violates the following Content Security Policy directive: "script-src 'self' 'unsafe-inline'".
```

**Solution**: The external script domain needs to be added to `script-src` directive.

### **3. Uncaught ReferenceError: tailwind is not defined**
```
Uncaught ReferenceError: tailwind is not defined
```

**Solution**: This happens when Tailwind CSS script loads but CSP blocks subsequent configuration. Add `'unsafe-eval'` to development mode or use specific domain allowlists.

## **🔧 How CSP Works in KI Wellness**

### **Development Mode**
When `app.debug = True` or `ENV = 'development'`:
```python
csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:",
    "style-src 'self' 'unsafe-inline' https:",
    "font-src 'self' https:",
    "img-src 'self' data: https:",
    "connect-src 'self' https:",
    "frame-src https:",
    "object-src 'none'",
    "base-uri 'self'"
]
```

**Benefits**:
- ✅ More permissive for easier development
- ✅ Allows all HTTPS external resources
- ✅ Enables `unsafe-eval` for dynamic scripts like Tailwind config

### **Production Mode**
When `app.debug = False` and `ENV = 'production'`:
```python
csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://www.google.com https://www.gstatic.com https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://unpkg.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https:",
    "connect-src 'self' https://www.google.com https://www.gstatic.com",
    "frame-src https://www.google.com",
    "object-src 'none'",
    "base-uri 'self'"
]
```

**Benefits**:
- 🔒 Strict security policy
- 🔒 Only allows specific trusted domains
- 🔒 Prevents most XSS attacks

## **🚨 Troubleshooting Steps**

### **Step 1: Check Browser Console**
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Look for CSP violation errors
4. Note the blocked resource URL and directive

### **Step 2: Identify the Resource Type**
- **Stylesheets**: CSS files, Google Fonts
- **Scripts**: JavaScript files, CDN libraries
- **Fonts**: Font files from Google Fonts
- **Images**: External images, data URIs
- **Frames**: iframes, embedded content

### **Step 3: Update CSP Configuration**
Edit `security_middleware.py` to add the blocked domain:

```python
# For scripts
"script-src 'self' 'unsafe-inline' https://your-new-domain.com",

# For styles
"style-src 'self' 'unsafe-inline' https://your-new-domain.com",

# For fonts
"font-src 'self' https://your-new-domain.com",
```

### **Step 4: Test Changes**
1. Restart your Flask application
2. Clear browser cache (Ctrl+F5)
3. Check if the resource loads correctly
4. Verify no new CSP errors appear

## **📋 External Resources Used**

### **Current Allowed Domains**

| Resource Type | Domain | Purpose |
|---------------|--------|---------|
| Scripts | `cdn.tailwindcss.com` | Tailwind CSS framework |
| Scripts | `www.google.com` | reCAPTCHA v2 |
| Scripts | `www.gstatic.com` | Google services |
| Scripts | `cdn.jsdelivr.net` | Chart.js library |
| Scripts | `unpkg.com` | Alpine.js framework |
| Styles | `fonts.googleapis.com` | Google Fonts CSS |
| Styles | `cdn.tailwindcss.com` | Tailwind CSS |
| Fonts | `fonts.gstatic.com` | Google Fonts files |
| Frames | `www.google.com` | reCAPTCHA iframe |

### **Adding New External Resources**

If you need to add a new external resource:

1. **Identify the domain** and resource type
2. **Add to appropriate directive** in `security_middleware.py`
3. **Test thoroughly** in both development and production
4. **Update documentation** with the new resource

## **🔧 Advanced Configuration**

### **Nonce-based CSP (Recommended for Production)**
For better security, consider using nonces instead of `'unsafe-inline'`:

```python
import secrets

# Generate nonce for each request
nonce = secrets.token_urlsafe(16)

# Use in CSP
"script-src 'self' 'nonce-{}'".format(nonce)

# Add to script tags
<script nonce="{{ nonce }}">...</script>
```

### **Report-Only Mode**
For testing CSP changes without blocking resources:

```python
response.headers['Content-Security-Policy-Report-Only'] = "; ".join(csp)
```

### **CSP Reporting**
Monitor CSP violations by adding a report endpoint:

```python
"report-uri /csp-violation-report"
```

## **🛡️ Security Best Practices**

### **Development**
- ✅ Use relaxed CSP for easier debugging
- ✅ Monitor console for violations
- ✅ Test all external resources
- ✅ Document any new additions

### **Production**
- ✅ Use strict CSP with specific domains
- ✅ Avoid `'unsafe-eval'` if possible
- ✅ Minimize `'unsafe-inline'` usage
- ✅ Regularly audit allowed domains
- ✅ Set up CSP violation reporting

### **Regular Maintenance**
- 🔄 Review CSP policy quarterly
- 🔄 Remove unused domain allowances
- 🔄 Update domains when services change
- 🔄 Monitor for new security best practices

## **🆘 Emergency Fixes**

### **Temporarily Disable CSP**
If CSP is blocking critical functionality:

```python
# In security_middleware.py, comment out CSP header
# response.headers['Content-Security-Policy'] = "; ".join(csp)
```

**⚠️ Warning**: Only use this temporarily and restore CSP as soon as possible.

### **Quick Development Fix**
For immediate development needs:

```python
# Very permissive CSP (DEVELOPMENT ONLY)
csp = ["default-src *; script-src * 'unsafe-inline' 'unsafe-eval'; style-src * 'unsafe-inline'"]
```

**⚠️ Warning**: Never use this in production.

## **📞 Getting Help**

### **Browser Tools**
- Chrome DevTools → Security tab
- Firefox DevTools → Console → Security
- Edge DevTools → Console

### **Online Validators**
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/)
- [CSP Scanner](https://cspscanner.com/)

### **Documentation**
- [MDN CSP Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Google CSP Guide](https://developers.google.com/web/fundamentals/security/csp)

---

**Remember**: CSP is a powerful security feature, but it requires careful configuration to balance security with functionality.
