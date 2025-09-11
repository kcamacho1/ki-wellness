# R2 API Security Guide

## Overview
This document outlines the security measures implemented for the R2 (Cloudflare R2) API endpoints in the Ki Wellness application.

## Security Features Implemented

### 1. Authentication & Authorization
- **Login Required**: All R2 endpoints require user authentication (`@login_required`)
- **Admin-Only Stats**: R2 statistics endpoint restricted to admin users (`@admin_required`)
- **User Context**: All operations are tied to the authenticated user

### 2. Rate Limiting
- **Upload Endpoint**: 10 requests per minute per IP
- **Pexels Search**: 10 requests per minute per IP
- **Global Rate Limiting**: 60 requests per minute per IP (via security middleware)

### 3. File Upload Security

#### File Size Validation
- **Maximum Size**: 5MB per file (optimized for food images)
- **Minimum Size**: 1KB per file
- **Client-Side Check**: File size validated before upload
- **Server-Side Check**: Double validation in R2 client

#### File Type Validation
- **Allowed Extensions**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **MIME Type Validation**: Content type verified against file extension
- **Magic Byte Validation**: File signatures checked to prevent spoofing

#### Content Security
- **Executable Detection**: Scans for script tags, executable signatures
- **Malicious Pattern Detection**: Blocks files containing dangerous patterns
- **WebP Validation**: Special validation for WebP format
- **Food Image Validation**: Ensures uploaded images are food-related
- **Dimension Validation**: Checks image dimensions (100x100 to 4000x4000 pixels)
- **Aspect Ratio Validation**: Prevents extremely wide or tall images

### 4. Path Traversal Protection
- **Folder Sanitization**: User-provided folder names sanitized
- **Character Filtering**: Removes dangerous characters (`..`, `/`, `\`)
- **Length Limits**: Folder names limited to 50 characters

### 5. Input Sanitization
- **Recipe Data**: All recipe data sanitized before Pexels API calls
- **SQL Injection Prevention**: Input validation against SQL injection patterns
- **XSS Prevention**: Dangerous characters removed from user inputs

### 6. CSRF Protection
- **Token Validation**: CSRF tokens required for file uploads
- **Form Protection**: All forms include CSRF tokens

### 7. Logging & Monitoring
- **Upload Logging**: All successful uploads logged with user ID
- **Error Logging**: Failed uploads and security violations logged
- **Rate Limit Tracking**: IP-based rate limiting with automatic blocking

## API Endpoints Security

### `/api/r2/upload` (POST)
**Security Level**: High
- ✅ Authentication required
- ✅ Rate limited (10/min)
- ✅ CSRF protection
- ✅ File validation
- ✅ Path traversal protection
- ✅ Content scanning
- ✅ Size limits

### `/api/r2/stats` (GET)
**Security Level**: High
- ✅ Authentication required
- ✅ Admin only
- ✅ No sensitive data exposure

### Pexels API Endpoints (REMOVED)
**Status**: Removed from main application
- ✅ Image uploads now required for all recipes
- ✅ Pexels API only used in separate script
- ✅ No longer exposed in main application

## Security Best Practices

### 1. File Upload Guidelines
```python
# Always validate file content
if not validate_file_content(file_data, filename):
    return error_response

# Sanitize folder names
folder = sanitize_folder_name(user_folder)

# Check file size
if len(file_data) > MAX_FILE_SIZE:
    return error_response
```

### 2. Input Validation
```python
# Sanitize all user inputs
recipe = sanitize_recipe_data(recipe_data)

# Validate file extensions
if file_ext not in ALLOWED_EXTENSIONS:
    return error_response
```

### 3. Error Handling
```python
# Log security violations
current_app.logger.warning(f"Security violation: {details}")

# Don't expose internal errors
return jsonify({'error': 'Upload failed'}), 500
```

## Security Monitoring

### 1. Log Analysis
Monitor logs for:
- Failed upload attempts
- Rate limit violations
- File validation failures
- Unusual upload patterns

### 2. Metrics to Track
- Upload success/failure rates
- File type distribution
- User upload patterns
- Rate limit hits

### 3. Alerts
Set up alerts for:
- High rate limit violations
- Multiple failed uploads from same IP
- Unusual file types being uploaded
- Admin endpoint access

## Environment Variables

### Required for Security
```bash
# R2 Configuration
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=your_bucket_name
R2_PUBLIC_URL=https://your-domain.com

# Pexels API (only used in separate script)
# PEXELS_API_KEY=your_pexels_key

# Security
SECRET_KEY=your_secret_key
```

## Security Checklist

### Before Deployment
- [ ] All environment variables set
- [ ] R2 credentials configured
- [ ] Rate limits tested
- [ ] File validation tested
- [ ] CSRF tokens working
- [ ] Admin endpoints protected

### Regular Maintenance
- [ ] Review upload logs weekly
- [ ] Monitor rate limit violations
- [ ] Check for unusual patterns
- [ ] Update security dependencies
- [ ] Review access logs

## Incident Response

### If Security Breach Detected
1. **Immediate**: Block suspicious IP addresses
2. **Investigate**: Review logs for attack patterns
3. **Contain**: Disable affected endpoints if necessary
4. **Report**: Document incident and response
5. **Prevent**: Update security measures

### Emergency Contacts
- **Security Team**: [Contact Information]
- **System Admin**: [Contact Information]
- **Legal Team**: [Contact Information]

## Compliance

### Data Protection
- User uploads are stored securely in R2
- No personal data in file metadata
- Automatic cleanup of failed uploads

### Privacy
- Images are publicly accessible via CDN
- No tracking of individual file access
- User consent required for uploads

## Updates

### Version History
- **v1.0**: Initial security implementation
- **v1.1**: Added file content validation
- **v1.2**: Enhanced input sanitization
- **v1.3**: Added CSRF protection

### Future Enhancements
- [ ] Virus scanning integration
- [ ] Image content analysis
- [ ] Advanced threat detection
- [ ] Automated security testing

---

**Last Updated**: December 2024  
**Security Level**: High  
**Review Frequency**: Monthly
