#!/usr/bin/env python3
"""
Simple Recipe Image Fetcher Script
Fetches relevant image URLs for community recipes and saves them directly to the database.
No file downloads - just URL storage!
"""

import os
import requests
import time
import sqlite3
import re
from urllib.parse import quote_plus
import random

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ki_wellness.db')

def get_database_connection():
    """Get database connection based on environment"""
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
        return sqlite3.connect(db_path), 'sqlite'
    else:
        # For PostgreSQL, you'd use psycopg2
        import psycopg2
        return psycopg2.connect(DATABASE_URL), 'postgresql'

def search_images_simple(query):
    """Search for images using Unsplash Source API (no API keys required)"""
    # Use Unsplash Source API which provides direct image URLs
    # This is free and doesn't require API keys
    
    # Clean the query for URL safety
    clean_query = re.sub(r'[^\w\s]', ' ', query).strip().replace(' ', ',')
    
    # Generate different image variations for variety
    image_variations = [
        f"https://source.unsplash.com/400x300/?{clean_query},food",
        f"https://source.unsplash.com/400x300/?{clean_query},cooking",
        f"https://source.unsplash.com/400x300/?{clean_query},recipe"
    ]
    
    # Return a random variation for variety
    return random.choice(image_variations)

def clean_filename(filename):
    """Clean filename for safe saving"""
    # Remove special characters and replace spaces with underscores
    cleaned = re.sub(r'[^\w\s-]', '', filename)
    cleaned = re.sub(r'[-\s]+', '_', cleaned)
    return cleaned.lower()[:50]  # Limit length

def generate_search_queries(recipe_name, category):
    """Generate search queries for image search"""
    queries = []
    
    # Clean the recipe name
    clean_name = re.sub(r'[^\w\s]', ' ', recipe_name).strip()
    
    # Add recipe name as primary query
    queries.append(clean_name)
    
    # Add category-based queries
    if category:
        queries.append(f"{category} food")
        queries.append(f"{category} recipe")
    
    # Add food-related terms
    food_terms = ["food", "cooking", "recipe", "meal", "dish"]
    for term in food_terms:
        queries.append(f"{clean_name} {term}")
    
    return queries

def fetch_recipe_images():
    """Main function to fetch image URLs for recipes without images"""
    print("🚀 Starting Recipe Image URL Fetching...")
    print("📝 This will save image URLs directly to the database (no file downloads)")
    
    # Get database connection
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        # Get recipes without images (community recipes)
        if db_type == 'sqlite':
            query = """
            SELECT r.id, r.name, r.category, r.image_path, r.user_id
            FROM recipe r
            WHERE r.image_path IS NULL 
            AND r.is_public = 1
            AND r.user_id != 1  -- Exclude admin/your own recipes
            ORDER BY r.created_at DESC
            LIMIT 50  -- Process up to 50 recipes
            """
        else:  # PostgreSQL
            query = """
            SELECT r.id, r.name, r.category, r.image_path, r.user_id
            FROM recipe r
            WHERE r.image_path IS NULL 
            AND r.is_public = true
            AND r.user_id != 1  -- Exclude admin/your own recipes
            ORDER BY r.created_at DESC
            LIMIT 50  -- Process up to 50 recipes
            """
        
        cursor.execute(query)
        recipes = cursor.fetchall()
        
        print(f"📊 Found {len(recipes)} community recipes without images")
        
        if not recipes:
            print("✨ All recipes already have images!")
            return
        
        # Process each recipe
        success_count = 0
        for recipe_id, recipe_name, category, image_path, user_id in recipes:
            print(f"\n🔍 Processing: {recipe_name} (Category: {category})")
            
            # Generate search queries
            search_queries = generate_search_queries(recipe_name, category)
            
            # Use the first query to get an image URL
            primary_query = search_queries[0]
            print(f"  Searching for: '{primary_query}'")
            
            # Get image URL
            image_url = search_images_simple(primary_query)
            
            if image_url:
                print(f"  🖼️  Found image: {image_url}")
                
                # Update database with the image URL
                if db_type == 'sqlite':
                    update_query = "UPDATE recipe SET image_path = ? WHERE id = ?"
                else:  # PostgreSQL
                    update_query = "UPDATE recipe SET image_path = %s WHERE id = %s"
                cursor.execute(update_query, (image_url, recipe_id))
                conn.commit()
                
                print(f"  💾 Updated database for recipe {recipe_id}")
                success_count += 1
            else:
                print(f"  ⚠️  No suitable image found for: {recipe_name}")
            
            # Add delay to be respectful to the image service
            time.sleep(1)
        
        print(f"\n🎉 Image URL fetching completed!")
        print(f"✅ Successfully updated {success_count} out of {len(recipes)} recipes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def preview_recipe_images():
    """Preview what images would be fetched without making changes"""
    print("🔍 Preview Mode - No database changes will be made")
    print("=" * 50)
    
    # Get database connection
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        # Get recipes without images
        if db_type == 'sqlite':
            query = """
            SELECT r.id, r.name, r.category, r.image_path, r.user_id
            FROM recipe r
            WHERE r.image_path IS NULL 
            AND r.is_public = 1
            AND r.user_id != 1
            ORDER BY r.created_at DESC
            LIMIT 10  -- Preview first 10
            """
        else:  # PostgreSQL
            query = """
            SELECT r.id, r.name, r.category, r.image_path, r.user_id
            FROM recipe r
            WHERE r.image_path IS NULL 
            AND r.is_public = true
            AND r.user_id != 1
            ORDER BY r.created_at DESC
            LIMIT 10  -- Preview first 10
            """
        
        cursor.execute(query)
        recipes = cursor.fetchall()
        
        print(f"📊 Found {len(recipes)} community recipes without images")
        
        if not recipes:
            print("✨ All recipes already have images!")
            return
        
        print("\n📋 Preview of what would be fetched:")
        print("-" * 50)
        
        for recipe_id, recipe_name, category, image_path, user_id in recipes:
            print(f"\nRecipe: {recipe_name}")
            print(f"Category: {category}")
            
            # Generate search query
            search_queries = generate_search_queries(recipe_name, category)
            primary_query = search_queries[0]
            
            # Show what image URL would be generated
            image_url = search_images_simple(primary_query)
            print(f"Image URL: {image_url}")
        
        print("\n" + "=" * 50)
        print("This is just a preview. Run the script again to actually update the database.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main entry point"""
    print("🍳 Recipe Image URL Fetcher")
    print("=" * 50)
    print("This script will fetch relevant image URLs for community recipes")
    print("and save them directly to the database.")
    print()
    print("Options:")
    print("1. Preview what would be fetched (no changes)")
    print("2. Fetch and save image URLs to database")
    print("3. Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            preview_recipe_images()
            break
        elif choice == '2':
            # Ask for confirmation
            response = input("This will update the database. Continue? (y/n): ").lower().strip()
            if response == 'y':
                fetch_recipe_images()
            else:
                print("Operation cancelled.")
            break
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
