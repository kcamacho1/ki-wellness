#!/usr/bin/env python3
"""
Optimize Existing Images Script for Ki Wellness
Processes and re-uploads all existing images in R2 storage with mobile-friendly compression
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, Recipe
from services.r2_client import r2_client
from services.image_processor import image_processor


class ImageOptimizer:
    """
    Optimizes existing images in R2 storage
    """
    
    def __init__(self):
        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.total_savings = 0
        self.start_time = None
        
    def run_optimization(self, dry_run: bool = False, limit: int = None):
        """
        Run image optimization for all recipes
        
        Args:
            dry_run: If True, only show what would be processed
            limit: Maximum number of images to process (None for all)
        """
        print("🔄 Starting image optimization process...")
        print(f"📱 Mobile-friendly settings: 600x450px, 200KB max, WebP format")
        print(f"🔍 Mode: {'DRY RUN' if dry_run else 'LIVE PROCESSING'}")
        print("-" * 60)
        
        self.start_time = time.time()
        
        with app.app_context():
            # Get all recipes with images
            recipes = Recipe.query.filter(
                Recipe.image_path.isnot(None),
                Recipe.image_path != ''
            ).all()
            
            if limit:
                recipes = recipes[:limit]
                print(f"📊 Processing {len(recipes)} recipes (limited to {limit})")
            else:
                print(f"📊 Found {len(recipes)} recipes with images")
            
            if not recipes:
                print("❌ No recipes with images found")
                return
            
            # Process each recipe
            for i, recipe in enumerate(recipes, 1):
                print(f"\n[{i}/{len(recipes)}] Processing recipe: {recipe.name}")
                self.process_recipe_image(recipe, dry_run)
            
            # Show summary
            self.show_summary(dry_run)
    
    def process_recipe_image(self, recipe: Recipe, dry_run: bool = False):
        """
        Process a single recipe's image
        """
        try:
            # Check if image is already optimized
            if recipe.image_path and recipe.image_path.endswith('_optimized.webp'):
                print(f"  ⏭️  Already optimized: {recipe.image_path}")
                self.skipped_count += 1
                return
            
            # Get current image info
            current_image_path = recipe.image_path
            if not current_image_path:
                print(f"  ⏭️  No image path")
                self.skipped_count += 1
                return
            
            # Check if it's an R2 URL
            if not (current_image_path.startswith('http') and 
                   ('objects.kiwellness.org' in current_image_path or 
                    '.r2.cloudflarestorage.com' in current_image_path)):
                print(f"  ⏭️  Not an R2 image: {current_image_path}")
                self.skipped_count += 1
                return
            
            # Extract object key from URL
            object_key = self.extract_object_key(current_image_path)
            if not object_key:
                print(f"  ❌ Could not extract object key from: {current_image_path}")
                self.error_count += 1
                return
            
            print(f"  📥 Downloading: {object_key}")
            
            if dry_run:
                print(f"  🔍 DRY RUN: Would optimize {object_key}")
                self.processed_count += 1
                return
            
            # Download current image
            try:
                response = r2_client.s3_client.get_object(
                    Bucket=r2_client.bucket_name,
                    Key=object_key
                )
                original_data = response['Body'].read()
                original_size = len(original_data)
                
                print(f"  📊 Original size: {original_size / 1024:.1f}KB")
                
            except Exception as e:
                print(f"  ❌ Failed to download: {e}")
                self.error_count += 1
                return
            
            # Process image
            print(f"  🔄 Processing image...")
            processed_result = image_processor.process_recipe_image(original_data, recipe.name)
            
            if not processed_result['success']:
                print(f"  ❌ Processing failed: {processed_result['error']}")
                self.error_count += 1
                return
            
            # Calculate savings
            optimized_size = processed_result['optimized_size']
            savings = original_size - optimized_size
            savings_percent = (savings / original_size) * 100 if original_size > 0 else 0
            
            print(f"  ✅ Optimized: {optimized_size / 1024:.1f}KB "
                  f"({savings_percent:.1f}% reduction)")
            
            # Generate new object key
            new_object_key = self.generate_optimized_key(object_key)
            
            # Upload optimized image
            print(f"  📤 Uploading optimized image...")
            upload_result = r2_client.upload_file(
                file_data=processed_result['optimized_data'],
                filename=processed_result['filename'],
                folder='optimized',
                process_image=False  # Already processed
            )
            
            if not upload_result:
                print(f"  ❌ Upload failed")
                self.error_count += 1
                return
            
            # Update recipe with new image path
            recipe.image_path = upload_result['public_url']
            db.session.commit()
            
            print(f"  ✅ Updated recipe with optimized image")
            
            # Update statistics
            self.processed_count += 1
            self.total_savings += savings
            
            # Clean up old image (optional)
            try:
                r2_client.delete_file(object_key)
                print(f"  🗑️  Deleted old image")
            except Exception as e:
                print(f"  ⚠️  Could not delete old image: {e}")
            
        except Exception as e:
            print(f"  ❌ Error processing recipe {recipe.id}: {e}")
            self.error_count += 1
    
    def extract_object_key(self, url: str) -> str:
        """
        Extract object key from R2 URL
        """
        try:
            if 'objects.kiwellness.org' in url:
                # Custom domain format
                parts = url.split('objects.kiwellness.org/')
                if len(parts) > 1:
                    return parts[1]
            elif '.r2.cloudflarestorage.com' in url:
                # R2 domain format
                parts = url.split('.r2.cloudflarestorage.com/')
                if len(parts) > 1:
                    return parts[1]
            return None
        except Exception:
            return None
    
    def generate_optimized_key(self, original_key: str) -> str:
        """
        Generate optimized object key
        """
        # Add optimized prefix and change extension to .webp
        name, ext = os.path.splitext(original_key)
        return f"{name}_optimized.webp"
    
    def show_summary(self, dry_run: bool = False):
        """
        Show optimization summary
        """
        elapsed_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 OPTIMIZATION SUMMARY")
        print("=" * 60)
        
        if dry_run:
            print(f"🔍 DRY RUN - No changes made")
        
        print(f"✅ Processed: {self.processed_count} images")
        print(f"⏭️  Skipped: {self.skipped_count} images")
        print(f"❌ Errors: {self.error_count} images")
        
        if self.total_savings > 0:
            print(f"💾 Total savings: {self.total_savings / 1024:.1f}KB")
            print(f"📱 Average size: {self.total_savings / max(self.processed_count, 1) / 1024:.1f}KB per image")
        
        print(f"⏱️  Time taken: {elapsed_time:.1f} seconds")
        
        if not dry_run and self.processed_count > 0:
            print(f"\n🎉 Image optimization complete!")
            print(f"📱 All images are now mobile-friendly and compressed")
        elif dry_run:
            print(f"\n🔍 Dry run complete - no changes made")
            print(f"💡 Run without --dry-run to apply optimizations")


def main():
    """
    Main function with command line arguments
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimize existing images in R2 storage')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be processed without making changes')
    parser.add_argument('--limit', type=int, 
                       help='Limit number of images to process')
    parser.add_argument('--confirm', action='store_true',
                       help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # Confirmation prompt
    if not args.dry_run and not args.confirm:
        print("⚠️  This will process and re-upload ALL existing images in R2 storage.")
        print("📱 Images will be compressed to mobile-friendly sizes (200KB max, WebP format).")
        print("🗑️  Old images will be deleted after successful optimization.")
        print()
        
        response = input("Are you sure you want to continue? (yes/no): ").lower()
        if response not in ['yes', 'y']:
            print("❌ Operation cancelled")
            return
    
    # Run optimization
    optimizer = ImageOptimizer()
    optimizer.run_optimization(
        dry_run=args.dry_run,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
