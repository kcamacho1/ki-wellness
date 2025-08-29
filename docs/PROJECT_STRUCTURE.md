# Ki Wellness Project Structure

This document outlines the organized structure of the Ki Wellness application.

## Directory Organization

### Root Directory
- `app.py` - Main Flask application entry point
- `database.py` - Database models and configuration
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules

### Core Directories

#### `/services/` - Business Logic Services
- `stripe_client.py` - Payment processing with Stripe
- `analytics_service.py` - Analytics and tracking
- `openrouter_client.py` - AI chat integration
- `food_data.py` - Food database and nutrition data
- `health_resources.py` - Health resources and recommendations

#### `/apis/` - API Endpoints
- `recipe_api.py` - Recipe management API
- `__init__.py` - Package initialization

#### `/templates/` - HTML Templates
- `base.html` - Base template
- `dashboard.html` - User dashboard
- `profile.html` - User profile
- `recipes/` - Recipe-related templates
- `components/` - Reusable template components

#### `/static/` - Static Assets
- `css/` - Stylesheets
- `js/` - JavaScript files
- `assets/` - Images and other assets
  - `branding/` - Brand assets (logo, favicon, profile images)
  - `avatars/` - User avatar images
  - `stock-photos/` - Stock food images
- `uploads/` - User-uploaded content

#### `/models/` - Database Models
- Additional model definitions (if any)

### Development & Maintenance

#### `/tests/` - Test Files
- `test_*.py` - All test files for the application

#### `/scripts/` - Utility Scripts
- `scheduled_analysis.py` - Automated analysis tasks
- `create_test_user.py` - Test user creation
- `fetch_recipe_images_simple.py` - Recipe image fetching
- `update_*.py` - Template and navigation updates
- `add_avatar_*.py` - Avatar functionality
- `setup_cron.sh` - Cron job setup

#### `/migrations/` - Database Migrations
- `migrate_*.py` - All database migration scripts

#### `/routes/` - Blueprint Route Organization
- `static_pages.py` - Static pages (home, privacy, terms)
- `auth.py` - Authentication routes
- `admin.py` - Admin dashboard and management
- `dashboard.py` - Main app pages (dashboard, profile, AI coach)
- `api.py` - API endpoints for app functionality
- `payments.py` - Stripe payment and subscription routes

#### `/config/` - Configuration Files
- `render.yaml` - Render deployment configuration
- `build.sh` - Build script
- `runtime.txt` - Python runtime specification
- `.python-version` - Python version specification

#### `/docs/` - Documentation
- `README.md` - Main project documentation
- `PRODUCTION_SETUP.md` - Production deployment guide
- `DEPLOYMENT_CHECKLIST.md` - Deployment checklist
- `HUMAN_HELP_SETUP.md` - Human help integration guide
- `STRIPE_WEBHOOK_SETUP.md` - Stripe webhook configuration
- `PROJECT_STRUCTURE.md` - This file
- `DATABASE_SETUP.md` - Database configuration guide

### Data & Logs

#### `/static/` - Static Web Assets
- CSS, JavaScript, images, and other static files

#### `/logs/` - Application Logs
- `scheduled_analysis.log` - Scheduled task logs

### Database Files
- `instance/ki_wellness.db` - Local SQLite database (development)

## Import Structure

### Main Application (`app.py`)
```python
from services.openrouter_client import get_openrouter_client, generate_ai_response
from services.food_data import BASIC_FOODS, COMMON_FOODS_DB
from services.health_resources import get_relevant_resources, format_resources_for_prompt
from services.stripe_client import get_stripe_client
from services.analytics_service import analytics_service
```

### Services
Services can import from each other using relative imports:
```python
from services.analytics_service import analytics_service
from services.openrouter_client import get_openrouter_client
```

### Database Access
All modules access the database through the root `database.py`:
```python
from database import db, User, FoodLog, etc.
```

## Benefits of This Organization

1. **Separation of Concerns** - Each directory has a specific purpose
2. **Maintainability** - Easy to find and modify specific functionality
3. **Scalability** - New features can be added to appropriate directories
4. **Testing** - All tests are organized in one place
5. **Documentation** - All docs are centralized
6. **Deployment** - Configuration files are separated
7. **Development** - Scripts and utilities are organized

## File Naming Conventions

- **Services**: `*_service.py` or descriptive names like `stripe_client.py`
- **Tests**: `test_*.py`
- **Migrations**: `migrate_*.py`
- **Scripts**: Descriptive names like `create_test_user.py`
- **Routes**: Blueprint names like `auth.py`, `admin.py`
- **Configuration**: Standard names like `render.yaml`, `build.sh`

This structure makes the codebase more professional, maintainable, and easier to navigate for developers.
