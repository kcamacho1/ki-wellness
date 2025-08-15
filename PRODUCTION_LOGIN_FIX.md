# Production Login Fix - Missing is_active Column

## Issue Description

The production application is experiencing login failures with the following error:

```
❌ Database error during login: (psycopg.errors.UndefinedColumn) column users.is_active does not exist
```

This error occurs because the `users` table in the production database is missing the `is_active` column that is defined in the User model.

## Root Cause

The `is_active` column was added to the User model in the codebase but the corresponding database migration was not applied to the production database. This creates a schema mismatch where:

- **Code expects**: `users.is_active` column to exist
- **Database has**: No `is_active` column in the `users` table

## Solution

### Option 1: Quick Fix (Recommended)

Run the automated fix script:

```bash
# Make sure you're in the project root directory
cd /path/to/ki_wellness

# Run the fix script
./fix_production_login.sh
```

This script will:
1. Activate the virtual environment
2. Check dependencies
3. Add the missing `is_active` column to the `users` table
4. Verify the fix was successful

### Option 2: Manual Fix

If the automated script doesn't work, you can run the fix manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the Python fix script directly
python fix_production_is_active_column.py
```

### Option 3: Database Verification

To check the current state of your production database:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the verification script
python verify_production_database.py
```

This will show you:
- All existing tables
- Current columns in each table
- Missing columns that need to be added
- Database connection status

## What the Fix Does

The fix script performs the following operations:

1. **Connects to the production database** using the `DATABASE_URL` environment variable
2. **Checks if the `is_active` column exists** in the `users` table
3. **Adds the missing column** if it doesn't exist:
   ```sql
   ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL
   ```
4. **Verifies the fix** by checking that the column was successfully added
5. **Reports success/failure** with appropriate exit codes

## Expected Result

After running the fix:

- ✅ Users can log in successfully
- ✅ No more "column users.is_active does not exist" errors
- ✅ All existing users will have `is_active = TRUE` by default
- ✅ New users will have the `is_active` column properly set

## Verification

To verify the fix worked:

1. **Check the logs** - Login attempts should no longer show the column error
2. **Test login** - Try logging in with a valid user account
3. **Check database** - Run the verification script to confirm the column exists

## Troubleshooting

### If the fix script fails:

1. **Check environment variables**:
   ```bash
   echo $DATABASE_URL
   ```

2. **Check database connection**:
   ```bash
   python verify_production_database.py
   ```

3. **Check permissions**:
   - Ensure the database user has ALTER TABLE permissions
   - Ensure the script has read access to the project files

### If login still fails after the fix:

1. **Restart the application** to ensure it picks up the schema changes
2. **Check for other missing columns** using the verification script
3. **Review application logs** for any new errors

## Prevention

To prevent this issue in the future:

1. **Always run migrations** when deploying schema changes
2. **Use the verification script** before and after deployments
3. **Test database schema** in staging environment first
4. **Keep migration scripts** in version control and document them

## Files Created

- `fix_production_is_active_column.py` - Python script to add the missing column
- `fix_production_login.sh` - Shell script to run the fix automatically
- `verify_production_database.py` - Script to verify database schema
- `PRODUCTION_LOGIN_FIX.md` - This documentation file

## Support

If you continue to experience issues after running the fix:

1. Check the application logs for detailed error messages
2. Run the verification script to identify any other missing columns
3. Review the database schema against the model definitions
4. Consider running the comprehensive `fix_database_schema.py` script from the cleanup_backup directory
