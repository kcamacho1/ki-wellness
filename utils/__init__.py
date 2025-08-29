# Utils module initialization
# This module contains utility functions and helpers

from .decorators import premium_required, admin_required
from .helpers import (
    get_app_setting, 
    set_app_setting, 
    check_ai_usage_limits,
    initialize_default_settings
)
# Additional utilities will be added as we continue refactoring
# from .food_utils import search_openfoodfacts_api, search_food_database  
# from .ai_utils import create_optimized_prompt, determine_topic

__all__ = [
    'premium_required',
    'admin_required', 
    'get_app_setting',
    'set_app_setting',
    'check_ai_usage_limits',
    'initialize_default_settings'
]
