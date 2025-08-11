#!/usr/bin/env python3
"""
Migration script to update the TokenUsage table with new columns for input/output token tracking.
This script adds the missing columns that are needed for the flexible service tier implementation.
"""

import os
import sys
import sqlite3
from datetime import datetime

def migrate_token_usage_table():
    """Update TokenUsage table with new columns"""
    try:
        print("🔄 Starting TokenUsage table migration...")
        
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
        
        # Check if token_usage table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='token_usage'")
        if not cursor.fetchone():
            print("❌ token_usage table not found. Creating it with new structure...")
            
            # Create the table with the new structure
            cursor.execute("""
                CREATE TABLE token_usage (
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
            
            # Create index for better performance
            cursor.execute("CREATE INDEX idx_token_usage_user_month ON token_usage(user_id, month)")
            print("✅ Created new token_usage table with updated structure")
            
        else:
            print("📊 Found existing token_usage table, checking structure...")
            
            # Get current table structure
            cursor.execute("PRAGMA table_info(token_usage)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Current columns: {columns}")
            
            # Check which columns are missing
            required_columns = ['input_tokens', 'output_tokens']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if not missing_columns:
                print("✅ All required columns already exist")
                return True
            
            print(f"🔧 Adding missing columns: {missing_columns}")
            
            # Add missing columns
            for column in missing_columns:
                if column == 'input_tokens':
                    cursor.execute("ALTER TABLE token_usage ADD COLUMN input_tokens INTEGER DEFAULT 0")
                    print(f"✅ Added column: {column}")
                elif column == 'output_tokens':
                    cursor.execute("ALTER TABLE token_usage ADD COLUMN output_tokens INTEGER DEFAULT 0")
                    print(f"✅ Added column: {column}")
            
            # Update existing records to have default values
            if 'input_tokens' in missing_columns or 'output_tokens' in missing_columns:
                cursor.execute("""
                    UPDATE token_usage 
                    SET input_tokens = COALESCE(input_tokens, 0),
                        output_tokens = COALESCE(output_tokens, 0)
                    WHERE input_tokens IS NULL OR output_tokens IS NULL
                """)
                print("✅ Updated existing records with default values")
        
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
        print("✅ TokenUsage table migration completed successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 TokenUsage Table Migration Script")
    print("=" * 50)
    
    success = migrate_token_usage_table()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nThe TokenUsage table now supports:")
        print("• Separate input and output token tracking")
        print("• Enhanced cost calculation based on token types")
        print("• Better analytics for OpenAI API usage")
        print("\nYour application should now work without the column error!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)
