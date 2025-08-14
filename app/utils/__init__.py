"""
Ki Wellness - Utils Package
===========================

This package contains utility functions and helper modules for the Ki Wellness application.

Author: Ki Wellness Team
Version: 2.0
"""

# Import utility modules for easy access
from .profile_utils import *
from .general_utils import *
from .dashboard_utils import *

# Export utility classes
__all__ = [
    # Utility classes
    'ValidationUtils',
    'SecurityUtils', 
    'TimeUtils',
    'ConversionUtils',
    'NotificationUtils',
    'DataQualityUtils',
    'ProfileUtils',
    'ProfileResponseBuilder',
    'handle_profile_operation',
    
    # Profile utilities
    'calculate_age',
    'validate_weight',
    'validate_height',
    'get_weight_conversion',
    'get_height_conversion',
    'format_weight',
    'format_height',
    'validate_date_of_birth',
    'get_bmi_category',
    'calculate_bmi',
    'get_activity_level_description',
    'get_goal_description',
    
    # General utilities
    'generate_verification_code',
    'send_sms_verification',
    'send_email_verification',
    'validate_phone_number',
    'validate_email',
    'sanitize_input',
    'format_currency',
    'format_percentage',
    'get_file_extension',
    'is_valid_image',
    'resize_image',
    'generate_filename',
    'log_activity',
    'get_client_ip',
    'is_mobile_device',
    'format_timestamp',
    'parse_date',
    'validate_username',
    'generate_secure_token',
    'hash_sensitive_data',
    'validate_password_strength',
    
    # Dashboard utilities
    'DashboardDataService',
    'DashboardStatsService',
    'DashboardDateService',
    'DashboardResponseService',
    'DashboardValidationService',
    'DashboardCacheService',
    'DashboardAnalyticsService'
]
