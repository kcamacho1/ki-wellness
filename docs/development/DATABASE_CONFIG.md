# Database Configuration Guide

## Overview
This document outlines the database configuration for the KI Wellness application, ensuring consistency between development and production environments.

## Database Locations

### Development Environment (SQLite)
- **Primary Location**: `ki_wellness.db` (project root)
- **Fallback Locations**: 
  - `app/ki_wellness.db`
  - `app/instance/ki_wellness.db`
  - `instance/ki_wellness.db`

### Production Environment (PostgreSQL)
- **Location**: Configured via `DATABASE_URL` environment variable
- **Host**: Render.com (production)
- **Adapter**: psycopg3 (modern PostgreSQL adapter)

## Configuration Files

### 1. `config.py`
- **Purpose**: Central database configuration
- **Development**: Uses absolute path to project root database
- **Production**: Uses `DATABASE_URL` environment variable

### 2. `app/main.py`
- **Purpose**: Fallback database configuration
- **Logic**: Uses absolute path if no database URL is configured

### 3. `run.py`
- **Purpose**: Development server startup
- **Environment**: Sets `FLASK_ENV=development`

## Database Schema

### Required Tables
- `users` - User authentication and profiles
- `user_profiles` - Extended user information
- `food_cache` - Cached food nutritional data
- `food_journal` - User food journal entries
- `mood_entries` - User mood tracking
- `patterns_cache` - AI analysis patterns
- `reviews` - User reviews and testimonials
- `user_agreements` - Legal agreements acceptance
- `reminders` - User reminder settings
- `reminder_logs` - Reminder interaction logs
- `notifications` - Notification delivery logs

### Users Table Schema
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    email_notifications BOOLEAN DEFAULT TRUE,
    sms_notifications BOOLEAN DEFAULT FALSE,
    push_notifications BOOLEAN DEFAULT TRUE
);
```

## Environment Variables

### Development (.env)
```bash
# Database (optional - defaults to SQLite)
DATABASE_URL=

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# Turnstile (disabled in development)
TURNSTILE_ENABLED=false
```

### Production (Render.com)
```bash
# Database (required)
DATABASE_URL=postgresql://user:pass@host:port/db

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your_production_secret_key

# Turnstile (enabled in production)
TURNSTILE_ENABLED=true
SITE_KEY=your_turnstile_site_key
SECRET_KEY=your_turnstile_secret_key
```

## Database Initialization

### Development
1. Application starts with `python run.py`
2. `config.py` sets SQLite database path
3. `main.py` initializes database tables
4. Admin account is created automatically

### Production
1. Application starts with `gunicorn app.main:app`
2. `DATABASE_URL` environment variable is used
3. PostgreSQL connection is established
4. Tables are created if they don't exist

## Troubleshooting

### Common Issues

#### 1. Database Schema Mismatch
**Symptoms**: `OperationalError: no such column: users.email_notifications`
**Solution**: Ensure all database files have the same schema by copying the correct database

#### 2. Multiple Database Files
**Symptoms**: Inconsistent data across different database locations
**Solution**: Use absolute paths in configuration and maintain single source of truth

#### 3. Flask Instance Folder Issues
**Symptoms**: Database created in unexpected location
**Solution**: Explicitly set database path in configuration

### Verification Commands
```bash
# Check database file sizes
ls -la *.db app/*.db instance/*.db app/instance/*.db

# Verify schema consistency
sqlite3 ki_wellness.db "PRAGMA table_info(users);"
sqlite3 app/ki_wellness.db "PRAGMA table_info(users);"

# Check database path in Flask app
python -c "from app.main import app; print(app.config['SQLALCHEMY_DATABASE_URI'])"
```

## Best Practices

### 1. Single Source of Truth
- Maintain one primary database file
- Copy to fallback locations when needed
- Use absolute paths in configuration

### 2. Environment Separation
- Development: SQLite with local file
- Production: PostgreSQL with environment variable
- Never mix environments

### 3. Schema Consistency
- All database files must have identical schema
- Use migrations for schema changes
- Test schema changes in development first

### 4. Configuration Management
- Centralize database configuration in `config.py`
- Use environment variables for production secrets
- Document all configuration options

## Migration Guide

### Adding New Columns
1. Update SQLAlchemy models in `main.py`
2. Create migration script
3. Apply to all database locations
4. Verify schema consistency

### Database File Updates
1. Update primary database file
2. Copy to all fallback locations
3. Restart application
4. Verify functionality

## Security Considerations

### Development
- SQLite files should not be committed to version control
- Use strong secret keys even in development
- Disable Turnstile for local testing

### Production
- Use strong, unique secret keys
- Enable Turnstile verification
- Use environment variables for all secrets
- Regular database backups
- Monitor database access logs
