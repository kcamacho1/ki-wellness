#!/usr/bin/env python3

"""
Migration: Add Email Verification
Created: 2024-12-19
Description: Add email verification fields to user table
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app and database
from app import app
from database import db, User
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add email verification fields to user table"""
    
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            # Detect database type
            db_dialect = db.engine.dialect.name
            logger.info(f"Database dialect: {db_dialect}")
            
            # Add email verification fields if they don't exist
            if 'email_verified' not in columns:
                logger.info("Adding email_verified column...")
                with db.engine.connect() as conn:
                    if db_dialect == 'postgresql':
                        conn.execute(text('ALTER TABLE "user" ADD COLUMN email_verified BOOLEAN DEFAULT FALSE'))
                    else:  # SQLite
                        conn.execute(text('ALTER TABLE user ADD COLUMN email_verified BOOLEAN DEFAULT FALSE'))
                    conn.commit()
            else:
                logger.info("email_verified column already exists")
                
            if 'email_verification_token' not in columns:
                logger.info("Adding email_verification_token column...")
                with db.engine.connect() as conn:
                    if db_dialect == 'postgresql':
                        conn.execute(text('ALTER TABLE "user" ADD COLUMN email_verification_token TEXT'))
                    else:  # SQLite
                        conn.execute(text('ALTER TABLE user ADD COLUMN email_verification_token TEXT'))
                    conn.commit()
            else:
                logger.info("email_verification_token column already exists")
                
            if 'email_verification_expires' not in columns:
                logger.info("Adding email_verification_expires column...")
                with db.engine.connect() as conn:
                    if db_dialect == 'postgresql':
                        conn.execute(text('ALTER TABLE "user" ADD COLUMN email_verification_expires TIMESTAMP'))
                    else:  # SQLite
                        conn.execute(text('ALTER TABLE user ADD COLUMN email_verification_expires TIMESTAMP'))
                    conn.commit()
            else:
                logger.info("email_verification_expires column already exists")
                
            if 'email_verification_sent_at' not in columns:
                logger.info("Adding email_verification_sent_at column...")
                with db.engine.connect() as conn:
                    if db_dialect == 'postgresql':
                        conn.execute(text('ALTER TABLE "user" ADD COLUMN email_verification_sent_at TIMESTAMP'))
                    else:  # SQLite
                        conn.execute(text('ALTER TABLE user ADD COLUMN email_verification_sent_at TIMESTAMP'))
                    conn.commit()
            else:
                logger.info("email_verification_sent_at column already exists")
            
            # For existing users, set email_verified to True (they were created before verification was required)
            existing_users_count = db.session.query(User).filter(User.email_verified.is_(None)).count()
            if existing_users_count > 0:
                logger.info(f"Setting email_verified=True for {existing_users_count} existing users...")
                db.session.query(User).filter(User.email_verified.is_(None)).update(
                    {User.email_verified: True}, 
                    synchronize_session=False
                )
                db.session.commit()
            
            logger.info("✅ Email verification migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False

def rollback_migration():
    """Remove email verification fields from user table"""
    
    with app.app_context():
        try:
            logger.info("Rolling back email verification migration...")
            
            # Check if columns exist before dropping
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            # Detect database type
            db_dialect = db.engine.dialect.name
            logger.info(f"Database dialect: {db_dialect}")
            
            if 'email_verified' in columns:
                with db.engine.connect() as conn:
                    if db_dialect == 'postgresql':
                        conn.execute(text('ALTER TABLE "user" DROP COLUMN email_verified'))
                    else:  # SQLite
                        conn.execute(text('ALTER TABLE user DROP COLUMN email_verified'))
                    conn.commit()
                logger.info("Dropped email_verified column")
                
            if 'email_verification_token' in columns:
                with db.engine.connect() as conn:
                    if db_dialect == 'postgresql':
                        conn.execute(text('ALTER TABLE "user" DROP COLUMN email_verification_token'))
                    else:  # SQLite
                        conn.execute(text('ALTER TABLE user DROP COLUMN email_verification_token'))
                    conn.commit()
                logger.info("Dropped email_verification_token column")
                
            if 'email_verification_expires' in columns:
                with db.engine.connect() as conn:
                    if db_dialect == 'postgresql':
                        conn.execute(text('ALTER TABLE "user" DROP COLUMN email_verification_expires'))
                    else:  # SQLite
                        conn.execute(text('ALTER TABLE user DROP COLUMN email_verification_expires'))
                    conn.commit()
                logger.info("Dropped email_verification_expires column")
                
            if 'email_verification_sent_at' in columns:
                with db.engine.connect() as conn:
                    if db_dialect == 'postgresql':
                        conn.execute(text('ALTER TABLE "user" DROP COLUMN email_verification_sent_at'))
                    else:  # SQLite
                        conn.execute(text('ALTER TABLE user DROP COLUMN email_verification_sent_at'))
                    conn.commit()
                logger.info("Dropped email_verification_sent_at column")
            
            logger.info("✅ Email verification migration rollback completed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {str(e)}")
            return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_migration()
    else:
        run_migration()
