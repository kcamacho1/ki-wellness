#!/usr/bin/env python3
"""
Mark Production Users as Email Verified
Created: 2024-12-19
Description: Production-safe script to update all existing users to mark their 
             email addresses as verified. Works with both PostgreSQL (production) 
             and SQLite (development).

Usage:
  Production: python scripts/mark_production_users_verified.py --production
  Development: python scripts/mark_production_users_verified.py --dev
  Auto-detect: python scripts/mark_production_users_verified.py
"""

import os
import sys
import argparse
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, User


def detect_environment():
    """Detect if running in production or development"""
    db_url = os.getenv('DATABASE_URL', '')
    if 'postgresql' in db_url or 'postgres' in db_url:
        return 'production'
    return 'development'


def mark_users_verified(dry_run=False):
    """Mark all existing users as email verified
    
    Args:
        dry_run (bool): If True, only show what would be updated without making changes
    """
    
    env = detect_environment()
    print(f"🌿 Ki Wellness - Email Verification Updater ({env.upper()})")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Get all users who are not email verified
            unverified_users = User.query.filter_by(email_verified=False).all()
            total_users = User.query.count()
            verified_users = User.query.filter_by(email_verified=True).count()
            
            print(f"📊 Current Status:")
            print(f"   • Environment: {env}")
            print(f"   • Database: {'PostgreSQL' if env == 'production' else 'SQLite'}")
            print(f"   • Total Users: {total_users}")
            print(f"   • Already Verified: {verified_users}")
            print(f"   • Need Verification: {len(unverified_users)}")
            print()
            
            if not unverified_users:
                print("✅ All users are already email verified!")
                print("🎉 No action needed - all users can log in normally.")
                return True
            
            print(f"👥 Users to be marked as verified:")
            for i, user in enumerate(unverified_users, 1):
                created_date = user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else 'Unknown'
                role_info = f" [{user.role}]" if user.role and user.role != 'user' else ""
                print(f"   {i:2}. {user.username} ({user.email}){role_info}")
                print(f"       Created: {created_date}")
            
            print()
            
            if dry_run:
                print("🔍 DRY RUN MODE - No changes will be made")
                print(f"📝 Would update {len(unverified_users)} users to email_verified=True")
                return True
            
            # Production safety check
            if env == 'production':
                print("⚠️  PRODUCTION ENVIRONMENT DETECTED")
                print("🔒 This will modify the production database")
                print()
                confirm = input(f"🤔 Proceed to mark {len(unverified_users)} users as verified in PRODUCTION? (yes/no): ").strip().lower()
                if confirm not in ['yes', 'y']:
                    print("❌ Operation cancelled for safety")
                    return False
            else:
                confirm = input(f"🤔 Mark {len(unverified_users)} users as verified? (y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    print("❌ Operation cancelled")
                    return False
            
            print()
            print("🔄 Updating users...")
            
            # Update all unverified users
            updated_count = 0
            for user in unverified_users:
                print(f"   ✓ Marking {user.username} as verified...")
                user.email_verified = True
                updated_count += 1
            
            # Commit the changes
            db.session.commit()
            
            print()
            print(f"✅ Successfully updated {updated_count} users!")
            
            # Final status
            final_verified = User.query.filter_by(email_verified=True).count()
            final_unverified = User.query.filter_by(email_verified=False).count()
            
            print()
            print("📊 Final Status:")
            print(f"   • Total verified users: {final_verified}")
            print(f"   • Remaining unverified: {final_unverified}")
            print()
            
            if final_unverified == 0:
                print("🎉 SUCCESS: All users can now log in without email verification!")
            else:
                print(f"⚠️  Note: {final_unverified} users still require verification")
            
            print(f"💾 Changes committed to {env} database")
            
        except Exception as e:
            print(f"❌ Error updating users: {str(e)}")
            print("🔄 Rolling back changes...")
            db.session.rollback()
            return False
    
    return True


def show_status_only():
    """Show current email verification status without making changes"""
    
    env = detect_environment()
    print(f"🌿 Ki Wellness - Email Verification Status ({env.upper()})")
    print("=" * 60)
    
    with app.app_context():
        try:
            total_users = User.query.count()
            verified_users = User.query.filter_by(email_verified=True).count()
            unverified_users = User.query.filter_by(email_verified=False).count()
            
            print(f"📊 Current Status:")
            print(f"   • Environment: {env}")
            print(f"   • Database: {'PostgreSQL' if env == 'production' else 'SQLite'}")
            print(f"   • Total Users: {total_users}")
            print(f"   • Email Verified: {verified_users}")
            print(f"   • Not Verified: {unverified_users}")
            
            if unverified_users > 0:
                print()
                print("👥 Unverified Users:")
                unverified = User.query.filter_by(email_verified=False).all()
                for i, user in enumerate(unverified, 1):
                    created_date = user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Unknown'
                    role_info = f" [{user.role}]" if user.role and user.role != 'user' else ""
                    print(f"   {i:2}. {user.username} ({user.email}){role_info} - Created: {created_date}")
            else:
                print()
                print("✅ All users are email verified!")
            
        except Exception as e:
            print(f"❌ Error querying database: {str(e)}")


def main():
    """Main function with command line argument parsing"""
    
    parser = argparse.ArgumentParser(
        description='Mark existing users as email verified',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/mark_production_users_verified.py --status
  python scripts/mark_production_users_verified.py --dry-run
  python scripts/mark_production_users_verified.py --production
  python scripts/mark_production_users_verified.py --dev
        """
    )
    
    parser.add_argument('--status', action='store_true', 
                       help='Show current verification status only')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without making changes')
    parser.add_argument('--production', action='store_true',
                       help='Force production mode (safety check)')
    parser.add_argument('--dev', action='store_true',
                       help='Force development mode')
    
    args = parser.parse_args()
    
    # Handle environment forcing
    if args.production and args.dev:
        print("❌ Error: Cannot specify both --production and --dev")
        sys.exit(1)
    
    # Set environment if forced
    if args.production:
        os.environ['FORCE_PRODUCTION'] = 'true'
    elif args.dev:
        os.environ['FORCE_DEVELOPMENT'] = 'true'
    
    try:
        if args.status:
            show_status_only()
        else:
            mark_users_verified(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
