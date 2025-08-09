#!/usr/bin/env python3
"""
Startup script for KI Wellness Profile System
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_sqlalchemy
        import psycopg2
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_postgresql():
    """Check if PostgreSQL is accessible"""
    try:
        from config import config
        import psycopg2
        
        conn = psycopg2.connect(
            host=config['development'].POSTGRES_HOST,
            port=config['development'].POSTGRES_PORT,
            user=config['development'].POSTGRES_USER,
            password=config['development'].POSTGRES_PASSWORD
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("Please make sure PostgreSQL is running and configured correctly")
        return False

def main():
    """Main function to start the application"""
    print("🚀 Starting KI Wellness Profile System...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check PostgreSQL
    if not check_postgresql():
        print("\nTo fix PostgreSQL issues:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Update the database configuration in config.py")
        print("3. Run: python init_db.py")
        sys.exit(1)
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    print("\n✅ All checks passed!")
    print("🌐 Starting Flask application...")
    print("📱 The application will be available at: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the Flask application
    try:
        from app.main import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
