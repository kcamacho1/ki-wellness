#!/usr/bin/env python3
"""
Add Pexels Images to Recipes Script
Adds dynamic images to existing recipes that don't have images
Run this script separately from the main application
"""

import sys
import os
import time
import hashlib
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db, Recipe
from services.pexels_client import pexels_client


def add_images_to_recipes():
    """
    Add Pexels images to recipes that don't have images
    """
    
    with app.app_context():
        print("🔍 Finding recipes without images...")
        
        # Find recipes without images
        recipes_without_images = Recipe.query.filter(
            db.and_(
                db.or_(
                    Recipe.image_path.is_(None),
                    Recipe.image_path == '',
                    Recipe.dynamic_image_url.is_(None),
                    Recipe.dynamic_image_url == ''
                )
            )
        ).all()
        
        print(f"📊 Found {len(recipes_without_images)} recipes without images")
        
        if not recipes_without_images:
            print("✅ All recipes already have images!")
            return
        
        # Check if Pexels API is available
        if not pexels_client.api_key:
            print("❌ Pexels API key not configured. Please set PEXELS_API_KEY in your environment.")
            return
        
        print(f"🚀 Starting to add images to {len(recipes_without_images)} recipes...")
        print("⏱️  This may take a while due to API rate limits...")
        
        success_count = 0
        error_count = 0
        
        for i, recipe in enumerate(recipes_without_images, 1):
            print(f"\n📝 Processing recipe {i}/{len(recipes_without_images)}: {recipe.name}")
            
            try:
                # Convert recipe to dict for Pexels search
                recipe_data = {
                    'name': recipe.name,
                    'description': recipe.description,
                    'category': recipe.category,
                    'ingredients': [
                        {
                            'food_name': ing.food_name,
                            'amount': ing.amount,
                            'unit': ing.unit
                        }
                        for ing in recipe.ingredients
                    ]
                }
                
                # Search for image
                image_result = pexels_client.search_food_image(recipe_data)
                
                if image_result:
                    print(f"  🖼️  Found image: {image_result['alt']}")
                    
                    # Store image in R2 if available
                    from services.r2_client import r2_client
                    if r2_client and r2_client.is_available():
                        try:
                            # Download and store image in R2
                            stored_url = r2_client.upload_from_url(
                                url=image_result['url'],
                                filename=f"recipe_{recipe.id}_{hashlib.md5(image_result['query'].encode()).hexdigest()[:8]}.jpg",
                                folder="dynamic-images"
                            )
                            
                            if stored_url:
                                # Update recipe with stored image
                                recipe.dynamic_image_url = stored_url['public_url']
                                recipe.image_path = stored_url['public_url']
                                print(f"  ✅ Stored image in R2: {stored_url['public_url']}")
                            else:
                                # Fallback to direct Pexels URL
                                recipe.dynamic_image_url = image_result['url']
                                print(f"  ⚠️  Using direct Pexels URL: {image_result['url']}")
                        except Exception as e:
                            print(f"  ⚠️  R2 upload failed: {e}, using direct Pexels URL")
                            recipe.dynamic_image_url = image_result['url']
                    else:
                        # No R2 available, use direct Pexels URL
                        recipe.dynamic_image_url = image_result['url']
                        print(f"  ⚠️  R2 not available, using direct Pexels URL: {image_result['url']}")
                    
                    # Commit the changes
                    db.session.commit()
                    success_count += 1
                    print(f"  ✅ Updated recipe with image")
                    
                else:
                    print(f"  ❌ No image found for recipe: {recipe.name}")
                    error_count += 1
                
                # Rate limiting - wait between requests
                if i < len(recipes_without_images):  # Don't wait after the last request
                    print(f"  ⏳ Waiting 1 second for rate limiting...")
                    time.sleep(1)
                
            except Exception as e:
                print(f"  ❌ Error processing recipe {recipe.name}: {e}")
                error_count += 1
                db.session.rollback()
        
        print(f"\n🎉 Image addition complete!")
        print(f"✅ Successfully added images to {success_count} recipes")
        print(f"❌ Failed to add images to {error_count} recipes")
        
        # Show API usage stats
        stats = pexels_client.get_image_stats()
        print(f"\n📊 API Usage Statistics:")
        print(f"  Hourly requests: {stats['hourly_requests']}/{stats['hourly_limit']}")
        print(f"  Monthly requests: {stats['monthly_requests']}/{stats['monthly_limit']}")
        print(f"  Cache size: {stats['cache_size']} images")


def show_recipe_stats():
    """
    Show statistics about recipes and their images
    """
    with app.app_context():
        print("📊 Recipe Image Statistics:")
        
        total_recipes = Recipe.query.count()
        recipes_with_images = Recipe.query.filter(
            db.or_(
                Recipe.image_path.isnot(None),
                Recipe.dynamic_image_url.isnot(None)
            )
        ).count()
        
        recipes_without_images = total_recipes - recipes_with_images
        
        print(f"  Total recipes: {total_recipes}")
        print(f"  Recipes with images: {recipes_with_images}")
        print(f"  Recipes without images: {recipes_without_images}")
        
        if recipes_without_images > 0:
            print(f"\n🔍 Recipes without images:")
            recipes_without = Recipe.query.filter(
                db.and_(
                    db.or_(
                        Recipe.image_path.is_(None),
                        Recipe.image_path == '',
                        Recipe.dynamic_image_url.is_(None),
                        Recipe.dynamic_image_url == ''
                    )
                )
            ).limit(10).all()
            
            for recipe in recipes_without:
                print(f"  - {recipe.name} (ID: {recipe.id}, Category: {recipe.category})")
            
            if len(recipes_without) == 10 and recipes_without_images > 10:
                print(f"  ... and {recipes_without_images - 10} more")


if __name__ == "__main__":
    print("🍽️  Ki Wellness - Add Pexels Images to Recipes")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        show_recipe_stats()
    else:
        print("This script will add Pexels images to recipes that don't have images.")
        print("Make sure you have PEXELS_API_KEY configured in your environment.")
        print()
        
        response = input("Do you want to continue? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            add_images_to_recipes()
        else:
            print("Operation cancelled.")
