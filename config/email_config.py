"""
Email configuration for Ki Wellness application
Supports both SMTP (Outlook/Office365) and SendGrid
"""
import os
from urllib.parse import urljoin


class EmailConfig:
    """Email configuration class"""
    
    # SendGrid Configuration
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    
    # Email settings
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    FROM_NAME = os.getenv('FROM_NAME', 'Ki Wellness')
    
    # Application settings
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
    
    # Password reset email configuration
    PASSWORD_RESET_SUBJECT = 'Reset Your Ki Wellness Password'
    PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 24
    
    @classmethod
    def get_reset_link(cls, token):
        """Generate password reset link"""
        return urljoin(cls.APP_URL, f'/reset-password/{token}')
    
    @classmethod
    def is_sendgrid_configured(cls):
        """Check if SendGrid is properly configured"""
        return bool(cls.SENDGRID_API_KEY and cls.FROM_EMAIL)
    
    @classmethod
    def validate_configuration(cls):
        """Validate email configuration"""
        if cls.is_sendgrid_configured():
            return {
                'valid': True,
                'method': 'SendGrid',
                'from_email': cls.FROM_EMAIL
            }
        else:
            return {
                'valid': False,
                'method': None,
                'error': 'SendGrid not configured (missing API key or FROM_EMAIL)'
            }


# SendGrid specific settings
SENDGRID_CONFIG = {
    'base_url': 'https://api.sendgrid.com/v3/',
    'timeout': 30
}
