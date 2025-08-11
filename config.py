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
    
    # Auto-detect environment and configure Turnstile
    @property
    def TURNSTILE_ENABLED(self):
        # Check if explicitly disabled via environment variable
        if os.getenv('TURNSTILE_ENABLED', '').lower() == 'false':
            return False
        
        # Check if running on localhost (development)
        # This will be overridden by Flask context in main.py
        host = os.getenv('HOST', '127.0.0.1')
        if host in ['127.0.0.1', 'localhost', '0.0.0.0']:
            return False
        
        # Check if running on kiwellness.org domain (production)
        if 'kiwellness.org' in os.getenv('SERVER_NAME', ''):
            return True
        
        # Default to enabled for production safety
        return True

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
        
        # Turnstile status will be auto-detected based on host
        turnstile_status = "disabled" if not self.TURNSTILE_ENABLED else "enabled"
        print(f"🔧 Development mode: Turnstile captcha {turnstile_status}")

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    
    def __init__(self):
        super().__init__()
        # Ensure Turnstile is enabled in production
        if not self.TURNSTILE_ENABLED:
            print("⚠️  Warning: Turnstile captcha is disabled in production!")
        else:
            print("✅ Production mode: Turnstile captcha enabled")
        
        # Force enable Turnstile for kiwellness.org domain
        if 'kiwellness.org' in os.getenv('SERVER_NAME', ''):
            print("🌐 kiwellness.org domain detected: Turnstile captcha enforced")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
