import os
import mimetypes
from datetime import datetime, timedelta
from flask import Flask, session
from flask_login import LoginManager
from dotenv import load_dotenv


from database import db, User # Import database and models
from routes import register_blueprints # Import route blueprints
from services.stripe_client import get_stripe_client # Import stripe client
from services.analytics_service import analytics_service # Import analytics service
from security_middleware import SecurityMiddleware # Import security middleware
from utils.helpers import initialize_default_settings # Import utilities and decorators

load_dotenv() # Load environment variables

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Fix MIME types for static files
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

# Session configuration - Auto-logout after 24 hours of inactivity
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Keep HttpOnly for security
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Database configuration - Multi-driver approach
db_url = os.getenv('DATABASE_URL')
is_production = bool(db_url and 'postgresql' in db_url)

if is_production:
    # Production - PostgreSQL with driver detection
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    # Try to use the best available driver
    try:
        import psycopg2
        print("✅ Using psycopg2 (maximum compatibility)")
        # Use standard postgresql:// URL - SQLAlchemy will auto-detect
    except ImportError:
        try:
            import psycopg
            print("✅ Using psycopg3 (Python 3.13+ compatible)")
            # Force psycopg dialect
            if '+psycopg' not in db_url:
                db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        except ImportError:
            print("⚠️ No PostgreSQL driver found - falling back to SQLite")
            db_url = None
            is_production = False
    
    if is_production:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {
                'connect_timeout': 10
            },
            'pool_timeout': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
        print(f"✅ Production database configured with PostgreSQL")
else:
    # Development - SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ki_wellness_dev.db'
    print(f"✅ Development database configured with SQLite")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def check_session_expiry():
    """Check if user session should expire"""
    if 'last_activity' in session:
        if datetime.now() - session['last_activity'] > app.config['PERMANENT_SESSION_LIFETIME']:
            session.clear()
            return False
    session['last_activity'] = datetime.now()
    return True

# Initialize security middleware
security = SecurityMiddleware(app)

def create_admin_user():
    """Create admin user if it doesn't exist"""
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')
    admin_email = os.getenv('ADMIN_EMAIL')
    
    if not all([admin_username, admin_password, admin_email]):
        print("⚠️ Admin credentials not set in environment variables")
        return
    
    # Check if admin user already exists
    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        print(f"✅ Admin user already exists: {admin_email}")
        return
    
    try:
        from werkzeug.security import generate_password_hash
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=generate_password_hash(admin_password),
            name="Administrator",
            is_admin=True,
            email_verified=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        print(f"✅ Admin user created successfully: {admin_email}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.session.rollback()

# Register all route blueprints
register_blueprints(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
        initialize_default_settings()
        
        # Initialize Stripe products and prices
        try:
            stripe_client = get_stripe_client()
            if stripe_client:
                print("🔧 Initializing Stripe products and prices...")
                stripe_client.setup_products_and_prices()
                print("✅ Stripe products and prices initialized")
        except Exception as e:
            print(f"⚠️ Stripe setup error: {e}")
            # Continue even if Stripe setup fails
        
        print("🚀 Ki Wellness application started successfully!")
    
    app.run(
        debug=os.getenv('FLASK_ENV') == 'development',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )
