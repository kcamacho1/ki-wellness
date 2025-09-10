"""
Email configuration for Ki Wellness application
Supports both SMTP (Outlook/Office365) and SendGrid
"""
import os
from urllib.parse import urljoin
from config.environment import get_environment_detector


class EmailConfig:
    """Email configuration class"""
    
    def __init__(self):
        """Initialize email configuration using environment detection"""
        self._env_detector = get_environment_detector()
        self._config = self._env_detector.get_email_config()
    
    @property
    def SENDGRID_API_KEY(self):
        """SendGrid API Key"""
        return self._config.get('SENDGRID_API_KEY')
    
    @property
    def FROM_EMAIL(self):
        """From email address"""
        return self._config.get('FROM_EMAIL')
    
    @property
    def FROM_NAME(self):
        """From name"""
        return self._config.get('FROM_NAME', 'Ki Wellness')
    
    @property
    def APP_URL(self):
        """Application URL"""
        return self._config.get('APP_URL')
    
    @property
    def PASSWORD_RESET_SUBJECT(self):
        """Password reset email subject"""
        return self._config.get('PASSWORD_RESET_SUBJECT', 'Reset Your Ki Wellness Password')
    
    @property
    def EMAIL_VERIFICATION_SUBJECT(self):
        """Email verification subject"""
        return self._config.get('EMAIL_VERIFICATION_SUBJECT', 'Verify Your Ki Wellness Email Address')
    
    @property
    def PASSWORD_RESET_TOKEN_EXPIRY_HOURS(self):
        """Password reset token expiry hours"""
        return self._config.get('PASSWORD_RESET_TOKEN_EXPIRY_HOURS', 24)
    
    def get_reset_link(self, token):
        """Generate password reset link"""
        return urljoin(self.APP_URL, f'/reset-password/{token}')
    
    def get_verification_link(self, token):
        """Generate email verification link"""
        return urljoin(self.APP_URL, f'/verify-email/{token}')
    
    def is_sendgrid_configured(self):
        """Check if SendGrid is properly configured"""
        return bool(self.SENDGRID_API_KEY and self.FROM_EMAIL)
    
    def validate_configuration(self):
        """Validate email configuration"""
        if self.is_sendgrid_configured():
            return {
                'valid': True,
                'method': 'SendGrid',
                'from_email': self.FROM_EMAIL
            }
        else:
            return {
                'valid': False,
                'method': None,
                'error': 'SendGrid not configured (missing API key or FROM_EMAIL)'
            }


# Global email config instance for backward compatibility
_email_config = None


def get_email_config() -> EmailConfig:
    """Get the global email configuration instance"""
    global _email_config
    if _email_config is None:
        _email_config = EmailConfig()
    return _email_config


# SendGrid specific settings
SENDGRID_CONFIG = {
    'base_url': 'https://api.sendgrid.com/v3/',
    'timeout': 30
}
