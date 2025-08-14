# YouTube OAuth Setup Guide - Fix redirect_uri_mismatch Error

## ✅ Good News!
I can see from your Google Cloud Console that you've already added the YouTube redirect URIs:
- `http://localhost:5001/youtube/oauth2callback` ✅
- `https://kiwellness.org/youtube/oauth2callback` ✅

## ⚠️ Missing Configuration
However, you're still missing the Google OAuth login redirect URI. You need to add this to your Google Cloud Console:

### Add Google OAuth Login Redirect URI

1. **In your Google Cloud Console** (where you just added the YouTube URIs)
2. **In the "Authorized redirect URIs" section**
3. **Click "+ Add URI" and add:**
   ```
   http://localhost:5001/login/google/authorized
   ```
4. **Also add the production version:**
   ```
   https://kiwellness.org/login/google/authorized
   ```
5. **Click "Save"**

## Current Status
Your Google Cloud Console should have these 4 redirect URIs:

### Development (localhost):
- `http://localhost:5001/login/google/authorized` (Google OAuth login)
- `http://localhost:5001/youtube/oauth2callback` (YouTube API) ✅

### Production (kiwellness.org):
- `https://kiwellness.org/login/google/authorized` (Google OAuth login)
- `https://kiwellness.org/youtube/oauth2callback` (YouTube API) ✅

## Next Steps

### Step 1: Add Missing Redirect URI
Add the Google OAuth login redirect URI as shown above.

### Step 2: Set Environment Variables
Make sure you have these in your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=217684288941-your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### Step 3: Enable YouTube Data API v3
1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

### Step 4: Test the Connection
1. **Restart your Flask application**
2. **Go to the exercise page**
3. **Click "Connect YouTube"**
4. **You should now be redirected to Google OAuth consent screen**
5. **After authorization, you'll be redirected back to the exercise page**

## Why This Was Happening

Your application has **two separate OAuth flows**:

1. **Google OAuth Login** (`/login/google/authorized`)
   - Used for user authentication (sign in with Google)
   - This was missing from your Google Cloud Console

2. **YouTube API OAuth** (`/youtube/oauth2callback`)
   - Used for YouTube API access (exercise page)
   - This was already configured ✅

Both use the same Google OAuth 2.0 credentials but different redirect URIs, and both need to be configured in Google Cloud Console.

## Troubleshooting

If you still get errors after adding the missing redirect URI:

1. **Wait 5-10 minutes** - Google says settings can take time to propagate
2. **Clear browser cache and cookies** - OAuth errors are sometimes cached
3. **Check your environment variables** - Make sure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
4. **Verify YouTube Data API v3 is enabled** in Google Cloud Console

## Success Indicators

After completing the setup, you should be able to:
- ✅ Click "Connect YouTube" on the exercise page
- ✅ Be redirected to Google OAuth consent screen
- ✅ Authorize the application
- ✅ Be redirected back to the exercise page
- ✅ See your YouTube playlists loaded

Let me know if you need help with any of these steps!
