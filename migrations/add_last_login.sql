-- Migration: Add last_login field to User table
-- Run with: psql $DATABASE_URL -f add_last_login.sql

-- Add last_login column to user table
ALTER TABLE "user" ADD COLUMN last_login TIMESTAMP;

-- Verify the column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'user' AND column_name = 'last_login';

-- Show success message
SELECT 'last_login column added successfully!' as result;
