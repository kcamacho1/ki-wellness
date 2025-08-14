# Google OAuth Setup for YouTube API

## Overview

This guide explains how to set up Google OAuth credentials to enable YouTube API integration in the exercise page.

## Prerequisites

1. A Google account
2. Access to Google Cloud Console
3. Basic understanding of OAuth 2.0

## Step-by-Step Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "Ki Wellness YouTube Integration")
4. Click "Create"

### 2. Enable YouTube Data API v3

1. In your project, go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on it and click "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: "Ki Wellness"
   - User support email: Your email
   - Developer contact information: Your email
   - Save and continue through the steps

4. Create OAuth client ID:
   - Application type: Web application
   - Name: "Ki Wellness Web Client"
   - Authorized redirect URIs:
     - `http://localhost:5001/youtube/oauth2callback` (for development)
     - `https://yourdomain.com/youtube/oauth2callback` (for production)
   - Click "Create"

### 4. Get Your Credentials

After creating the OAuth client ID, you'll get:
- Client ID
- Client Secret

### 5. Configure Environment Variables

Add these to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5001/youtube/oauth2callback
```

### 6. Test the Integration

1. Start your Flask application
2. Navigate to `/exercise`
3. Click "Connect YouTube"
4. Complete the OAuth flow
5. Verify that your playlists load

## Security Considerations

### Development
- Use localhost redirect URIs
- Keep credentials in `.env` file (not in version control)
- Use test accounts for development

### Production
- Use HTTPS redirect URIs
- Store credentials securely
- Implement proper session management
- Consider storing tokens in database instead of session

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Ensure the redirect URI in Google Console matches your environment variable
   - Check for trailing slashes or protocol mismatches

2. **"Access blocked"**
   - Add your email to the OAuth consent screen test users
   - Verify the app is not in restricted mode

3. **"API not enabled"**
   - Ensure YouTube Data API v3 is enabled in your Google Cloud project

4. **"Quota exceeded"**
   - YouTube API has daily quotas
   - Consider implementing caching for playlist data

### Debug Mode

Enable debug logging by setting:
```env
FLASK_DEBUG=1
```

Check the console for detailed error messages.

## API Quotas and Limits

- YouTube Data API v3 has daily quotas
- Default quota: 10,000 units per day
- Playlist operations: ~1-5 units per request
- Consider implementing caching to reduce API calls

## Next Steps

Once OAuth is working:

1. Implement token refresh logic
2. Add error handling for API failures
3. Consider caching playlist data
4. Add user preference storage
5. Implement rate limiting

## Support

For issues with:
- **Google OAuth**: Check Google Cloud Console documentation
- **YouTube API**: Check YouTube Data API documentation
- **Flask Integration**: Check the application logs and this documentation
