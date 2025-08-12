# Cleanup Backup Directory

This directory contains migration scripts and setup files that were used during the development and cleanup process of the Ki Wellness application.

## Migration Scripts

### Database Migrations
- `migrate_*.py` - Various database migration scripts for schema updates
- `init_db.py` - Initial database setup script
- `init_db_render.py` - Database initialization for Render deployment
- `fix_database_schema.py` - Database schema fixes
- `fix_token_usage_structure.py` - Token usage table structure fixes

### System Setup Scripts
- `setup_recaptcha.py` - reCAPTCHA integration setup
- `security_audit.py` - Security audit script
- `activate_venv.sh` - Virtual environment activation script

## Usage

These scripts are kept for reference and potential rollback purposes. They should not be run unless you need to:

1. **Rollback to a previous database schema**
2. **Re-run a specific migration**
3. **Debug database issues**

## Important Notes

- **Backup your database** before running any migration scripts
- **Test in development environment** first
- **Review the script contents** before execution
- **Some scripts may be outdated** and not compatible with current codebase

## Current Status

All migrations have been applied to the production database. These scripts are kept for:
- Historical reference
- Emergency rollback scenarios
- Development environment setup
