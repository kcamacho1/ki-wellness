import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get database URL with proper handling for different environments"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Default to SQLite for development - use absolute path
        # Get the project root directory (parent of app directory)
        project_root = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(project_root, 'ki_wellness.db')
        return f'sqlite:///{db_path}'
    
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
    
    # Google reCAPTCHA v3 Configuration
    RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY')
    RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')
    
    # Auto-detect environment and configure reCAPTCHA
    @property
    def RECAPTCHA_ENABLED(self):
        # Check if explicitly disabled via environment variable
        if os.getenv('RECAPTCHA_ENABLED', '').lower() == 'false':
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
            # Use absolute path for development database
            project_root = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(project_root, 'ki_wellness.db')
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
            print(f"🔧 Development mode: Using SQLite database at {db_path}")
        else:
            print("🔧 Development mode: Using PostgreSQL database (FORCE_POSTGRES_DEV set)")
        
        # reCAPTCHA status will be auto-detected based on host
        recaptcha_status = "disabled" if not self.RECAPTCHA_ENABLED else "enabled"
        print(f"🔧 Development mode: reCAPTCHA v3 {recaptcha_status}")

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    
    def __init__(self):
        super().__init__()
        # Ensure reCAPTCHA is enabled in production
        if not self.RECAPTCHA_ENABLED:
            print("⚠️  Warning: reCAPTCHA v3 is disabled in production!")
        else:
            print("✅ Production mode: reCAPTCHA v3 enabled")
        
        # Force enable reCAPTCHA for kiwellness.org domain
        if 'kiwellness.org' in os.getenv('SERVER_NAME', ''):
            print("🌐 kiwellness.org domain detected: reCAPTCHA v3 enforced")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
