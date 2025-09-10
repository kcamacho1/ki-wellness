#!/usr/bin/env python3
"""
Environment Detection and Configuration Module for Ki Wellness
Provides centralized environment detection and configuration management

Database Configuration:
- DATABASE_URL environment variable takes absolute priority over environment detection
- If DATABASE_URL is set, it will be used regardless of detected environment
- If DATABASE_URL is not set, falls back to environment-based defaults
"""

import os
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class EnvironmentDetector:
    """
    Centralized environment detection and configuration management
    """
    
    def __init__(self):
        self._environment = None
        self._config_cache = {}
        self._detect_environment()
    
    def _detect_environment(self) -> Environment:
        """
        Detect the current environment based on various indicators
        """
        if self._environment is not None:
            return self._environment
        
        # Check explicit environment variable first
        explicit_env = os.getenv('FLASK_ENV', '').lower()
        if explicit_env in ['development', 'dev']:
            self._environment = Environment.DEVELOPMENT
        elif explicit_env in ['production', 'prod']:
            self._environment = Environment.PRODUCTION
        elif explicit_env in ['testing', 'test']:
            self._environment = Environment.TESTING
        
        # Auto-detect based on database URL (primary indicator)
        elif self._is_production_database():
            self._environment = Environment.PRODUCTION
        else:
            self._environment = Environment.DEVELOPMENT
        
        return self._environment
    
    def _is_production_database(self) -> bool:
        """Check if using production database (PostgreSQL)"""
        db_url = os.getenv('DATABASE_URL', '')
        return bool(db_url and ('postgresql://' in db_url or 'postgres://' in db_url))
    
    @property
    def environment(self) -> Environment:
        """Get current environment"""
        return self._detect_environment()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing"""
        return self.environment == Environment.TESTING
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration - DATABASE_URL takes priority over environment detection
        """
        if 'database_config' in self._config_cache:
            return self._config_cache['database_config']
        
        config = {}
        db_url = os.getenv('DATABASE_URL')
        
        # DATABASE_URL takes absolute priority - if set, use it regardless of environment
        if db_url:
            # Handle postgres:// to postgresql:// conversion
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
            # Check if it's a PostgreSQL URL
            if 'postgresql://' in db_url or 'postgres://' in db_url:
                # Try to use the best available driver
                try:
                    import psycopg2
                    print("✅ Using psycopg2 (maximum compatibility)")
                except ImportError:
                    try:
                        import psycopg
                        print("✅ Using psycopg3 (Python 3.13+ compatible)")
                        if '+psycopg' not in db_url:
                            db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
                    except ImportError:
                        print("⚠️ No PostgreSQL driver found - falling back to SQLite")
                        db_url = 'sqlite:///ki_wellness_dev.db'
                
                config = {
                    'SQLALCHEMY_DATABASE_URI': db_url,
                    'SQLALCHEMY_ENGINE_OPTIONS': {
                        'connect_args': {
                            'connect_timeout': 10
                        },
                        'pool_timeout': 20,
                        'pool_recycle': 3600,
                        'pool_pre_ping': True
                    }
                }
                print("✅ Database configured with PostgreSQL (from DATABASE_URL)")
            else:
                # Assume it's a SQLite URL or other database
                config = {
                    'SQLALCHEMY_DATABASE_URI': db_url
                }
                print(f"✅ Database configured with custom URL: {db_url}")
        else:
            # No DATABASE_URL set - fall back to environment-based defaults
            if self.is_production:
                raise ValueError("DATABASE_URL environment variable is required for production")
            else:
                # Development/Testing - SQLite
                db_name = 'ki_wellness_test.db' if self.is_testing else 'ki_wellness_dev.db'
                config = {
                    'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_name}'
                }
                print(f"✅ {'Testing' if self.is_testing else 'Development'} database configured with SQLite (default)")
        
        config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self._config_cache['database_config'] = config
        return config
    
    def get_stripe_config(self) -> Dict[str, Any]:
        """
        Get Stripe configuration based on environment
        """
        if 'stripe_config' in self._config_cache:
            return self._config_cache['stripe_config']
        
        stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
        stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        # Auto-detect Stripe environment
        stripe_is_live = bool(stripe_secret_key and stripe_secret_key.startswith('sk_live_'))
        stripe_is_test = bool(stripe_secret_key and stripe_secret_key.startswith('sk_test_'))
        
        if stripe_is_live:
            print("✅ Stripe LIVE mode detected - Production payments enabled")
            stripe_mode = 'live'
            stripe_env = 'production'
        elif stripe_is_test:
            print("✅ Stripe TEST mode detected - Development payments enabled")
            stripe_mode = 'test'
            stripe_env = 'development'
        else:
            print("⚠️ No valid Stripe keys found - Payment features disabled")
            stripe_mode = 'disabled'
            stripe_env = 'disabled'
        
        config = {
            'STRIPE_SECRET_KEY': stripe_secret_key,
            'STRIPE_PUBLISHABLE_KEY': stripe_publishable_key,
            'STRIPE_WEBHOOK_SECRET': stripe_webhook_secret,
            'STRIPE_MODE': stripe_mode,
            'STRIPE_ENV': stripe_env
        }
        
        self._config_cache['stripe_config'] = config
        return config
    
    def get_session_config(self) -> Dict[str, Any]:
        """
        Get session configuration based on environment
        """
        if 'session_config' in self._config_cache:
            return self._config_cache['session_config']
        
        from datetime import timedelta
        
        if self.is_production:
            # Production - Secure session settings
            config = {
                'PERMANENT_SESSION_LIFETIME': timedelta(hours=2),
                'SESSION_COOKIE_SECURE': True,  # HTTPS required
                'SESSION_COOKIE_HTTPONLY': True,
                'SESSION_COOKIE_SAMESITE': 'Lax'
            }
        else:
            # Development/Testing - Relaxed session settings
            config = {
                'PERMANENT_SESSION_LIFETIME': timedelta(hours=24),  # Longer for dev convenience
                'SESSION_COOKIE_SECURE': False,  # Allow HTTP
                'SESSION_COOKIE_HTTPONLY': True,
                'SESSION_COOKIE_SAMESITE': 'Lax'
            }
        
        self._config_cache['session_config'] = config
        return config
    
    def get_security_config(self) -> Dict[str, Any]:
        """
        Get security configuration based on environment
        """
        if 'security_config' in self._config_cache:
            return self._config_cache['security_config']
        
        if self.is_production:
            # Production - Strict security
            config = {
                'SECRET_KEY': os.getenv('SECRET_KEY'),
                'DEBUG': False,
                'TESTING': False,
                'WTF_CSRF_ENABLED': True,
                'WTF_CSRF_TIME_LIMIT': 3600
            }
        else:
            # Development/Testing - Relaxed security
            config = {
                'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
                'DEBUG': True,
                'TESTING': self.is_testing,
                'WTF_CSRF_ENABLED': False,  # Disabled for easier development
                'WTF_CSRF_TIME_LIMIT': None
            }
        
        self._config_cache['security_config'] = config
        return config
    
    def get_email_config(self) -> Dict[str, Any]:
        """
        Get email configuration based on environment
        """
        if 'email_config' in self._config_cache:
            return self._config_cache['email_config']
        
        # Auto-detect application URL
        app_url = self._get_app_url()
        
        config = {
            'APP_URL': app_url,
            'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
            'FROM_EMAIL': os.getenv('FROM_EMAIL'),
            'FROM_NAME': os.getenv('FROM_NAME', 'Ki Wellness'),
            'PASSWORD_RESET_SUBJECT': 'Reset Your Ki Wellness Password',
            'EMAIL_VERIFICATION_SUBJECT': 'Verify Your Ki Wellness Email Address',
            'PASSWORD_RESET_TOKEN_EXPIRY_HOURS': 24
        }
        
        self._config_cache['email_config'] = config
        return config
    
    def _get_app_url(self) -> str:
        """
        Auto-detect application URL based on environment
        """
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
        if self._is_production_database():
            return 'https://kiwellness.org'
        
        # Default to localhost for development
        return 'http://localhost:5000'
    
    def get_flask_config(self) -> Dict[str, Any]:
        """
        Get Flask application configuration based on environment
        """
        if 'flask_config' in self._config_cache:
            return self._config_cache['flask_config']
        
        config = {}
        
        # Merge all configuration sections
        config.update(self.get_security_config())
        config.update(self.get_session_config())
        config.update(self.get_database_config())
        config.update(self.get_stripe_config())
        config.update(self.get_email_config())
        
        # Environment-specific Flask settings
        if self.is_production:
            config.update({
                'HOST': '0.0.0.0',
                'PORT': int(os.getenv('PORT', 5000)),
                'DEBUG': False
            })
        else:
            config.update({
                'HOST': '0.0.0.0',
                'PORT': int(os.getenv('PORT', 5000)),
                'DEBUG': True
            })
        
        self._config_cache['flask_config'] = config
        return config
    
    def get_admin_config(self) -> Dict[str, Any]:
        """
        Get admin configuration based on environment
        """
        if 'admin_config' in self._config_cache:
            return self._config_cache['admin_config']
        
        config = {
            'ADMIN_USERNAME': os.getenv('ADMIN_USERNAME'),
            'ADMIN_PASSWORD': os.getenv('ADMIN_PASSWORD'),
            'ADMIN_EMAIL': os.getenv('ADMIN_EMAIL')
        }
        
        self._config_cache['admin_config'] = config
        return config
    
    def print_environment_info(self):
        """
        Print environment detection information
        """
        env_name = self.environment.value.upper()
        print(f"🌍 Environment: {env_name}")
        
        if self.is_production:
            print("🚀 Running in PRODUCTION mode")
        elif self.is_development:
            print("🛠️ Running in DEVELOPMENT mode")
        elif self.is_testing:
            print("🧪 Running in TESTING mode")
        
        # Print key configuration info
        db_config = self.get_database_config()
        db_uri = db_config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'postgresql://' in db_uri:
            print("📊 Database: PostgreSQL (from DATABASE_URL)")
        elif 'sqlite://' in db_uri:
            print("📊 Database: SQLite (from DATABASE_URL or default)")
        else:
            print(f"📊 Database: Custom ({db_uri})")
        
        stripe_config = self.get_stripe_config()
        stripe_mode = stripe_config.get('STRIPE_MODE', 'disabled')
        if stripe_mode == 'live':
            print("💳 Stripe: LIVE mode (Production payments)")
        elif stripe_mode == 'test':
            print("💳 Stripe: TEST mode (Development payments)")
        else:
            print("💳 Stripe: DISABLED")
        
        email_config = self.get_email_config()
        app_url = email_config.get('APP_URL', 'Unknown')
        print(f"🌐 App URL: {app_url}")


# Global environment detector instance
_env_detector = None


def get_environment_detector() -> EnvironmentDetector:
    """
    Get the global environment detector instance
    """
    global _env_detector
    if _env_detector is None:
        _env_detector = EnvironmentDetector()
    return _env_detector


def is_production() -> bool:
    """
    Quick check if running in production
    """
    return get_environment_detector().is_production


def is_development() -> bool:
    """
    Quick check if running in development
    """
    return get_environment_detector().is_development


def is_testing() -> bool:
    """
    Quick check if running in testing
    """
    return get_environment_detector().is_testing


def get_config(section: str = None) -> Dict[str, Any]:
    """
    Get configuration for a specific section or all sections
    
    Args:
        section: Configuration section ('database', 'stripe', 'session', 'security', 'email', 'flask', 'admin')
    
    Returns:
        Configuration dictionary
    """
    detector = get_environment_detector()
    
    if section is None:
        return detector.get_flask_config()
    
    section_map = {
        'database': detector.get_database_config,
        'stripe': detector.get_stripe_config,
        'session': detector.get_session_config,
        'security': detector.get_security_config,
        'email': detector.get_email_config,
        'flask': detector.get_flask_config,
        'admin': detector.get_admin_config
    }
    
    if section not in section_map:
        raise ValueError(f"Unknown configuration section: {section}")
    
    return section_map[section]()
