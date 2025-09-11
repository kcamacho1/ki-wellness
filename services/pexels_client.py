#!/usr/bin/env python3
"""
Pexels API Client for Ki Wellness
Handles dynamic image fetching for recipe placeholders
"""

import requests
import json
import time
import hashlib
from typing import Dict, Any, Optional, List
from config.environment import get_environment_detector
from services.r2_client import r2_client


class PexelsClient:
    """
    Pexels API client for fetching food images
    """
    
    def __init__(self):
        self.env_detector = get_environment_detector()
        self.config = self.env_detector.get_pexels_config()
        self.api_key = self.config.get('PEXELS_API_KEY')
        self.base_url = self.config.get('PEXELS_API_URL')
        self.rate_limit = self.config.get('PEXELS_RATE_LIMIT', 200)
        self.monthly_limit = self.config.get('PEXELS_MONTHLY_LIMIT', 20000)
        self.image_size = self.config.get('PEXELS_IMAGE_SIZE', 'medium')
        self.orientation = self.config.get('PEXELS_ORIENTATION', 'landscape')
        self.cache_duration = self.config.get('PEXELS_CACHE_DURATION', 7 * 24 * 60 * 60)
        self.free_only = self.config.get('PEXELS_FREE_ONLY', True)
        self.attribution_required = self.config.get('PEXELS_ATTRIBUTION_REQUIRED', True)
        
        # Rate limiting tracking
        self.request_count = 0
        self.last_reset = time.time()
        self.monthly_count = 0
        self.monthly_reset = time.time()
        
        # Cache for storing fetched images
        self.image_cache = {}
    
    def _is_rate_limited(self) -> bool:
        """
        Check if we're hitting rate limits
        """
        current_time = time.time()
        
        # Reset hourly counter
        if current_time - self.last_reset >= 3600:  # 1 hour
            self.request_count = 0
            self.last_reset = current_time
        
        # Reset monthly counter
        if current_time - self.monthly_reset >= 30 * 24 * 3600:  # 30 days
            self.monthly_count = 0
            self.monthly_reset = current_time
        
        return (self.request_count >= self.rate_limit or 
                self.monthly_count >= self.monthly_limit)
    
    def _increment_counters(self):
        """
        Increment rate limiting counters
        """
        self.request_count += 1
        self.monthly_count += 1
    
    def _get_cached_image(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached image if available and not expired
        """
        if query in self.image_cache:
            cached_data = self.image_cache[query]
            if time.time() - cached_data['timestamp'] < self.cache_duration:
                return cached_data['data']
            else:
                # Remove expired cache entry
                del self.image_cache[query]
        return None
    
    def _cache_image(self, query: str, data: Dict[str, Any]):
        """
        Cache image data with timestamp
        """
        self.image_cache[query] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def _generate_search_query(self, recipe: Dict[str, Any]) -> str:
        """
        Generate search query from recipe data
        """
        query_parts = []
        
        # Add category if available
        if recipe.get('category'):
            category = recipe['category'].lower()
            category_mappings = {
                'breakfast': 'healthy breakfast',
                'lunch': 'fresh lunch',
                'dinner': 'dinner meal',
                'snack': 'healthy snack',
                'dessert': 'dessert sweet',
                'soup': 'soup bowl',
                'salad': 'fresh salad',
                'smoothie': 'smoothie bowl',
                'pasta': 'pasta dish',
                'rice': 'rice dish',
                'seafood': 'seafood fish',
                'vegetarian': 'vegetarian meal',
                'vegan': 'vegan food',
                'keto': 'keto meal',
                'paleo': 'paleo food',
                'gluten-free': 'gluten free food'
            }
            query_parts.append(category_mappings.get(category, category))
        
        # Add main ingredients
        if recipe.get('ingredients') and isinstance(recipe['ingredients'], list):
            main_ingredients = []
            for ingredient in recipe['ingredients'][:3]:  # First 3 ingredients
                if isinstance(ingredient, dict):
                    ingredient_name = ingredient.get('food_name') or ingredient.get('name', '')
                else:
                    ingredient_name = str(ingredient)
                
                if ingredient_name:
                    main_ingredients.append(ingredient_name.lower())
            
            if main_ingredients:
                query_parts.extend(main_ingredients)
        
        # Add recipe name if no other keywords
        if not query_parts and recipe.get('name'):
            recipe_name = recipe['name'].lower()
            # Remove common words and keep meaningful ones
            common_words = {'recipe', 'dish', 'food', 'meal', 'the', 'a', 'an', 'and', 'or', 'with'}
            words = [word for word in recipe_name.split() if word not in common_words]
            query_parts.extend(words[:3])  # First 3 meaningful words
        
        # Fallback to generic food
        if not query_parts:
            query_parts = ['food meal']
        
        return ' '.join(query_parts[:5])  # Limit to 5 keywords
    
    def search_food_image(self, recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Search for food image based on recipe data
        """
        if not self.api_key:
            return None
        
        # Check rate limits
        if self._is_rate_limited():
            return None
        
        # Generate search query
        query = self._generate_search_query(recipe)
        
        # Check cache first
        cached_result = self._get_cached_image(query)
        if cached_result:
            return cached_result
        
        try:
            # Make API request with security headers
            headers = {
                'Authorization': self.api_key,
                'User-Agent': 'Ki-Wellness/1.0',
                'Accept': 'application/json',
                'Connection': 'close'  # Prevent connection reuse for security
            }
            
            params = {
                'query': query,
                'per_page': 10,  # Get multiple options
                'orientation': self.orientation,
                'size': self.image_size
            }
            
            # Pexels API only returns free photos by default
            # All photos on Pexels are free to use under the Pexels License
            
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            self._increment_counters()
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('photos') and len(data['photos']) > 0:
                    # Select the first photo
                    photo = data['photos'][0]
                    
                    result = {
                        'url': photo['src'][self.image_size],
                        'alt': photo.get('alt', f"{query} food image"),
                        'photographer': photo.get('photographer', 'Unknown'),
                        'photographer_url': photo.get('photographer_url', ''),
                        'pexels_url': photo.get('url', ''),
                        'query': query,
                        'cached': False,
                        'license': 'Pexels License (Free to use)',
                        'attribution': f"Photo by {photo.get('photographer', 'Unknown')} on Pexels" if self.attribution_required else None,
                        'free_use': True
                    }
                    
                    # Cache the result
                    self._cache_image(query, result)
                    
                    return result
                else:
                    # No photos found, try a more generic search
                    return self._fallback_search()
            else:
                print(f"Pexels API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Pexels API request failed: {e}")
            return None
    
    def _fallback_search(self) -> Optional[Dict[str, Any]]:
        """
        Fallback to generic food search if specific search fails
        """
        try:
            headers = {
                'Authorization': self.api_key,
                'User-Agent': 'Ki-Wellness/1.0'
            }
            
            params = {
                'query': 'food meal',
                'per_page': 5,
                'orientation': self.orientation,
                'size': self.image_size
            }
            
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('photos') and len(data['photos']) > 0:
                    photo = data['photos'][0]
                    
                    return {
                        'url': photo['src'][self.image_size],
                        'alt': 'Food meal image',
                        'photographer': photo.get('photographer', 'Unknown'),
                        'photographer_url': photo.get('photographer_url', ''),
                        'pexels_url': photo.get('url', ''),
                        'query': 'food meal',
                        'cached': False,
                        'license': 'Pexels License (Free to use)',
                        'attribution': f"Photo by {photo.get('photographer', 'Unknown')} on Pexels" if self.attribution_required else None,
                        'free_use': True
                    }
            
        except requests.exceptions.RequestException as e:
            print(f"Pexels fallback search failed: {e}")
        
        return None
    
    def store_image_in_r2(self, image_url: str, recipe_id: int, query: str) -> Optional[str]:
        """
        Download image from Pexels and store in R2
        
        Args:
            image_url: Pexels image URL
            recipe_id: Recipe ID for organization
            query: Search query used to find the image
        
        Returns:
            R2 public URL if successful, None otherwise
        """
        if not r2_client.is_available():
            print("⚠️ R2 storage not available, skipping image storage")
            return None
        
        try:
            # Generate filename based on recipe ID and query
            filename = f"recipe_{recipe_id}_{hashlib.md5(query.encode()).hexdigest()[:8]}.jpg"
            
            # Upload to R2
            result = r2_client.upload_from_url(
                url=image_url,
                filename=filename,
                folder="dynamic-images"
            )
            
            if result:
                print(f"✅ Stored dynamic image in R2: {result['public_url']}")
                return result['public_url']
            else:
                print("❌ Failed to store image in R2")
                return None
                
        except Exception as e:
            print(f"❌ Error storing image in R2: {e}")
            return None
    
    def get_image_stats(self) -> Dict[str, Any]:
        """
        Get current API usage statistics
        """
        current_time = time.time()
        
        return {
            'hourly_requests': self.request_count,
            'hourly_limit': self.rate_limit,
            'monthly_requests': self.monthly_count,
            'monthly_limit': self.monthly_limit,
            'cache_size': len(self.image_cache),
            'time_to_hourly_reset': max(0, 3600 - (current_time - self.last_reset)),
            'time_to_monthly_reset': max(0, 30 * 24 * 3600 - (current_time - self.monthly_reset))
        }
    
    def clear_cache(self):
        """
        Clear the image cache
        """
        self.image_cache.clear()


# Global instance
pexels_client = PexelsClient()
