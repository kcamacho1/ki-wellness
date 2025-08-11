#!/usr/bin/env python3
"""
Script to fix the TokenUsage table structure to match the expected schema.
This script renames columns and ensures the table structure is correct.
"""

import os
import sys
import sqlite3
from datetime import datetime

def fix_token_usage_structure():
    """Fix TokenUsage table structure to match expected schema"""
    try:
        print("🔄 Starting TokenUsage table structure fix...")
        
        # Get the database path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'ki_wellness.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            return False
        
        print(f"📁 Database found at: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current table structure
        cursor.execute("PRAGMA table_info(token_usage)")
        columns = {column[1]: column for column in cursor.fetchall()}
        print(f"Current columns: {list(columns.keys())}")
        
        # Check what needs to be fixed
        needs_fixing = []
        
        # Check if we need to rename tokens_used to total_tokens
        if 'tokens_used' in columns and 'total_tokens' not in columns:
            needs_fixing.append('rename_tokens_used')
        
        # Check if we need to add total_tokens column
        if 'total_tokens' not in columns:
            needs_fixing.append('add_total_tokens')
        
        if not needs_fixing:
            print("✅ Table structure is already correct")
            return True
        
        print(f"🔧 Fixes needed: {needs_fixing}")
        
        # Create a temporary table with the correct structure
        print("🔧 Creating new table with correct structure...")
        cursor.execute("""
            CREATE TABLE token_usage_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month VARCHAR(7) NOT NULL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost_usd FLOAT DEFAULT 0.0,
                model_used VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Copy data from old table to new table
        if 'tokens_used' in columns:
            print("📊 Migrating data from old structure...")
            cursor.execute("""
                INSERT INTO token_usage_new (id, user_id, month, input_tokens, output_tokens, total_tokens, cost_usd, model_used, created_at)
                SELECT 
                    id, 
                    user_id, 
                    month, 
                    COALESCE(input_tokens, 0) as input_tokens,
                    COALESCE(output_tokens, 0) as output_tokens,
                    COALESCE(tokens_used, 0) as total_tokens,
                    cost_usd, 
                    model_used, 
                    created_at
                FROM token_usage
            """)
        else:
            print("📊 No existing data to migrate")
        
        # Drop the old table
        cursor.execute("DROP TABLE token_usage")
        
        # Rename the new table
        cursor.execute("ALTER TABLE token_usage_new RENAME TO token_usage")
        
        # Create index for better performance
        cursor.execute("CREATE INDEX idx_token_usage_user_month ON token_usage(user_id, month)")
        
        # Verify the final table structure
        cursor.execute("PRAGMA table_info(token_usage)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"\n📋 Final table structure:")
        for column in final_columns:
            print(f"  • {column}")
        
        # Check if there are any existing records
        cursor.execute("SELECT COUNT(*) FROM token_usage")
        record_count = cursor.fetchone()[0]
        print(f"\n📊 Total records in token_usage table: {record_count}")
        
        # Commit the changes
        conn.commit()
        print("✅ TokenUsage table structure fixed successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 TokenUsage Table Structure Fix Script")
    print("=" * 50)
    
    success = fix_token_usage_structure()
    
    if success:
        print("\n🎉 Structure fix completed successfully!")
        print("\nThe TokenUsage table now has the correct structure:")
        print("• id (Primary Key)")
        print("• user_id (Foreign Key)")
        print("• month (YYYY-MM format)")
        print("• input_tokens (Input/prompt tokens)")
        print("• output_tokens (Output/completion tokens)")
        print("• total_tokens (Total tokens used)")
        print("• cost_usd (Cost in USD)")
        print("• model_used (GPT model name)")
        print("• created_at (Timestamp)")
        print("\nYour application should now work correctly!")
    else:
        print("\n❌ Structure fix failed. Please check the error messages above.")
        sys.exit(1)
