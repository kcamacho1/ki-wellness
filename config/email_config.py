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
    
    # Application settings with auto-detection
    @staticmethod
    def _get_app_url():
        """Auto-detect application URL based on environment"""
        # First try explicit environment variable
        app_url = os.getenv('APP_URL')
        if app_url:
            return app_url
        
        # Auto-detect based on common environment indicators
        # Check for Render.com environment
        render_service = os.getenv('RENDER_SERVICE_NAME')
        if render_service:
            return 'https://kiwellness.org'
        
        # Check for production indicators
        environment = os.getenv('ENVIRONMENT', '').lower()
        if environment in ['production', 'prod']:
            return 'https://kiwellness.org'
        
        # Check if we're using PostgreSQL (production indicator)
        database_url = os.getenv('DATABASE_URL', '')
        if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
            return 'https://kiwellness.org'
        
        # Default to localhost for development
        return 'http://localhost:5000'
    
    APP_URL = _get_app_url()
    
    # Password reset email configuration
    PASSWORD_RESET_SUBJECT = 'Reset Your Ki Wellness Password'
    
    # Email verification configuration
    EMAIL_VERIFICATION_SUBJECT = 'Verify Your Ki Wellness Email Address'
    PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 24
    
    @classmethod
    def get_reset_link(cls, token):
        """Generate password reset link"""
        app_url = cls._get_app_url()
        return urljoin(app_url, f'/reset-password/{token}')
    
    @classmethod
    def get_verification_link(cls, token):
        """Generate email verification link"""
        app_url = cls._get_app_url()
        return urljoin(app_url, f'/verify-email/{token}')
    
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
