"""
Modular route registry for Ki Wellness
Allows dynamic registration of routes based on feature flags
"""
from flask import Flask
from config.feature_flags import feature_flags, is_feature_enabled

class ModularRouteRegistry:
    """Registry for managing modular route registration"""
    
    def __init__(self):
        self.registered_blueprints = []
        self.failed_registrations = []
    
    def register_blueprint(self, app: Flask, blueprint, url_prefix: str = '', 
                          feature_flag: str = None, required: bool = False):
        """
        Register a blueprint with optional feature flag check
        
        Args:
            app: Flask application instance
            blueprint: Blueprint to register
            url_prefix: URL prefix for the blueprint
            feature_flag: Feature flag name to check
            required: Whether this blueprint is required (always register)
        """
        try:
            # Check if feature is enabled (skip check for required blueprints)
            if not required and feature_flag and not is_feature_enabled(feature_flag):
                print(f"⚠️ Skipping {blueprint.name} - feature '{feature_flag}' is disabled")
                return False
            
            # Register the blueprint
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            self.registered_blueprints.append({
                'name': blueprint.name,
                'feature_flag': feature_flag,
                'required': required,
                'url_prefix': url_prefix
            })
            print(f"✅ Registered {blueprint.name} blueprint")
            return True
            
        except Exception as e:
            error_msg = f"Failed to register {blueprint.name}: {str(e)}"
            self.failed_registrations.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def get_registration_summary(self) -> dict:
        """Get summary of blueprint registrations"""
        return {
            'registered': len(self.registered_blueprints),
            'failed': len(self.failed_registrations),
            'blueprints': self.registered_blueprints,
            'errors': self.failed_registrations,
            'disabled_features': feature_flags.get_disabled_features()
        }

# Global registry instance
route_registry = ModularRouteRegistry()

def register_modular_blueprints(app: Flask):
    """Register all blueprints with feature flag support"""
    
    # Import blueprints
    from .static_pages import static_bp
    from .auth import auth_bp
    from .admin import admin_bp
    from .dashboard import dashboard_bp
    from .payments import payments_bp
    from .ai import ai_bp
    from .api import api_bp
    from .food import food_bp
    from .profile import profile_bp
    from apis.recipe_api import recipe_bp
    
    # Register required blueprints (always enabled)
    route_registry.register_blueprint(app, static_bp, '', 'static_pages', required=True)
    route_registry.register_blueprint(app, auth_bp, '', 'auth', required=True)
    route_registry.register_blueprint(app, api_bp, '', None, required=True)  # API is always needed
    
    # Register optional blueprints (controlled by feature flags)
    route_registry.register_blueprint(app, dashboard_bp, '', 'dashboard')
    route_registry.register_blueprint(app, admin_bp, '', 'admin')
    route_registry.register_blueprint(app, payments_bp, '', 'payments')
    route_registry.register_blueprint(app, ai_bp, '', 'ai_coach')
    route_registry.register_blueprint(app, food_bp, '', 'nutrition_review')
    route_registry.register_blueprint(app, profile_bp, '', 'profile')
    route_registry.register_blueprint(app, recipe_bp, '', 'recipes')
    
    # Print registration summary
    summary = route_registry.get_registration_summary()
    print(f"\n📊 Route Registration Summary:")
    print(f"   ✅ Registered: {summary['registered']} blueprints")
    print(f"   ❌ Failed: {summary['failed']} blueprints")
    if summary['disabled_features']:
        print(f"   🚫 Disabled features: {', '.join(summary['disabled_features'])}")
    
    return summary
