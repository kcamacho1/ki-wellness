#!/usr/bin/env python3
"""
Migration script to add extended nutritional fields to food_journal table
This adds comprehensive nutritional data fields while keeping the UI clean
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, db
from sqlalchemy import text

def migrate_extended_nutrition():
    """Add extended nutritional fields to food_journal table"""
    print("🔧 Starting extended nutrition migration...")
    
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('food_journal')]
            
            # Extended nutritional fields to add
            new_columns = [
                ('saturated_fat', 'FLOAT'),
                ('trans_fat', 'FLOAT'),
                ('cholesterol', 'FLOAT'),
                ('potassium', 'FLOAT'),
                ('calcium', 'FLOAT'),
                ('iron', 'FLOAT'),
                ('vitamin_a', 'FLOAT'),
                ('vitamin_c', 'FLOAT'),
                ('vitamin_d', 'FLOAT'),
                ('vitamin_e', 'FLOAT'),
                ('vitamin_k', 'FLOAT'),
                ('vitamin_b6', 'FLOAT'),
                ('vitamin_b12', 'FLOAT'),
                ('magnesium', 'FLOAT'),
                ('zinc', 'FLOAT'),
                ('phosphorus', 'FLOAT'),
                ('manganese', 'FLOAT'),
                ('selenium', 'FLOAT'),
                ('copper', 'FLOAT'),
                ('thiamin', 'FLOAT'),
                ('riboflavin', 'FLOAT'),
                ('niacin', 'FLOAT'),
                ('folate', 'FLOAT'),
                ('pantothenic_acid', 'FLOAT'),
                ('biotin', 'FLOAT'),
                ('choline', 'FLOAT'),
                ('betaine', 'FLOAT'),
                ('taurine', 'FLOAT'),
                ('caffeine', 'FLOAT'),
                ('alcohol', 'FLOAT'),
                ('water_content', 'FLOAT'),
                ('ash', 'FLOAT'),
                ('data_source', 'VARCHAR(50)'),
                ('barcode', 'VARCHAR(50)')
            ]
            
            # Add columns that don't exist
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    print(f"  ➕ Adding column: {column_name}")
                    sql = f"ALTER TABLE food_journal ADD COLUMN {column_name} {column_type}"
                    db.session.execute(text(sql))
                else:
                    print(f"  ✅ Column already exists: {column_name}")
            
            db.session.commit()
            print("✅ Extended nutrition migration completed successfully!")
            
            # Verify the migration
            inspector = db.inspect(db.engine)
            final_columns = [col['name'] for col in inspector.get_columns('food_journal')]
            print(f"📊 Total columns in food_journal table: {len(final_columns)}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = migrate_extended_nutrition()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("The food_journal table now supports comprehensive nutritional data storage.")
        print("Users will see only core nutritional values in the UI, but all data is stored for future analysis.")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)
