#!/usr/bin/env python3
"""
Startup script for KI Wellness Profile System
"""

import os
import sys

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_sqlalchemy
        # Try both psycopg versions for compatibility
        try:
            import psycopg
            print("✅ Using psycopg (newer version)")
        except ImportError:
            try:
                import psycopg2
                print("✅ Using psycopg2 (legacy version)")
            except ImportError:
                print("⚠️  No PostgreSQL adapter found - will use SQLite for development")
        
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def main():
    """Main function to start the application"""
    print("🚀 Starting KI Wellness Profile System...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Set environment variables for development
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    print("\n✅ All checks passed!")
    print("🌐 Starting Flask application...")
    print("📱 The application will be available at: http://localhost:5001")
    print("🗄️  Using SQLite database for development (auto-created)")
    print("🔒 Turnstile captcha disabled for development")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the Flask application
    try:
        from app.main import app
        app.run(debug=True, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
