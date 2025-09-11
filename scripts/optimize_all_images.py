#!/usr/bin/env python3
"""
Comprehensive Image Optimization Script for Ki Wellness
Processes all images (recipe images, dynamic images, etc.) with mobile-friendly compression
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, Recipe
from services.r2_client import r2_client
from services.image_processor import image_processor


class ComprehensiveImageOptimizer:
    """
    Comprehensive image optimizer for all image types
    """
    
    def __init__(self):
        self.stats = {
            'recipes_processed': 0,
            'recipes_skipped': 0,
            'recipes_errors': 0,
            'dynamic_images_processed': 0,
            'dynamic_images_skipped': 0,
            'dynamic_images_errors': 0,
            'total_savings_bytes': 0,
            'total_original_size': 0,
            'total_optimized_size': 0
        }
        self.start_time = None
        
    def run_comprehensive_optimization(self, dry_run: bool = False, limit: int = None):
        """
        Run comprehensive image optimization
        
        Args:
            dry_run: If True, only show what would be processed
            limit: Maximum number of images to process (None for all)
        """
        print("🔄 Starting comprehensive image optimization...")
        print(f"📱 Mobile-friendly settings: 600x450px, 200KB max, WebP format")
        print(f"🔍 Mode: {'DRY RUN' if dry_run else 'LIVE PROCESSING'}")
        print("-" * 70)
        
        self.start_time = time.time()
        
        with app.app_context():
            # Process recipe images
            self.process_recipe_images(dry_run, limit)
            
            # Process dynamic images
            self.process_dynamic_images(dry_run, limit)
            
            # Show comprehensive summary
            self.show_comprehensive_summary(dry_run)
    
    def process_recipe_images(self, dry_run: bool = False, limit: int = None):
        """
        Process recipe images
        """
        print("\n📸 PROCESSING RECIPE IMAGES")
        print("-" * 40)
        
        recipes = Recipe.query.filter(
            Recipe.image_path.isnot(None),
            Recipe.image_path != ''
        ).all()
        
        if limit:
            recipes = recipes[:limit]
        
        print(f"📊 Found {len(recipes)} recipes with images")
        
        for i, recipe in enumerate(recipes, 1):
            print(f"\n[{i}/{len(recipes)}] Recipe: {recipe.name}")
            self.process_single_image(
                recipe.image_path, 
                f"recipe_{recipe.id}", 
                dry_run,
                update_callback=lambda new_url: self.update_recipe_image(recipe, new_url)
            )
    
    def process_dynamic_images(self, dry_run: bool = False, limit: int = None):
        """
        Process dynamic images (Pexels images stored in R2)
        """
        print("\n🖼️  PROCESSING DYNAMIC IMAGES")
        print("-" * 40)
        
        recipes = Recipe.query.filter(
            Recipe.dynamic_image_url.isnot(None),
            Recipe.dynamic_image_url != ''
        ).all()
        
        if limit:
            recipes = recipes[:limit]
        
        print(f"📊 Found {len(recipes)} recipes with dynamic images")
        
        for i, recipe in enumerate(recipes, 1):
            print(f"\n[{i}/{len(recipes)}] Dynamic: {recipe.name}")
            self.process_single_image(
                recipe.dynamic_image_url,
                f"dynamic_{recipe.id}",
                dry_run,
                update_callback=lambda new_url: self.update_dynamic_image(recipe, new_url)
            )
    
    def process_single_image(self, image_url: str, identifier: str, dry_run: bool = False, 
                           update_callback=None):
        """
        Process a single image
        """
        try:
            # Check if it's an R2 URL
            if not self.is_r2_url(image_url):
                print(f"  ⏭️  Not an R2 image: {image_url}")
                if 'recipe' in identifier:
                    self.stats['recipes_skipped'] += 1
                else:
                    self.stats['dynamic_images_skipped'] += 1
                return
            
            # Check if already optimized
            if image_url.endswith('_optimized.webp'):
                print(f"  ⏭️  Already optimized")
                if 'recipe' in identifier:
                    self.stats['recipes_skipped'] += 1
                else:
                    self.stats['dynamic_images_skipped'] += 1
                return
            
            # Extract object key
            object_key = self.extract_object_key(image_url)
            if not object_key:
                print(f"  ❌ Could not extract object key")
                if 'recipe' in identifier:
                    self.stats['recipes_errors'] += 1
                else:
                    self.stats['dynamic_images_errors'] += 1
                return
            
            print(f"  📥 Downloading: {object_key}")
            
            if dry_run:
                print(f"  🔍 DRY RUN: Would optimize {object_key}")
                if 'recipe' in identifier:
                    self.stats['recipes_processed'] += 1
                else:
                    self.stats['dynamic_images_processed'] += 1
                return
            
            # Download and process
            try:
                response = r2_client.s3_client.get_object(
                    Bucket=r2_client.bucket_name,
                    Key=object_key
                )
                original_data = response['Body'].read()
                original_size = len(original_data)
                
                print(f"  📊 Original: {original_size / 1024:.1f}KB")
                
                # Process image
                processed_result = image_processor.process_recipe_image(original_data, identifier)
                
                if not processed_result['success']:
                    print(f"  ❌ Processing failed: {processed_result['error']}")
                    if 'recipe' in identifier:
                        self.stats['recipes_errors'] += 1
                    else:
                        self.stats['dynamic_images_errors'] += 1
                    return
                
                # Calculate savings
                optimized_size = processed_result['optimized_size']
                savings = original_size - optimized_size
                savings_percent = (savings / original_size) * 100 if original_size > 0 else 0
                
                print(f"  ✅ Optimized: {optimized_size / 1024:.1f}KB "
                      f"({savings_percent:.1f}% reduction)")
                
                # Upload optimized image
                new_object_key = self.generate_optimized_key(object_key)
                upload_result = r2_client.upload_file(
                    file_data=processed_result['optimized_data'],
                    filename=processed_result['filename'],
                    folder='optimized',
                    process_image=False
                )
                
                if not upload_result:
                    print(f"  ❌ Upload failed")
                    if 'recipe' in identifier:
                        self.stats['recipes_errors'] += 1
                    else:
                        self.stats['dynamic_images_errors'] += 1
                    return
                
                # Update database
                if update_callback:
                    update_callback(upload_result['public_url'])
                
                # Update statistics
                if 'recipe' in identifier:
                    self.stats['recipes_processed'] += 1
                else:
                    self.stats['dynamic_images_processed'] += 1
                
                self.stats['total_savings_bytes'] += savings
                self.stats['total_original_size'] += original_size
                self.stats['total_optimized_size'] += optimized_size
                
                # Clean up old image
                try:
                    r2_client.delete_file(object_key)
                    print(f"  🗑️  Deleted old image")
                except Exception as e:
                    print(f"  ⚠️  Could not delete old image: {e}")
                
            except Exception as e:
                print(f"  ❌ Download/process failed: {e}")
                if 'recipe' in identifier:
                    self.stats['recipes_errors'] += 1
                else:
                    self.stats['dynamic_images_errors'] += 1
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            if 'recipe' in identifier:
                self.stats['recipes_errors'] += 1
            else:
                self.stats['dynamic_images_errors'] += 1
    
    def update_recipe_image(self, recipe: Recipe, new_url: str):
        """Update recipe image path"""
        recipe.image_path = new_url
        db.session.commit()
        print(f"  ✅ Updated recipe image path")
    
    def update_dynamic_image(self, recipe: Recipe, new_url: str):
        """Update dynamic image URL"""
        recipe.dynamic_image_url = new_url
        db.session.commit()
        print(f"  ✅ Updated dynamic image URL")
    
    def is_r2_url(self, url: str) -> bool:
        """Check if URL is an R2 URL"""
        return (url and url.startswith('http') and 
                ('objects.kiwellness.org' in url or '.r2.cloudflarestorage.com' in url))
    
    def extract_object_key(self, url: str) -> Optional[str]:
        """Extract object key from R2 URL"""
        try:
            if 'objects.kiwellness.org' in url:
                parts = url.split('objects.kiwellness.org/')
                return parts[1] if len(parts) > 1 else None
            elif '.r2.cloudflarestorage.com' in url:
                parts = url.split('.r2.cloudflarestorage.com/')
                return parts[1] if len(parts) > 1 else None
            return None
        except Exception:
            return None
    
    def generate_optimized_key(self, original_key: str) -> str:
        """Generate optimized object key"""
        name, ext = os.path.splitext(original_key)
        return f"{name}_optimized.webp"
    
    def show_comprehensive_summary(self, dry_run: bool = False):
        """Show comprehensive optimization summary"""
        elapsed_time = time.time() - self.start_time
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE OPTIMIZATION SUMMARY")
        print("=" * 70)
        
        if dry_run:
            print("🔍 DRY RUN - No changes made")
        
        print(f"📸 Recipe Images:")
        print(f"  ✅ Processed: {self.stats['recipes_processed']}")
        print(f"  ⏭️  Skipped: {self.stats['recipes_skipped']}")
        print(f"  ❌ Errors: {self.stats['recipes_errors']}")
        
        print(f"\n🖼️  Dynamic Images:")
        print(f"  ✅ Processed: {self.stats['dynamic_images_processed']}")
        print(f"  ⏭️  Skipped: {self.stats['dynamic_images_skipped']}")
        print(f"  ❌ Errors: {self.stats['dynamic_images_errors']}")
        
        total_processed = (self.stats['recipes_processed'] + 
                          self.stats['dynamic_images_processed'])
        
        if self.stats['total_savings_bytes'] > 0:
            total_savings_mb = self.stats['total_savings_bytes'] / (1024 * 1024)
            total_original_mb = self.stats['total_original_size'] / (1024 * 1024)
            total_optimized_mb = self.stats['total_optimized_size'] / (1024 * 1024)
            savings_percent = (self.stats['total_savings_bytes'] / 
                             self.stats['total_original_size'] * 100) if self.stats['total_original_size'] > 0 else 0
            
            print(f"\n💾 Storage Savings:")
            print(f"  📊 Original size: {total_original_mb:.2f}MB")
            print(f"  📊 Optimized size: {total_optimized_mb:.2f}MB")
            print(f"  💾 Total savings: {total_savings_mb:.2f}MB ({savings_percent:.1f}%)")
            print(f"  📱 Average per image: {total_optimized_mb / max(total_processed, 1) * 1024:.1f}KB")
        
        print(f"\n⏱️  Time taken: {elapsed_time:.1f} seconds")
        
        if not dry_run and total_processed > 0:
            print(f"\n🎉 Image optimization complete!")
            print(f"📱 All images are now mobile-friendly and compressed")
        elif dry_run:
            print(f"\n🔍 Dry run complete - no changes made")
            print(f"💡 Run without --dry-run to apply optimizations")


def main():
    """Main function with command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive image optimization for R2 storage')
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
    optimizer = ComprehensiveImageOptimizer()
    optimizer.run_comprehensive_optimization(
        dry_run=args.dry_run,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
