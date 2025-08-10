# Render PostgreSQL Database Setup Guide

## Step 1: Create PostgreSQL Database

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click "New +" → "PostgreSQL"
3. Configure:
   - **Name**: `ki-wellness-db`
   - **Database**: `ki_wellness`
   - **User**: `ki_wellness_user`
   - **Region**: Choose closest to your users
   - **PostgreSQL Version**: Latest

## Step 2: Get Database URL

1. Click on your database in dashboard
2. Go to "Connections" tab
3. Copy "External Database URL" or "Internal Database URL"

## Step 3: Set Environment Variables

1. Go to your web service
2. Click "Environment" tab
3. Add:
   ```
   DATABASE_URL=postgres://username:password@host:port/ki_wellness
   FLASK_ENV=production
   SECRET_KEY=your-secret-key
   SITE_KEY=your-turnstile-site-key
   SECRET_KEY=your-turnstile-secret-key
   ```

## Step 4: Deploy

1. Push your code to GitHub
2. Render will automatically deploy
3. Check logs for any issues

## Troubleshooting

- **Connection Errors**: Ensure database and web service are in same region
- **Sleep Issues**: Free tier databases sleep after inactivity
- **Migration**: Run `python init_db_render.py` if needed
