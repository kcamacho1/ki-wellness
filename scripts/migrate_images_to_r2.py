#!/usr/bin/env python3
"""
Migration script to move existing recipe images to Cloudflare R2
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, Recipe
from services.r2_client import r2_client
from config.environment import get_environment_detector

def migrate_recipe_images():
    """Migrate existing recipe images to R2 storage"""
    with app.app_context():
        if not r2_client.is_available():
            print("❌ R2 storage not available. Please check your configuration.")
            return False
        
        # Find recipes with local images
        recipes_with_images = Recipe.query.filter(
            Recipe.image_path.isnot(None),
            Recipe.image_path.like('uploads/recipes/%')
        ).all()
        
        print(f"Found {len(recipes_with_images)} recipes with local images to migrate")
        
        if not recipes_with_images:
            print("No local images to migrate")
            return True
        
        migrated_count = 0
        failed_count = 0
        
        for recipe in recipes_with_images:
            try:
                # Build local file path
                local_path = os.path.join(app.static_folder, recipe.image_path)
                
                if not os.path.exists(local_path):
                    print(f"⚠️ Local file not found: {local_path}")
                    failed_count += 1
                    continue
                
                # Read file data
                with open(local_path, 'rb') as f:
                    file_data = f.read()
                
                # Generate R2 filename
                filename = os.path.basename(recipe.image_path)
                
                # Upload to R2
                result = r2_client.upload_file(
                    file_data=file_data,
                    filename=filename,
                    folder="migrated-uploads"
                )
                
                if result:
                    # Update recipe with R2 URL
                    recipe.image_path = result['public_url']
                    migrated_count += 1
                    print(f"✅ Migrated: {recipe.name} -> {result['public_url']}")
                else:
                    print(f"❌ Failed to upload: {recipe.name}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error migrating {recipe.name}: {e}")
                failed_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n📊 Migration Summary:")
            print(f"   ✅ Successfully migrated: {migrated_count}")
            print(f"   ❌ Failed: {failed_count}")
            print(f"   📁 Total processed: {len(recipes_with_images)}")
            return True
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
            db.session.rollback()
            return False

def migrate_dynamic_images():
    """Migrate dynamic images from Pexels URLs to R2 storage"""
    with app.app_context():
        if not r2_client.is_available():
            print("❌ R2 storage not available. Please check your configuration.")
            return False
        
        # Find recipes with Pexels dynamic images
        recipes_with_dynamic = Recipe.query.filter(
            Recipe.dynamic_image_url.isnot(None),
            Recipe.dynamic_image_url.like('https://images.pexels.com/%')
        ).all()
        
        print(f"Found {len(recipes_with_dynamic)} recipes with Pexels dynamic images to migrate")
        
        if not recipes_with_dynamic:
            print("No Pexels dynamic images to migrate")
            return True
        
        migrated_count = 0
        failed_count = 0
        
        for recipe in recipes_with_dynamic:
            try:
                # Upload Pexels image to R2
                result = r2_client.upload_from_url(
                    url=recipe.dynamic_image_url,
                    filename=f"dynamic_recipe_{recipe.id}.jpg",
                    folder="migrated-dynamic"
                )
                
                if result:
                    # Update recipe with R2 URL
                    recipe.dynamic_image_url = result['public_url']
                    migrated_count += 1
                    print(f"✅ Migrated dynamic image: {recipe.name} -> {result['public_url']}")
                else:
                    print(f"❌ Failed to migrate dynamic image: {recipe.name}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error migrating dynamic image for {recipe.name}: {e}")
                failed_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n📊 Dynamic Image Migration Summary:")
            print(f"   ✅ Successfully migrated: {migrated_count}")
            print(f"   ❌ Failed: {failed_count}")
            print(f"   📁 Total processed: {len(recipes_with_dynamic)}")
            return True
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
            db.session.rollback()
            return False

def get_migration_stats():
    """Get statistics about images that need migration"""
    with app.app_context():
        local_images = Recipe.query.filter(
            Recipe.image_path.isnot(None),
            Recipe.image_path.like('uploads/recipes/%')
        ).count()
        
        pexels_dynamic = Recipe.query.filter(
            Recipe.dynamic_image_url.isnot(None),
            Recipe.dynamic_image_url.like('https://images.pexels.com/%')
        ).count()
        
        r2_images = Recipe.query.filter(
            Recipe.image_path.isnot(None),
            Recipe.image_path.like('https://%')
        ).count()
        
        print(f"📊 Image Migration Statistics:")
        print(f"   📁 Local images to migrate: {local_images}")
        print(f"   🌐 Pexels dynamic images to migrate: {pexels_dynamic}")
        print(f"   ☁️ Already in R2/cloud: {r2_images}")
        print(f"   📊 Total recipes: {Recipe.query.count()}")
        
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate recipe images to Cloudflare R2")
    parser.add_argument("--type", choices=['local', 'dynamic', 'all'], default='all', 
                       help="Type of images to migrate")
    parser.add_argument("--stats", action="store_true", help="Show migration statistics only")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without doing it")
    
    args = parser.parse_args()
    
    if args.stats:
        success = get_migration_stats()
    else:
        if args.dry_run:
            print("DRY RUN: Would migrate the following images:")
            get_migration_stats()
            success = True
        else:
            success = True
            
            if args.type in ['local', 'all']:
                print("🔄 Migrating local recipe images...")
                success &= migrate_recipe_images()
            
            if args.type in ['dynamic', 'all']:
                print("\n🔄 Migrating dynamic images...")
                success &= migrate_dynamic_images()
    
    sys.exit(0 if success else 1)
