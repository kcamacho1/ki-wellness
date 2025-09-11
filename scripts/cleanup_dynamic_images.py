#!/usr/bin/env python3
"""
Cleanup script for dynamic images
Removes dynamic_image_url from recipes that are older than specified days
"""

import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, Recipe
from config.environment import get_environment_detector

def cleanup_old_dynamic_images(days_old=30):
    """
    Remove dynamic_image_url from recipes older than specified days
    
    Args:
        days_old (int): Number of days old recipes to clean up
    """
    with app.app_context():
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find recipes with dynamic images older than cutoff
            old_recipes = Recipe.query.filter(
                Recipe.dynamic_image_url.isnot(None),
                Recipe.created_at < cutoff_date
            ).all()
            
            print(f"Found {len(old_recipes)} recipes with dynamic images older than {days_old} days")
            
            if not old_recipes:
                print("No old dynamic images to clean up")
                return True
            
            # Clear dynamic_image_url for old recipes
            for recipe in old_recipes:
                recipe.dynamic_image_url = None
                print(f"Cleared dynamic image for recipe: {recipe.name} (ID: {recipe.id})")
            
            # Commit changes
            db.session.commit()
            print(f"✅ Successfully cleaned up {len(old_recipes)} old dynamic images")
            return True
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            db.session.rollback()
            return False

def get_dynamic_image_stats():
    """Get statistics about dynamic images"""
    with app.app_context():
        try:
            total_recipes = Recipe.query.count()
            recipes_with_dynamic_images = Recipe.query.filter(
                Recipe.dynamic_image_url.isnot(None)
            ).count()
            
            print(f"📊 Dynamic Image Statistics:")
            print(f"   Total recipes: {total_recipes}")
            print(f"   Recipes with dynamic images: {recipes_with_dynamic_images}")
            print(f"   Percentage with dynamic images: {(recipes_with_dynamic_images/total_recipes*100):.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cleanup old dynamic images")
    parser.add_argument("--days", type=int, default=30, help="Number of days old to clean up (default: 30)")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without actually doing it")
    
    args = parser.parse_args()
    
    if args.stats:
        success = get_dynamic_image_stats()
    else:
        if args.dry_run:
            print(f"DRY RUN: Would clean up dynamic images older than {args.days} days")
            # In a real dry run, you'd query and show what would be cleaned
            success = True
        else:
            success = cleanup_old_dynamic_images(args.days)
    
    sys.exit(0 if success else 1)
