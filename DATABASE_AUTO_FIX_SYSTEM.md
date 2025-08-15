# Database Auto-Fix System

## Overview

The Database Auto-Fix System is a comprehensive solution that automatically checks and updates your database schema to match the model definitions. This prevents issues like the recent `is_active` column problem and ensures your database is always up to date.

## Features

### 🔍 **Automatic Schema Validation**
- Compares current database schema with model definitions
- Identifies missing columns, tables, and type mismatches
- Provides detailed reporting of schema issues

### 🔧 **Automatic Schema Repair**
- Adds missing columns with proper types and defaults
- Creates missing tables with correct structure
- Handles nullable constraints and default values
- Safe operations that don't destroy existing data

### 📊 **Comprehensive Reporting**
- Detailed status reports
- Fix operation summaries
- Error tracking and logging
- JSON output support for automation

### 🚀 **Multiple Access Methods**
- Command-line interface
- Shell script wrapper
- Integrated into application startup
- Programmatic API

## Quick Start

### 1. Check Database Status
```bash
# Using shell script
./auto_fix_database.sh status

# Using Python directly
python auto_fix_database.py --status
```

### 2. Check What Needs Fixing
```bash
# Using shell script
./auto_fix_database.sh check

# Using Python directly
python auto_fix_database.py --check
```

### 3. Apply Fixes
```bash
# Using shell script (with confirmation)
./auto_fix_database.sh fix

# Using shell script (force mode)
./auto_fix_database.sh fix-force

# Using Python directly
python auto_fix_database.py --fix --verbose
```

## How It Works

### Schema Definition
The system maintains a comprehensive schema definition based on your SQLAlchemy models:

```python
expected_schema = {
    'users': {
        'id': {'type': Integer, 'primary_key': True, 'autoincrement': True},
        'username': {'type': String(80), 'unique': True, 'nullable': False, 'index': True},
        'email': {'type': String(120), 'unique': True, 'nullable': False, 'index': True},
        'is_active': {'type': Boolean, 'default': True, 'nullable': False},
        # ... more columns
    },
    # ... more tables
}
```

### Validation Process
1. **Connect to Database**: Uses `DATABASE_URL` environment variable
2. **Inspect Current Schema**: Uses SQLAlchemy inspector to get current state
3. **Compare Schemas**: Compares current vs expected schema
4. **Identify Issues**: Finds missing columns, tables, and type mismatches
5. **Generate Report**: Creates detailed report of findings

### Fix Process
1. **Missing Tables**: Creates tables with proper structure
2. **Missing Columns**: Adds columns with correct types and defaults
3. **Type Mismatches**: Logs warnings (doesn't auto-fix to prevent data loss)
4. **Constraints**: Handles nullable, unique, and default constraints
5. **Verification**: Confirms fixes were applied successfully

## Supported Operations

### ✅ **Safe Operations (Auto-Fixed)**
- Adding missing columns
- Creating missing tables
- Setting default values
- Adding nullable constraints

### ⚠️ **Logged Operations (Manual Review)**
- Column type changes (potential data loss)
- Constraint modifications
- Index changes

### ❌ **Not Supported**
- Column renames
- Table renames
- Data migrations
- Complex schema changes

## Integration

### Application Startup
The auto-fix system is integrated into the main application startup:

```python
# In app/main.py
with app.app_context():
    # ... health checks ...
    
    # Auto-fix database schema if needed
    try:
        from .utils.database_auto_fix import auto_fix_database
        print("🔧 Checking and auto-fixing database schema...")
        fix_results = auto_fix_database()
        
        if fix_results.get('success', False):
            if fix_results.get('fixes_applied'):
                print(f"✅ Database schema auto-fixed - {len(fix_results['fixes_applied'])} fixes applied")
            else:
                print("✅ Database schema is up to date - no fixes needed")
    except Exception as e:
        print(f"⚠️  Database auto-fix failed: {e}")
```

### Programmatic Usage
```python
from app.utils.database_auto_fix import auto_fix_database, get_database_status

# Check status
status = get_database_status()
print(f"Database has {status['total_tables']} tables")

# Apply fixes
results = auto_fix_database()
if results['success']:
    print(f"Applied {len(results['fixes_applied'])} fixes")
```

## Command Line Interface

### Shell Script (`auto_fix_database.sh`)
```bash
# Show help
./auto_fix_database.sh help

# Check status
./auto_fix_database.sh status

# Check what needs fixing
./auto_fix_database.sh check

# Apply fixes with confirmation
./auto_fix_database.sh fix

# Apply fixes without confirmation
./auto_fix_database.sh fix-force
```

### Python Script (`auto_fix_database.py`)
```bash
# Show help
python auto_fix_database.py --help

# Check status
python auto_fix_database.py --status

# Check what needs fixing
python auto_fix_database.py --check

# Apply fixes
python auto_fix_database.py --fix

# Verbose output
python auto_fix_database.py --fix --verbose

# JSON output
python auto_fix_database.py --status --json
```

## Configuration

### Environment Variables
- `DATABASE_URL`: Required - Database connection string

### Logging
The system uses Python's logging module. Set log level via:
```python
import logging
logging.basicConfig(level=logging.INFO)  # For verbose output
```

## Output Examples

### Status Report
```
📊 Database Status Report
------------------------------
Timestamp: 2025-08-15T16:30:00.123456
Database: production-db.example.com
Total Tables: 8

📋 Table Details:
  📄 users
     Columns: 20
     Column names: id, username, email, password_hash, phone, is_admin, is_active, created_at, updated_at, email_verified, phone_verified, email_verification_token, phone_verification_code, phone_verification_expires, email_notifications, sms_notifications, push_notifications, oauth_provider, oauth_id, oauth_email, oauth_name, oauth_picture
```

### Fix Results
```
🔧 Auto-Fix Results
--------------------
Timestamp: 2025-08-15T16:30:00.123456
Success: ✅ Yes

Total Fixes Applied: 2
Total Errors: 0
Status: SUCCESS

✅ Fixes Applied:
  ➕ Added column users.is_active
  ➕ Added column user_profiles.weight_unit
```

## Error Handling

### Common Errors
1. **DATABASE_URL not set**: Set the environment variable
2. **Connection failed**: Check database connectivity
3. **Permission denied**: Ensure database user has ALTER TABLE permissions
4. **Column already exists**: System handles gracefully

### Error Recovery
- Failed operations are logged but don't stop the process
- Partial success is reported
- Application continues to start even if auto-fix fails

## Best Practices

### Development
1. **Test locally first**: Always test schema changes locally
2. **Use version control**: Keep migration scripts in version control
3. **Backup before fixes**: Always backup production database
4. **Monitor logs**: Check application logs for auto-fix results

### Production
1. **Schedule maintenance**: Run auto-fix during maintenance windows
2. **Monitor results**: Check auto-fix results in application logs
3. **Have rollback plan**: Keep database backups before major changes
4. **Test in staging**: Test schema changes in staging environment first

## Troubleshooting

### Auto-Fix Not Working
1. Check `DATABASE_URL` environment variable
2. Verify database connectivity
3. Check database user permissions
4. Review application logs for errors

### Missing Columns Still Present
1. Run status check to confirm current state
2. Check if column was added successfully
3. Restart application to pick up changes
4. Verify model definitions are correct

### Permission Errors
1. Ensure database user has ALTER TABLE permissions
2. Check if database is read-only
3. Verify connection string is correct
4. Contact database administrator if needed

## Files

### Core System
- `app/utils/database_auto_fix.py` - Main auto-fix system
- `auto_fix_database.py` - Command-line interface
- `auto_fix_database.sh` - Shell script wrapper

### Integration
- `app/main.py` - Application startup integration
- `app/models.py` - Model definitions (schema source)

### Documentation
- `DATABASE_AUTO_FIX_SYSTEM.md` - This documentation
- `PRODUCTION_LOGIN_FIX.md` - Specific fix documentation

## Future Enhancements

### Planned Features
- Column type migration support
- Data migration capabilities
- Schema versioning
- Rollback functionality
- Web interface for schema management

### Potential Improvements
- Support for more database types
- Advanced constraint handling
- Performance optimizations
- Integration with migration tools

## Support

For issues with the auto-fix system:

1. Check the troubleshooting section above
2. Review application logs for detailed error messages
3. Run status check to understand current state
4. Test fixes in development environment first
5. Contact the development team with specific error details
