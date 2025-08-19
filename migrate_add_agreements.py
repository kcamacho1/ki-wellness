#!/usr/bin/env python3
"""
Migration script to add agreement tracking fields to User model.
Run this script to update existing databases with the new agreement fields.
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User

def migrate_add_agreements():
    """Add agreement tracking fields to User model"""
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('user')]
            
            # Add new columns if they don't exist
            if 'agreed_to_terms' not in existing_columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "user" ADD COLUMN agreed_to_terms BOOLEAN DEFAULT FALSE'))
                    conn.commit()
                print("✓ Added agreed_to_terms column")
            
            if 'agreed_to_privacy' not in existing_columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "user" ADD COLUMN agreed_to_privacy BOOLEAN DEFAULT FALSE'))
                    conn.commit()
                print("✓ Added agreed_to_privacy column")
            
            if 'agreed_to_disclaimer' not in existing_columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "user" ADD COLUMN agreed_to_disclaimer BOOLEAN DEFAULT FALSE'))
                    conn.commit()
                print("✓ Added agreed_to_disclaimer column")
            
            if 'agreements_date' not in existing_columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "user" ADD COLUMN agreements_date TIMESTAMP'))
                    conn.commit()
                print("✓ Added agreements_date column")
            
            # Update existing users to have agreements marked as accepted
            # (assuming they implicitly agreed by using the service)
            existing_users = User.query.all()
            for user in existing_users:
                if not user.agreed_to_terms:
                    user.agreed_to_terms = True
                    user.agreed_to_privacy = True
                    user.agreed_to_disclaimer = True
                    user.agreements_date = user.created_at or datetime.utcnow()
            
            db.session.commit()
            print(f"✓ Updated {len(existing_users)} existing users with agreement data")
            
            print("\n🎉 Migration completed successfully!")
            print("All users now have agreement tracking fields.")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    print("Starting migration to add agreement tracking fields...")
    print("=" * 50)
    
    success = migrate_add_agreements()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("New users will now be required to agree to Terms of Service, Privacy Policy, and Disclaimer.")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
