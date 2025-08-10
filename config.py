import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get database URL with proper handling for different environments"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Default to SQLite for development
        return 'sqlite:///ki_wellness.db'
    
    # Handle Render's PostgreSQL URL format and update to use psycopg3
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    return database_url

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL Configuration (only used if DATABASE_URL is set)
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'ki_wellness')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    
    # Cloudflare Turnstile Configuration
    TURNSTILE_SITE_KEY = os.getenv('SITE_KEY')
    TURNSTILE_SECRET_KEY = os.getenv('SECRET_KEY')
    TURNSTILE_ENABLED = os.getenv('TURNSTILE_ENABLED', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    
    def __init__(self):
        super().__init__()
        # Force SQLite for development unless explicitly overridden
        if not os.getenv('FORCE_POSTGRES_DEV'):
            self.SQLALCHEMY_DATABASE_URI = 'sqlite:///ki_wellness.db'
            print("🔧 Development mode: Using SQLite database")
        else:
            print("🔧 Development mode: Using PostgreSQL database (FORCE_POSTGRES_DEV set)")
        
        # Disable Turnstile captcha in development for easier testing
        self.TURNSTILE_ENABLED = False
        print("🔧 Development mode: Turnstile captcha disabled")

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    
    def __init__(self):
        super().__init__()
        # Ensure Turnstile is enabled in production
        if not self.TURNSTILE_ENABLED:
            print("⚠️  Warning: Turnstile captcha is disabled in production!")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
