# Environment Detection System

## Overview

The Ki Wellness application now uses a centralized, modular environment detection system that automatically configures all components based on whether the application is running in development, production, or testing mode.

## Key Features

- **Automatic Environment Detection**: Detects environment based on database URL, explicit environment variables, and other indicators
- **Centralized Configuration**: All environment-specific settings are managed in one place
- **Modular Design**: Easy to extend and reuse across different parts of the application
- **Backward Compatibility**: Existing code continues to work with minimal changes

## Environment Detection Logic

The system detects the environment using the following priority order:

1. **Explicit Environment Variable**: `FLASK_ENV` set to 'development', 'production', or 'testing'
2. **Database URL**: PostgreSQL URL indicates production, SQLite indicates development
3. **Default**: Falls back to development mode

## Configuration Sections

### Database Configuration
**IMPORTANT**: The `DATABASE_URL` environment variable takes absolute priority over environment detection. If `DATABASE_URL` is set, it will be used regardless of the detected environment.

- **With DATABASE_URL**: Uses the specified database URL (PostgreSQL, SQLite, or any other supported database)
- **Without DATABASE_URL**: 
  - **Production**: PostgreSQL with connection pooling and optimized settings
  - **Development/Testing**: SQLite with relaxed settings

### Stripe Configuration
- **Production**: Live Stripe keys (`sk_live_*`)
- **Development**: Test Stripe keys (`sk_test_*`)
- **Disabled**: No valid keys found

### Session Configuration
- **Production**: Secure cookies, HTTPS required, 2-hour timeout
- **Development**: HTTP allowed, 24-hour timeout for convenience

### Security Configuration
- **Production**: Strict security, CSRF enabled, debug disabled
- **Development**: Relaxed security, CSRF disabled, debug enabled

### Email Configuration
- **Production**: Uses production app URL (https://kiwellness.org)
- **Development**: Uses localhost URL (http://localhost:5000)

## Usage

### Basic Usage

```python
from config.environment import get_environment_detector, is_production, is_development

# Get environment detector
detector = get_environment_detector()

# Check environment
if detector.is_production:
    # Production-specific code
    pass
elif detector.is_development:
    # Development-specific code
    pass

# Quick checks
if is_production():
    # Production code
    pass
```

### Getting Configuration

```python
from config.environment import get_config

# Get all Flask configuration
flask_config = get_config('flask')

# Get specific configuration sections
db_config = get_config('database')
stripe_config = get_config('stripe')
session_config = get_config('session')
security_config = get_config('security')
email_config = get_config('email')
admin_config = get_config('admin')
```

### Using in Flask App

```python
from config.environment import get_environment_detector, get_config

# Initialize environment detector
env_detector = get_environment_detector()

# Apply configuration to Flask app
app.config.update(get_config('flask'))

# Print environment information
env_detector.print_environment_info()
```

## Updated Components

### 1. Main Application (`app.py`)
- Uses environment detector for all configuration
- Automatically applies appropriate settings based on environment
- Simplified configuration code

### 2. Email Configuration (`config/email_config.py`)
- Now uses environment detector for URL detection
- Maintains backward compatibility with global instance
- Automatic environment-specific URL generation

### 3. Stripe Client (`services/stripe_client.py`)
- Uses environment detector for Stripe configuration
- Automatic environment detection for live/test keys
- Consistent configuration across the application

### 4. Security Middleware (`security_middleware.py`)
- Uses environment detector for development mode detection
- Consistent environment detection across security features
- Simplified development IP handling

## Environment Variables

The system respects the following environment variables:

### Database Configuration Priority
- `DATABASE_URL`: **Takes absolute priority** - if set, overrides all environment-based database configuration
  - Can be PostgreSQL: `postgresql://user:pass@host:port/dbname`
  - Can be SQLite: `sqlite:///path/to/database.db`
  - Can be any other supported database URL
  - If not set, falls back to environment-based defaults

### Required for Production
- `SECRET_KEY`: Application secret key
- `STRIPE_SECRET_KEY`: Stripe secret key (live for production)
- `STRIPE_PUBLISHABLE_KEY`: Stripe publishable key

### Optional
- `FLASK_ENV`: Explicit environment setting
- `APP_URL`: Override automatic URL detection
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`: Admin user credentials
- `SENDGRID_API_KEY`, `FROM_EMAIL`: Email configuration

## Practical Examples

### Database Configuration Examples

```bash
# Force PostgreSQL in development environment
export FLASK_ENV=development
export DATABASE_URL=postgresql://user:pass@localhost:5432/ki_wellness_dev
# Result: Uses PostgreSQL despite being in development mode

# Force SQLite in production environment  
export FLASK_ENV=production
export DATABASE_URL=sqlite:///production_backup.db
# Result: Uses SQLite despite being in production mode

# Use environment defaults (no DATABASE_URL)
export FLASK_ENV=development
# Result: Uses SQLite (development default)

export FLASK_ENV=production
# Result: Requires DATABASE_URL or throws error
```

### Manual Database Override Scenarios

1. **Development with Production Database**: Test against production data safely
2. **Production with Development Database**: Emergency fallback scenarios
3. **Custom Database Locations**: Use specific database files or connections
4. **Testing with Different Databases**: Test database migrations and compatibility

## Benefits

1. **Consistency**: All components use the same environment detection logic
2. **Maintainability**: Environment-specific settings are centralized
3. **Reliability**: Automatic detection reduces configuration errors
4. **Flexibility**: Easy to add new environment-specific configurations
5. **Testing**: Clear separation between development and production settings
6. **Manual Override**: DATABASE_URL provides complete control over database configuration

## Migration Guide

### For Existing Code

Most existing code will continue to work without changes. The environment detection system is designed to be backward compatible.

### For New Code

Use the environment detector instead of manual environment checks:

```python
# Old way
if os.getenv('FLASK_ENV') == 'development':
    # development code

# New way
from config.environment import is_development
if is_development():
    # development code
```

### For Configuration

Use the centralized configuration instead of manual environment variable access:

```python
# Old way
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

# New way
from config.environment import get_config
app.config.update(get_config('flask'))
```

## Testing

The environment detection system has been thoroughly tested and validated. It correctly:

- Detects development mode when using SQLite
- Detects production mode when using PostgreSQL
- Applies appropriate configuration for each environment
- Maintains backward compatibility with existing code

## Future Enhancements

The modular design makes it easy to add:

- Additional environment types (staging, testing)
- New configuration sections
- Environment-specific feature flags
- Configuration validation
- Environment-specific logging levels

## Troubleshooting

### Common Issues

1. **Environment not detected correctly**: Check that `DATABASE_URL` is set correctly for production
2. **Configuration not applied**: Ensure you're using `get_config()` or the environment detector
3. **Backward compatibility issues**: Check that existing code is using the updated configuration methods

### Debug Information

Use the environment detector's print method to see current configuration:

```python
from config.environment import get_environment_detector
detector = get_environment_detector()
detector.print_environment_info()
```

This will show:
- Detected environment
- Database configuration
- Stripe mode
- Application URL
- Other key settings
