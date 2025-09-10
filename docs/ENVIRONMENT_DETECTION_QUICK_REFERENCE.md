# Environment Detection System - Quick Reference

## Overview
The Ki Wellness application uses a centralized environment detection system that automatically configures all components based on the environment (development vs production).

## Quick Start

### Import and Use
```python
from config.environment import get_environment_detector, is_production, is_development

# Get environment detector
detector = get_environment_detector()

# Quick checks
if is_production():
    # Production code
    pass

if is_development():
    # Development code
    pass
```

### Get Configuration
```python
from config.environment import get_config

# Get all Flask configuration
flask_config = get_config('flask')

# Get specific sections
db_config = get_config('database')
stripe_config = get_config('stripe')
session_config = get_config('session')
security_config = get_config('security')
email_config = get_config('email')
admin_config = get_config('admin')
```

## Environment Detection Logic

1. **Explicit Environment Variable**: `FLASK_ENV` set to 'development', 'production', or 'testing'
2. **Database URL**: PostgreSQL URL indicates production, SQLite indicates development
3. **Default**: Falls back to development mode

## Configuration Sections

| Section | Development | Production | Override |
|---------|-------------|------------|----------|
| **Database** | SQLite | PostgreSQL with pooling | `DATABASE_URL` takes absolute priority |
| **Stripe** | Test keys (`sk_test_*`) | Live keys (`sk_live_*`) | Auto-detected from key format |
| **Sessions** | HTTP allowed, 24h timeout | HTTPS required, 2h timeout | Environment-based |
| **Security** | Relaxed, debug enabled | Strict, debug disabled | Environment-based |
| **Email** | localhost URL | Production URL | `APP_URL` override available |

## Database Configuration Examples

```bash
# Force PostgreSQL in development
export FLASK_ENV=development
export DATABASE_URL=postgresql://user:pass@localhost:5432/ki_wellness_dev
# Result: Uses PostgreSQL despite development mode

# Force SQLite in production
export FLASK_ENV=production  
export DATABASE_URL=sqlite:///production_backup.db
# Result: Uses SQLite despite production mode

# Use environment defaults
export FLASK_ENV=development
# No DATABASE_URL = uses SQLite (development default)
```

## Common Patterns

### Environment-Specific Code
```python
from config.environment import is_production

if is_production():
    # Production-specific logic
    app.config['DEBUG'] = False
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    # Development-specific logic
    app.config['DEBUG'] = True
    app.config['SESSION_COOKIE_SECURE'] = False
```

### Using Configuration
```python
from config.environment import get_config

# Apply configuration to Flask app
app.config.update(get_config('flask'))

# Get specific configuration
stripe_config = get_config('stripe')
if stripe_config.get('STRIPE_MODE') == 'live':
    # Production Stripe logic
    pass
```

### Component Integration
```python
from config.environment import get_environment_detector

class MyComponent:
    def __init__(self):
        self.env_detector = get_environment_detector()
        self.config = self.env_detector.get_my_config()
    
    def do_something(self):
        if self.env_detector.is_production:
            # Production logic
            pass
        else:
            # Development logic
            pass
```

## Environment Variables

### Database Configuration Priority
- `DATABASE_URL`: **Takes absolute priority** - overrides all environment-based database configuration
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
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`: Admin credentials
- `SENDGRID_API_KEY`, `FROM_EMAIL`: Email configuration

## Migration from Old Code

### Before (Manual Environment Detection)
```python
# Old way
if os.getenv('FLASK_ENV') == 'development':
    # development code

if os.getenv('DATABASE_URL') and 'postgresql' in os.getenv('DATABASE_URL'):
    # production code
```

### After (Environment Detection System)
```python
# New way
from config.environment import is_development, is_production

if is_development():
    # development code

if is_production():
    # production code
```

## Troubleshooting

### Environment Not Detected Correctly
- Check that `DATABASE_URL` is set correctly for production
- Verify `FLASK_ENV` environment variable if using explicit setting

### Configuration Not Applied
- Ensure you're using `get_config()` or the environment detector
- Check that the environment detection system is properly imported

### Backward Compatibility Issues
- Verify existing code is using the updated configuration methods
- Check that imports are updated to use the environment detection system

## Testing

### Validate Environment Detection
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

## Benefits

1. **Consistency**: All components use the same environment detection logic
2. **Maintainability**: Environment-specific settings are centralized
3. **Reliability**: Automatic detection reduces configuration errors
4. **Flexibility**: Easy to add new environment-specific configurations
5. **Testing**: Clear separation between development and production settings

## Files Updated

- `config/environment.py` - Core environment detection system
- `config/email_config.py` - Email configuration with environment detection
- `services/stripe_client.py` - Stripe client with environment detection
- `security_middleware.py` - Security middleware with environment detection
- `app.py` - Main application using environment detection system

For detailed documentation, see [ENVIRONMENT_DETECTION_SYSTEM.md](ENVIRONMENT_DETECTION_SYSTEM.md).
