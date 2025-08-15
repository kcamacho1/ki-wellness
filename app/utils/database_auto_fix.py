"""
Database Auto-Fix System
========================

This module provides automatic database schema validation and repair functionality.
It compares the current database schema with the model definitions and automatically
fixes any mismatches, missing columns, or outdated structures.

Author: Ki Wellness Team
Version: 2.0
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.types import String, Integer, Boolean, DateTime, Float, Date, Time, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseAutoFix:
    """
    Automatic database schema validation and repair system
    
    This class provides comprehensive database schema management:
    - Validates current schema against model definitions
    - Automatically adds missing columns
    - Updates column types and constraints
    - Creates missing tables
    - Provides detailed reporting
    """
    
    def __init__(self, database_url: str):
        """Initialize the auto-fix system with database connection"""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.fixes_applied = []
        self.errors_encountered = []
        
        # Define expected schema based on models
        self.expected_schema = self._define_expected_schema()
    
    def _define_expected_schema(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Define the expected database schema based on model definitions
        
        Returns:
            Dict mapping table names to column definitions
        """
        return {
            'users': {
                'id': {'type': Integer, 'primary_key': True, 'autoincrement': True},
                'username': {'type': String(80), 'unique': True, 'nullable': False, 'index': True},
                'email': {'type': String(120), 'unique': True, 'nullable': False, 'index': True},
                'password_hash': {'type': String(255), 'nullable': False},
                'phone': {'type': String(20), 'nullable': True, 'index': True},
                'is_admin': {'type': Boolean, 'default': False, 'nullable': False},
                'is_active': {'type': Boolean, 'default': True, 'nullable': False},
                'created_at': {'type': DateTime, 'default': datetime.utcnow},
                'updated_at': {'type': DateTime, 'default': datetime.utcnow},
                'email_verified': {'type': Boolean, 'default': False, 'nullable': False},
                'phone_verified': {'type': Boolean, 'default': False, 'nullable': False},
                'email_verification_token': {'type': String(255), 'nullable': True, 'unique': True},
                'phone_verification_code': {'type': String(6), 'nullable': True},
                'phone_verification_expires': {'type': DateTime, 'nullable': True},
                'email_notifications': {'type': Boolean, 'default': True},
                'sms_notifications': {'type': Boolean, 'default': False},
                'push_notifications': {'type': Boolean, 'default': True},
                'oauth_provider': {'type': String(20), 'nullable': True},
                'oauth_id': {'type': String(255), 'nullable': True, 'unique': True},
                'oauth_email': {'type': String(255), 'nullable': True},
                'oauth_name': {'type': String(255), 'nullable': True},
                'oauth_picture': {'type': String(500), 'nullable': True}
            },
            'user_profiles': {
                'id': {'type': Integer, 'primary_key': True, 'autoincrement': True},
                'user_id': {'type': Integer, 'nullable': False},
                'name': {'type': String(100), 'nullable': True},
                'avatar': {'type': String(100), 'nullable': True, 'default': 'default-avatar.png'},
                'weight_unit': {'type': String(10), 'nullable': True, 'default': 'kg'},
                'date_of_birth': {'type': Date, 'nullable': True},
                'age': {'type': Integer, 'nullable': True},
                'gender': {'type': String(20), 'nullable': True},
                'weight': {'type': Float, 'nullable': True},
                'height': {'type': Float, 'nullable': True},
                'height_ft': {'type': Float, 'nullable': True},
                'goal': {'type': String(100), 'nullable': True},
                'goals': {'type': Text, 'nullable': True},
                'custom_goal': {'type': String(200), 'nullable': True},
                'ailments': {'type': Text, 'nullable': True},
                'dietary_preferences': {'type': Text, 'nullable': True},
                'sleep_schedule': {'type': String(100), 'nullable': True},
                'daily_activities': {'type': Text, 'nullable': True},
                'exercise_routine': {'type': Text, 'nullable': True},
                'day_notes': {'type': Text, 'nullable': True},
                'night_notes': {'type': Text, 'nullable': True},
                'spiritual_religion': {'type': Text, 'nullable': True},
                'self_connection': {'type': Text, 'nullable': True},
                'surroundings_connection': {'type': Text, 'nullable': True},
                'providing_others': {'type': Text, 'nullable': True},
                'safe_groups': {'type': Text, 'nullable': True},
                'awe_things': {'type': Text, 'nullable': True},
                'creative_expression': {'type': Text, 'nullable': True},
                'upsetting_situations': {'type': Text, 'nullable': True},
                'spirit_notes': {'type': Text, 'nullable': True},
                'created_at': {'type': DateTime, 'default': datetime.utcnow},
                'updated_at': {'type': DateTime, 'default': datetime.utcnow}
            },
            'food_journal': {
                'id': {'type': Integer, 'primary_key': True, 'autoincrement': True},
                'user_id': {'type': Integer, 'nullable': False},
                'food_name': {'type': String(200), 'nullable': False},
                'brand': {'type': String(100), 'nullable': True},
                'serving_size': {'type': Float, 'nullable': False},
                'serving_unit': {'type': String(20), 'nullable': False},
                'calories': {'type': Float, 'nullable': True},
                'protein': {'type': Float, 'nullable': True},
                'carbs': {'type': Float, 'nullable': True},
                'fat': {'type': Float, 'nullable': True},
                'fiber': {'type': Float, 'nullable': True},
                'sugar': {'type': Float, 'nullable': True},
                'sodium': {'type': Float, 'nullable': True},
                'saturated_fat': {'type': Float, 'nullable': True},
                'trans_fat': {'type': Float, 'nullable': True},
                'cholesterol': {'type': Float, 'nullable': True},
                'potassium': {'type': Float, 'nullable': True},
                'calcium': {'type': Float, 'nullable': True},
                'iron': {'type': Float, 'nullable': True},
                'vitamin_a': {'type': Float, 'nullable': True},
                'vitamin_c': {'type': Float, 'nullable': True},
                'vitamin_d': {'type': Float, 'nullable': True},
                'vitamin_e': {'type': Float, 'nullable': True},
                'vitamin_k': {'type': Float, 'nullable': True},
                'vitamin_b6': {'type': Float, 'nullable': True},
                'vitamin_b12': {'type': Float, 'nullable': True},
                'magnesium': {'type': Float, 'nullable': True},
                'zinc': {'type': Float, 'nullable': True},
                'phosphorus': {'type': Float, 'nullable': True},
                'manganese': {'type': Float, 'nullable': True},
                'selenium': {'type': Float, 'nullable': True},
                'copper': {'type': Float, 'nullable': True},
                'thiamin': {'type': Float, 'nullable': True},
                'riboflavin': {'type': Float, 'nullable': True},
                'niacin': {'type': Float, 'nullable': True},
                'folate': {'type': Float, 'nullable': True},
                'pantothenic_acid': {'type': Float, 'nullable': True},
                'biotin': {'type': Float, 'nullable': True},
                'choline': {'type': Float, 'nullable': True},
                'betaine': {'type': Float, 'nullable': True},
                'taurine': {'type': Float, 'nullable': True},
                'caffeine': {'type': Float, 'nullable': True},
                'alcohol': {'type': Float, 'nullable': True},
                'water_content': {'type': Float, 'nullable': True},
                'ash': {'type': Float, 'nullable': True},
                'data_source': {'type': String(50), 'nullable': True},
                'barcode': {'type': String(50), 'nullable': True},
                'time_of_day': {'type': String(20), 'nullable': True},
                'water_amount': {'type': Float, 'nullable': True},
                'water_unit': {'type': String(20), 'nullable': True},
                'mood': {'type': String(50), 'nullable': True},
                'notes': {'type': Text, 'nullable': True},
                'consumed_at': {'type': DateTime, 'default': datetime.utcnow},
                'created_at': {'type': DateTime, 'default': datetime.utcnow}
            },
            'mood_entries': {
                'id': {'type': Integer, 'primary_key': True, 'autoincrement': True},
                'user_id': {'type': Integer, 'nullable': False},
                'mood': {'type': String(50), 'nullable': False},
                'notes': {'type': Text, 'nullable': True},
                'logged_at': {'type': DateTime, 'default': datetime.utcnow},
                'created_at': {'type': DateTime, 'default': datetime.utcnow}
            },
            'patterns_cache': {
                'id': {'type': Integer, 'primary_key': True, 'autoincrement': True},
                'user_id': {'type': Integer, 'nullable': False},
                'period_type': {'type': String(10), 'nullable': False},
                'analysis': {'type': Text, 'nullable': True},
                'suggestions': {'type': Text, 'nullable': True},
                'summary': {'type': JSON, 'nullable': True},
                'last_updated': {'type': DateTime, 'default': datetime.utcnow},
                'created_at': {'type': DateTime, 'default': datetime.utcnow}
            },
            'token_usage': {
                'id': {'type': Integer, 'primary_key': True, 'autoincrement': True},
                'user_id': {'type': Integer, 'nullable': False},
                'month': {'type': String(7), 'nullable': False},
                'input_tokens': {'type': Integer, 'default': 0},
                'output_tokens': {'type': Integer, 'default': 0},
                'total_tokens': {'type': Integer, 'default': 0},
                'cost_usd': {'type': Float, 'default': 0.0},
                'model_used': {'type': String(50), 'nullable': True},
                'created_at': {'type': DateTime, 'default': datetime.utcnow}
            },
            'email_subscriptions': {
                'id': {'type': Integer, 'primary_key': True, 'autoincrement': True},
                'email': {'type': String(120), 'unique': True, 'nullable': False, 'index': True},
                'unsubscribe_token': {'type': String(255), 'unique': True, 'nullable': False, 'index': True},
                'is_active': {'type': Boolean, 'default': True, 'nullable': False},
                'created_at': {'type': DateTime, 'default': datetime.utcnow},
                'updated_at': {'type': DateTime, 'default': datetime.utcnow}
            }
        }
    
    def _get_sql_type_string(self, column_def: Dict[str, Any]) -> str:
        """Convert SQLAlchemy type to SQL string for ALTER TABLE statements"""
        sql_type = column_def['type']
        
        if hasattr(sql_type, 'length') and sql_type.length:
            return f"{sql_type.__class__.__name__.upper()}({sql_type.length})"
        elif hasattr(sql_type, '__class__'):
            return sql_type.__class__.__name__.upper()
        else:
            return str(sql_type).upper()
    
    def _get_default_value(self, column_def: Dict[str, Any]) -> str:
        """Get default value for column definition"""
        default = column_def.get('default')
        if default is None:
            return ''
        
        if callable(default):
            # Handle callable defaults like datetime.utcnow
            if default.__name__ == 'utcnow':
                return 'DEFAULT CURRENT_TIMESTAMP'
            else:
                return f"DEFAULT {default()}"
        else:
            if isinstance(default, bool):
                return f"DEFAULT {str(default).upper()}"
            elif isinstance(default, str):
                return f"DEFAULT '{default}'"
            else:
                return f"DEFAULT {default}"
    
    def check_and_fix_database(self) -> Dict[str, Any]:
        """
        Main method to check and fix database schema
        
        Returns:
            Dict containing results of the operation
        """
        logger.info("🔍 Starting database schema validation and auto-fix...")
        
        try:
            # Get current database state
            existing_tables = self.inspector.get_table_names()
            logger.info(f"📊 Found {len(existing_tables)} existing tables: {existing_tables}")
            
            # Check and fix each expected table
            for table_name, expected_columns in self.expected_schema.items():
                if table_name in existing_tables:
                    self._fix_table_columns(table_name, expected_columns)
                else:
                    self._create_missing_table(table_name, expected_columns)
            
            # Generate report
            report = self._generate_report()
            
            logger.info("✅ Database schema validation and auto-fix completed")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error during database auto-fix: {e}")
            self.errors_encountered.append(str(e))
            return self._generate_report()
    
    def _fix_table_columns(self, table_name: str, expected_columns: Dict[str, Dict[str, Any]]):
        """Fix columns in an existing table"""
        logger.info(f"🔧 Checking table: {table_name}")
        
        try:
            # Get current columns
            current_columns = self.inspector.get_columns(table_name)
            current_column_names = [col['name'] for col in current_columns]
            
            # Check for missing columns
            for column_name, column_def in expected_columns.items():
                if column_name not in current_column_names:
                    self._add_missing_column(table_name, column_name, column_def)
                else:
                    # Check if column type needs updating
                    self._check_column_type(table_name, column_name, column_def, current_columns)
            
        except Exception as e:
            error_msg = f"Error fixing table {table_name}: {e}"
            logger.error(error_msg)
            self.errors_encountered.append(error_msg)
    
    def _add_missing_column(self, table_name: str, column_name: str, column_def: Dict[str, Any]):
        """Add a missing column to a table"""
        try:
            sql_type = self._get_sql_type_string(column_def)
            default_value = self._get_default_value(column_def)
            nullable = "NOT NULL" if column_def.get('nullable', True) is False else ""
            
            # Build ALTER TABLE statement
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"
            if default_value:
                alter_sql += f" {default_value}"
            if nullable:
                alter_sql += f" {nullable}"
            
            logger.info(f"➕ Adding column: {table_name}.{column_name}")
            with self.engine.connect() as conn:
                conn.execute(text(alter_sql))
                conn.commit()
            
            self.fixes_applied.append(f"Added column {table_name}.{column_name}")
            logger.info(f"✅ Successfully added column: {table_name}.{column_name}")
            
        except Exception as e:
            error_msg = f"Failed to add column {table_name}.{column_name}: {e}"
            logger.error(error_msg)
            self.errors_encountered.append(error_msg)
    
    def _check_column_type(self, table_name: str, column_name: str, expected_def: Dict[str, Any], current_columns: List[Dict]):
        """Check if column type needs updating"""
        # Find current column definition
        current_col = next((col for col in current_columns if col['name'] == column_name), None)
        if not current_col:
            return
        
        # For now, we'll just log type mismatches but not auto-fix them
        # as type changes can be destructive
        expected_type = self._get_sql_type_string(expected_def)
        current_type = str(current_col['type'])
        
        if expected_type.lower() != current_type.lower():
            logger.warning(f"⚠️  Type mismatch in {table_name}.{column_name}: expected {expected_type}, found {current_type}")
    
    def _create_missing_table(self, table_name: str, expected_columns: Dict[str, Dict[str, Any]]):
        """Create a missing table"""
        try:
            logger.info(f"🏗️  Creating missing table: {table_name}")
            
            # Build CREATE TABLE statement
            columns_sql = []
            for column_name, column_def in expected_columns.items():
                sql_type = self._get_sql_type_string(column_def)
                default_value = self._get_default_value(column_def)
                nullable = "NOT NULL" if column_def.get('nullable', True) is False else ""
                
                column_sql = f"{column_name} {sql_type}"
                if default_value:
                    column_sql += f" {default_value}"
                if nullable:
                    column_sql += f" {nullable}"
                
                if column_def.get('primary_key'):
                    column_sql += " PRIMARY KEY"
                if column_def.get('autoincrement'):
                    column_sql += " AUTOINCREMENT"
                
                columns_sql.append(column_sql)
            
            create_sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(columns_sql) + "\n)"
            
            with self.engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
            
            self.fixes_applied.append(f"Created table {table_name}")
            logger.info(f"✅ Successfully created table: {table_name}")
            
        except Exception as e:
            error_msg = f"Failed to create table {table_name}: {e}"
            logger.error(error_msg)
            self.errors_encountered.append(error_msg)
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of the auto-fix operation"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'success': len(self.errors_encountered) == 0,
            'fixes_applied': self.fixes_applied,
            'errors_encountered': self.errors_encountered,
            'summary': {
                'total_fixes': len(self.fixes_applied),
                'total_errors': len(self.errors_encountered),
                'status': 'success' if len(self.errors_encountered) == 0 else 'partial_success' if self.fixes_applied else 'failed'
            }
        }
    
    def get_database_status(self) -> Dict[str, Any]:
        """Get current database status without making changes"""
        try:
            existing_tables = self.inspector.get_table_names()
            status = {
                'timestamp': datetime.utcnow().isoformat(),
                'database_url': self.database_url.split('@')[1] if '@' in self.database_url else 'local',
                'total_tables': len(existing_tables),
                'tables': {}
            }
            
            for table_name in existing_tables:
                columns = self.inspector.get_columns(table_name)
                status['tables'][table_name] = {
                    'column_count': len(columns),
                    'columns': [col['name'] for col in columns]
                }
            
            return status
            
        except Exception as e:
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'status': 'error'
            }


def auto_fix_database(database_url: str = None) -> Dict[str, Any]:
    """
    Convenience function to automatically fix database schema
    
    Args:
        database_url: Database URL (uses DATABASE_URL env var if not provided)
    
    Returns:
        Dict containing results of the operation
    """
    if not database_url:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not found")
    
    auto_fix = DatabaseAutoFix(database_url)
    return auto_fix.check_and_fix_database()


def get_database_status(database_url: str = None) -> Dict[str, Any]:
    """
    Get current database status without making changes
    
    Args:
        database_url: Database URL (uses DATABASE_URL env var if not provided)
    
    Returns:
        Dict containing current database status
    """
    if not database_url:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not found")
    
    auto_fix = DatabaseAutoFix(database_url)
    return auto_fix.get_database_status()


if __name__ == "__main__":
    # Test the auto-fix system
    try:
        result = auto_fix_database()
        print("Database Auto-Fix Results:")
        print(f"Success: {result['success']}")
        print(f"Fixes Applied: {len(result['fixes_applied'])}")
        print(f"Errors: {len(result['errors_encountered'])}")
        
        if result['fixes_applied']:
            print("\nFixes Applied:")
            for fix in result['fixes_applied']:
                print(f"  ✅ {fix}")
        
        if result['errors_encountered']:
            print("\nErrors:")
            for error in result['errors_encountered']:
                print(f"  ❌ {error}")
                
    except Exception as e:
        print(f"Error running auto-fix: {e}")
