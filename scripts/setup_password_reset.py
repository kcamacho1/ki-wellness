#!/usr/bin/env python3
"""
Setup script for password reset functionality
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def setup_database_url():
    """Help user set up the DATABASE_URL environment variable"""
    print("🔧 Setting up Password Reset Functionality")
    print("=" * 50)
    
    # Check if DATABASE_URL is already set
    current_url = os.getenv('DATABASE_URL')
    if current_url:
        print(f"✅ DATABASE_URL is already set: {current_url[:20]}...")
        return True
    
    print("❌ DATABASE_URL environment variable is not set.")
    print("\nTo set it up, you have a few options:")
    print("\n1. Set it temporarily for this session:")
    print("   export DATABASE_URL='postgresql://username:password@host:port/database_name'")
    
    print("\n2. Add it to your shell profile (~/.zshrc, ~/.bash_profile, etc.):")
    print("   echo \"export DATABASE_URL='postgresql://username:password@host:port/database_name'\" >> ~/.zshrc")
    
    print("\n3. Create a .env file in the project root:")
    print("   echo \"DATABASE_URL=postgresql://username:password@host:port/database_name\" > .env")
    
    print("\n📝 Replace the connection string with your actual PostgreSQL database URL.")
    print("   Format: postgresql://username:password@host:port/database_name")
    
    return False

def run_migration():
    """Run the password reset migration"""
    print("\n🔄 Running password reset migration...")
    
    try:
        # Import and run the migration
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from migrations.migrate_add_password_reset import migrate
        migrate()
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main setup function"""
    if not setup_database_url():
        print("\n⚠️  Please set the DATABASE_URL environment variable and run this script again.")
        return
    
    if run_migration():
        print("\n✅ Password reset functionality setup complete!")
        print("\n🎉 You can now:")
        print("   - Use 'Forgot Password' on the login page")
        print("   - Change passwords in user profiles")
        print("   - Register with strong password requirements")
    else:
        print("\n❌ Setup failed. Please check your database connection and try again.")

if __name__ == "__main__":
    main()
