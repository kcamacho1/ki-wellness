# Routes module initialization
# This module contains all Flask blueprints for organizing routes

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

# List of all blueprints to register
BLUEPRINTS = [
    (static_bp, {'url_prefix': ''}),     # No prefix for static pages
    (auth_bp, {'url_prefix': ''}),       # No prefix for auth routes (login, register, etc.)
    (admin_bp, {'url_prefix': ''}),      # No prefix for admin routes (they have /admin in route paths)
    (dashboard_bp, {'url_prefix': ''}),  # No prefix for dashboard routes (main app pages)
    (payments_bp, {'url_prefix': ''}),   # No prefix for payment routes (they have /api or specific paths)
    (ai_bp, {'url_prefix': ''}),         # No prefix for AI routes (they have /api in route paths)
    (api_bp, {'url_prefix': ''}),        # No prefix for API routes (they have /api in route paths)
    (food_bp, {'url_prefix': ''}),       # No prefix for food routes (they have /api in route paths)
    (profile_bp, {'url_prefix': ''}),    # No prefix for profile routes (they have /api in route paths)
    (recipe_bp, {'url_prefix': ''}),     # No prefix for recipe routes (they have /api in route paths)
]

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    for blueprint, options in BLUEPRINTS:
        app.register_blueprint(blueprint, **options)
