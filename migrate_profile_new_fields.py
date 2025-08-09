#!/usr/bin/env python3
"""
Migration script to add new fields to user_profiles table:
- exercise_routine (TEXT)
- spiritual_religion (TEXT)
- self_connection (TEXT)
- surroundings_connection (TEXT)
- providing_others (TEXT)
- safe_groups (TEXT)
- awe_things (TEXT)
- creative_expression (TEXT)
- upsetting_situations (TEXT)
- spirit_notes (TEXT)
"""

import psycopg2
from config import DevelopmentConfig

def migrate_profile_new_fields():
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            host=DevelopmentConfig.POSTGRES_HOST,
            port=DevelopmentConfig.POSTGRES_PORT,
            database=DevelopmentConfig.POSTGRES_DB,
            user=DevelopmentConfig.POSTGRES_USER,
            password=DevelopmentConfig.POSTGRES_PASSWORD
        )
        cursor = conn.cursor()

        print("🔧 Adding new fields to user_profiles table...")

        # Add new fields
        new_fields = [
            'exercise_routine',
            'spiritual_religion',
            'self_connection',
            'surroundings_connection',
            'providing_others',
            'safe_groups',
            'awe_things',
            'creative_expression',
            'upsetting_situations',
            'spirit_notes'
        ]

        for field in new_fields:
            cursor.execute(f"""
                ALTER TABLE user_profiles
                ADD COLUMN IF NOT EXISTS {field} TEXT
            """)
            print(f"   ✅ Added {field}")

        conn.commit()
        print("✅ Successfully added all new fields to user_profiles table!")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_profile_new_fields()
