# Google OAuth Integration Setup Guide

This guide explains how to set up Google OAuth integration for the Ki Wellness application.

## Overview

The Ki Wellness application now supports Google OAuth for user authentication. This allows users to:
- Sign in with their Google account
- Create new accounts using Google OAuth
- Automatically have their email verified (Google emails are pre-verified)
- Have their basic profile information populated from Google

## Features Implemented

### ✅ Backend Features
- Google OAuth routes (`/login/google` and `/login/google/authorized`)
- OAuth user creation and login logic
- Integration with existing user profile system
- Admin control over new account creation
- OAuth configuration display in admin dashboard

### ✅ Frontend Features
- Google OAuth buttons on login and register pages
- OAuth status display in admin dashboard
- Proper error handling and user feedback

### ✅ Database Features
- OAuth fields added to users table:
  - `oauth_provider` - OAuth provider (e.g., 'google')
  - `oauth_id` - OAuth provider's user ID
  - `oauth_email` - Email from OAuth provider
  - `oauth_name` - Name from OAuth provider
  - `oauth_picture` - Profile picture URL from OAuth provider

## Setup Instructions

### 1. Google Cloud Console Setup

1. **Go to Google Cloud Console**
   - Visit: https://console.developers.google.com
   - Sign in with your Google account

2. **Create or Select a Project**
   - Create a new project or select an existing one
   - Note the Project ID for later use

3. **Enable Google+ API**
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" or "Google Identity"
   - Click on it and press "Enable"

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application" as the application type

5. **Configure OAuth Consent Screen**
   - If prompted, configure the OAuth consent screen
   - Add your application name: "Ki Wellness"
   - Add your domain to authorized domains
   - Add scopes: `email` and `profile`

6. **Set Up OAuth 2.0 Client**
   - **Authorized JavaScript origins:**
     - `http://localhost:5001` (for development)
     - `https://yourdomain.com` (for production)
   
   - **Authorized redirect URIs:**
     - `http://localhost:5001/login/google/authorized` (for development)
     - `https://yourdomain.com/login/google/authorized` (for production)

7. **Get Your Credentials**
   - After creating, you'll get a Client ID and Client Secret
   - Save these securely - you'll need them for the next step

### 2. Environment Configuration

Add the following environment variables to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### 3. Database Migration

The OAuth fields have already been added to the database. If you need to run the migration manually:

```bash
python cleanup_backup/migrate_oauth_fields.py
```

### 4. Dependencies

Ensure the required dependencies are installed:

```bash
pip install Flask-OAuthlib
```

## How It Works

### User Flow

1. **New User (OAuth Registration)**
   - User clicks "Continue with Google" on login/register page
   - Redirected to Google OAuth consent screen
   - User authorizes the application
   - Google redirects back to `/login/google/authorized`
   - System creates new user account with Google data
   - User is automatically logged in and redirected to dashboard

2. **Existing User (OAuth Login)**
   - User clicks "Continue with Google" on login page
   - Redirected to Google OAuth consent screen
   - User authorizes the application
   - Google redirects back to `/login/google/authorized`
   - System finds existing user by OAuth ID
   - User is logged in and redirected to dashboard

### Admin Control

The admin dashboard includes:
- **Account Creation Control**: Enable/disable new account creation (affects both regular and OAuth registration)
- **OAuth Configuration Display**: Shows OAuth status and setup instructions
- **OAuth Status Monitoring**: Displays whether OAuth is properly configured

## Security Features

### ✅ Implemented Security Measures
- OAuth tokens are validated with Google
- User data is securely stored in database
- Admin control over new account creation
- Proper session management for OAuth users
- Email verification is automatic for Google accounts

### 🔒 Security Best Practices
- Never expose OAuth credentials in client-side code
- Use HTTPS in production
- Regularly rotate OAuth credentials
- Monitor OAuth usage in admin dashboard
- Implement rate limiting on OAuth routes

## Testing

### Manual Testing
1. Set up Google OAuth credentials
2. Configure environment variables
3. Test OAuth login flow
4. Verify user creation and profile data
5. Test admin dashboard OAuth display

### Automated Testing
Run the OAuth integration test:

```bash
python tests/test_oauth_integration.py
```

## Troubleshooting

### Common Issues

1. **"OAuth is not available" error**
   - Ensure Flask-OAuthlib is installed
   - Check that OAuth credentials are properly configured

2. **"Invalid redirect URI" error**
   - Verify the redirect URI in Google Cloud Console matches your application URL
   - Check that the URI is exactly: `http://localhost:5001/login/google/authorized`

3. **"Access denied" error**
   - Check that Google+ API is enabled
   - Verify OAuth consent screen is configured
   - Ensure scopes include `email` and `profile`

4. **"New account creation is disabled" error**
   - Admin has disabled new account creation
   - Check admin dashboard to enable it

### Debug Mode

To enable OAuth debugging, add to your `.env` file:

```env
FLASK_DEBUG=1
OAUTH_DEBUG=1
```

## Production Deployment

### Environment Variables
For production, ensure these are set:

```env
# Production OAuth Configuration
GOOGLE_CLIENT_ID=your_production_client_id
GOOGLE_CLIENT_SECRET=your_production_client_secret

# Security
FLASK_ENV=production
SECRET_KEY=your_secure_secret_key
```

### Google Cloud Console
1. Add your production domain to authorized origins
2. Add production redirect URI
3. Configure OAuth consent screen for production
4. Set up proper domain verification

### SSL/HTTPS
- OAuth requires HTTPS in production
- Ensure your domain has valid SSL certificate
- Update redirect URIs to use HTTPS

## Monitoring

### Admin Dashboard
The admin dashboard shows:
- OAuth availability status
- Client ID and secret configuration status
- Setup instructions for administrators

### Logs
Monitor application logs for:
- OAuth authentication attempts
- User creation via OAuth
- OAuth errors and failures

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify Google Cloud Console configuration
3. Check application logs for error messages
4. Ensure all environment variables are set correctly

## Future Enhancements

Potential future OAuth features:
- Additional OAuth providers (Facebook, GitHub, etc.)
- OAuth account linking for existing users
- Advanced OAuth scopes for additional data
- OAuth user profile synchronization
