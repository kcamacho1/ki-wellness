#!/usr/bin/env python3
"""
Database Auto-Fix Command Line Tool
===================================

This script provides a command-line interface for the database auto-fix system.
It can check database status, apply fixes, and provide detailed reporting.

Usage:
    python auto_fix_database.py [--check] [--fix] [--status] [--verbose]

Author: Ki Wellness Team
Version: 2.0
"""

import os
import sys
import argparse
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.database_auto_fix import auto_fix_database, get_database_status

def print_banner():
    """Print application banner"""
    print("🔧 Ki Wellness - Database Auto-Fix System")
    print("=" * 50)
    print()

def print_status(status_data):
    """Print database status in a formatted way"""
    print("📊 Database Status Report")
    print("-" * 30)
    print(f"Timestamp: {status_data.get('timestamp', 'Unknown')}")
    print(f"Database: {status_data.get('database_url', 'Unknown')}")
    print(f"Total Tables: {status_data.get('total_tables', 0)}")
    print()
    
    if 'tables' in status_data:
        print("📋 Table Details:")
        for table_name, table_info in status_data['tables'].items():
            print(f"  📄 {table_name}")
            print(f"     Columns: {table_info.get('column_count', 0)}")
            print(f"     Column names: {', '.join(table_info.get('columns', []))}")
            print()
    
    if 'error' in status_data:
        print(f"❌ Error: {status_data['error']}")

def print_fix_results(results):
    """Print auto-fix results in a formatted way"""
    print("🔧 Auto-Fix Results")
    print("-" * 20)
    print(f"Timestamp: {results.get('timestamp', 'Unknown')}")
    print(f"Success: {'✅ Yes' if results.get('success', False) else '❌ No'}")
    print()
    
    summary = results.get('summary', {})
    print(f"Total Fixes Applied: {summary.get('total_fixes', 0)}")
    print(f"Total Errors: {summary.get('total_errors', 0)}")
    print(f"Status: {summary.get('status', 'unknown').upper()}")
    print()
    
    if results.get('fixes_applied'):
        print("✅ Fixes Applied:")
        for fix in results['fixes_applied']:
            print(f"  ➕ {fix}")
        print()
    
    if results.get('errors_encountered'):
        print("❌ Errors Encountered:")
        for error in results['errors_encountered']:
            print(f"  💥 {error}")
        print()

def main():
    """Main function to handle command line arguments and execute operations"""
    parser = argparse.ArgumentParser(
        description="Ki Wellness Database Auto-Fix System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python auto_fix_database.py --status          # Check current database status
  python auto_fix_database.py --fix             # Apply auto-fixes
  python auto_fix_database.py --check           # Check what needs fixing
  python auto_fix_database.py --fix --verbose   # Apply fixes with verbose output
        """
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current database status without making changes'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check what needs to be fixed (dry run)'
    )
    
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Apply database fixes automatically'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any([args.status, args.check, args.fix]):
        parser.print_help()
        return
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
    
    print_banner()
    
    try:
        # Check if DATABASE_URL is available
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ Error: DATABASE_URL environment variable not found")
            print("Please set the DATABASE_URL environment variable before running this script.")
            sys.exit(1)
        
        # Show status
        if args.status:
            print("🔍 Checking database status...")
            status = get_database_status()
            
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print_status(status)
        
        # Check what needs fixing (dry run)
        if args.check:
            print("🔍 Checking what needs to be fixed...")
            status = get_database_status()
            
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print_status(status)
                print("\n💡 To apply fixes, run: python auto_fix_database.py --fix")
        
        # Apply fixes
        if args.fix:
            print("🔧 Applying database fixes...")
            print("⚠️  This will modify your database schema!")
            print()
            
            # Ask for confirmation unless --verbose is used
            if not args.verbose:
                response = input("Do you want to continue? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("❌ Operation cancelled by user")
                    return
            
            results = auto_fix_database()
            
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print_fix_results(results)
            
            # Exit with appropriate code
            if results.get('success', False):
                print("🎉 Database auto-fix completed successfully!")
                sys.exit(0)
            else:
                print("⚠️  Database auto-fix completed with some issues.")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
