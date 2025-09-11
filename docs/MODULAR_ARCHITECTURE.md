# Ki Wellness - Modular Architecture Guide

## Overview

Ki Wellness has been restructured into a modular architecture that allows individual pages and features to be enabled/disabled without affecting other parts of the application. This makes the app more maintainable, testable, and allows for gradual rollouts or temporary feature disabling.

## Architecture Components

### 1. Feature Flags System

The feature flags system (`config/feature_flags.py`) controls which features are enabled:

```python
from config.feature_flags import is_feature_enabled

# Check if a feature is enabled
if is_feature_enabled('recipes'):
    # Show recipes functionality
    pass
```

**Available Features:**
- `auth` - Authentication system (always enabled)
- `dashboard` - Main dashboard
- `recipes` - Recipe management with community rating system
- `ai_coach` - AI coaching features
- `admin` - Admin panel
- `payments` - Payment processing
- `barcode_scanner` - Barcode scanning
- `nutrition_review` - Nutrition review
- `analytics` - Analytics features
- `support` - Support pages
- `human_help` - Human help features

### 2. Recipe Rating System Architecture

The recipe system includes a community-focused rating architecture:

**Database Schema:**
- `Recipe.average_rating` - Stored average rating for performance
- `Recipe.rating_count` - Number of users who rated the recipe
- `RecipeRating` - Individual user ratings (1-5 stars)

**Key Features:**
- Community-first approach (all recipes are public)
- Real-time rating updates
- Contributor recognition system
- Permission-based editing (owners only)

**API Endpoints:**
- `POST /api/recipes/<id>/rate` - Submit/update rating
- `GET /api/recipes/<id>` - Get recipe with rating info
- All recipe endpoints include `contributor` and `is_owner` fields

### 3. Modular Template Structure

Templates are now organized by feature:

```
templates/
├── layouts/           # Base templates for different page types
│   ├── auth_base.html
│   ├── dashboard_base.html
│   ├── admin_base.html
│   ├── recipes_base.html
│   └── ai_base.html
├── pages/            # Page-specific templates
│   ├── auth/         # Authentication pages
│   ├── dashboard/    # Dashboard pages
│   ├── admin/        # Admin pages
│   ├── ai/           # AI features
│   ├── recipes/      # Recipe pages
│   └── static/       # Static content pages
└── components/       # Reusable components
```

### 4. Modular Route Registration

Routes are registered conditionally based on feature flags (`routes/modular_registry.py`):

```python
# Required routes (always enabled)
route_registry.register_blueprint(app, auth_bp, '', 'auth', required=True)

# Optional routes (controlled by feature flags)
route_registry.register_blueprint(app, recipe_bp, '', 'recipes')
```

## Usage Examples

### Disabling a Feature via Environment Variable

```bash
# Disable recipes feature
export FEATURE_RECIPES=false

# Disable admin panel
export FEATURE_ADMIN=false

# Disable AI coach
export FEATURE_AI_COACH=false
```

### Disabling a Feature Programmatically

```python
from config.feature_flags import feature_flags

# Disable recipes feature
feature_flags.disable_feature('recipes')

# Re-enable recipes feature
feature_flags.enable_feature('recipes')
```

### Checking Feature Status

```python
from config.feature_flags import is_feature_enabled, get_feature_status

# Check individual feature
if is_feature_enabled('recipes'):
    # Show recipes UI
    pass

# Get all feature status
status = get_feature_status()
print(status)
```

## Benefits

### 1. **Independent Development**
- Teams can work on different features without conflicts
- Features can be developed and tested in isolation
- Easier to maintain and debug individual components

### 2. **Gradual Rollouts**
- Enable features for specific user groups
- A/B testing capabilities
- Safe feature deployment

### 3. **Emergency Disabling**
- Quickly disable problematic features
- Maintenance mode for specific features
- Reduce system load during high traffic

### 4. **Resource Optimization**
- Only load JavaScript/CSS for enabled features
- Reduce bundle size
- Improve page load times

### 5. **Testing & Development**
- Test individual features in isolation
- Mock disabled features during development
- Easier integration testing

## Template Usage

### Using Page-Specific Base Templates

```html
<!-- For authentication pages -->
{% extends "layouts/auth_base.html" %}

<!-- For dashboard pages -->
{% extends "layouts/dashboard_base.html" %}

<!-- For recipe pages -->
{% extends "layouts/recipes_base.html" %}
```

### Page-Specific Resources

Each base template loads only the resources needed for that page type:

- **auth_base.html**: Auth-specific styling
- **dashboard_base.html**: Dashboard JS modules, Chart.js, food-journal.css
- **recipes_base.html**: Recipe-specific styling
- **admin_base.html**: Admin-specific styling and JS
- **ai_base.html**: AI chat styling and JS

## Environment Variables

Set these environment variables to control features:

```bash
# Feature flags (true/false)
FEATURE_RECIPES=true
FEATURE_AI_COACH=true
FEATURE_ADMIN=true
FEATURE_PAYMENTS=true
FEATURE_BARCODE_SCANNER=true
FEATURE_NUTRITION_REVIEW=true
FEATURE_ANALYTICS=true
FEATURE_SUPPORT=true
FEATURE_HUMAN_HELP=true
```

## Testing Modularity

Run the modularity test suite:

```bash
python test_modularity.py
```

This tests:
- Feature flag functionality
- Environment variable integration
- Template structure organization
- Route registration system

## Migration Notes

### For Developers

1. **Template Updates**: All templates now use page-specific base templates
2. **Route Updates**: Routes now use the modular registration system
3. **Resource Loading**: JavaScript and CSS are loaded per-page-type
4. **Feature Checks**: Use `is_feature_enabled()` to check feature availability

### For Deployment

1. **Environment Variables**: Set feature flags in production environment
2. **Monitoring**: Monitor which features are enabled/disabled
3. **Rollback**: Use feature flags for quick rollbacks
4. **Performance**: Disabled features don't load resources

## Best Practices

1. **Always check feature flags** before showing feature-specific UI
2. **Use appropriate base templates** for new pages
3. **Test with features disabled** to ensure graceful degradation
4. **Document new features** in the feature flags system
5. **Use environment variables** for production feature control

## Troubleshooting

### Feature Not Loading
- Check if feature flag is enabled
- Verify environment variable is set correctly
- Check route registration in logs

### Template Not Found
- Verify template is in correct directory structure
- Check if using correct base template
- Ensure route is using correct template path

### Resources Not Loading
- Check if page is using correct base template
- Verify feature-specific resources are in base template
- Check browser console for 404 errors

## Future Enhancements

1. **User-specific feature flags** - Enable features per user
2. **A/B testing integration** - Built-in A/B testing
3. **Feature analytics** - Track feature usage
4. **Dynamic feature loading** - Load features on demand
5. **Feature dependencies** - Handle feature interdependencies
