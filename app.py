import os
import mimetypes
from datetime import datetime, timedelta
from flask import Flask, session
from flask_login import LoginManager
from dotenv import load_dotenv

from database import db, User # Import database and models
from routes.modular_registry import register_modular_blueprints # Import modular route blueprints
from services.stripe_client import get_stripe_client # Import stripe client
from services.analytics_service import analytics_service # Import analytics service
from security_middleware import SecurityMiddleware # Import security middleware
from utils.helpers import initialize_default_settings # Import utilities and decorators
from config.environment import get_environment_detector, get_config # Import environment detection

load_dotenv() # Load environment variables

# Initialize environment detector
env_detector = get_environment_detector()

app = Flask(__name__)

# Apply configuration from environment detector
app.config.update(get_config('flask'))

# Fix MIME types for static files
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

# Print environment information
env_detector.print_environment_info()

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
    admin_config = get_config('admin')
    admin_username = admin_config.get('ADMIN_USERNAME')
    admin_password = admin_config.get('ADMIN_PASSWORD')
    admin_email = admin_config.get('ADMIN_EMAIL')
    
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

# Register all route blueprints with feature flag support
register_modular_blueprints(app)

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
        debug=env_detector.is_development,
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000)
    )
