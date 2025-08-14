"""
Ki Wellness - Services Module
=============================

This module contains business logic, API integrations, and external service calls
for the Ki Wellness application. This helps separate concerns and improve maintainability.

Author: Ki Wellness Team
Version: 2.0
"""

import os
import json
import requests
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from flask import current_app, request
import pytz

# Fuzzy search imports
try:
    from fuzzywuzzy import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    print("⚠️  FuzzyWuzzy not available. Fuzzy search will be disabled.")

# Import models and utilities
from .models import db, User, UserProfile, FoodJournal, TokenUsage, APICosts
from .utils import ValidationUtils, SecurityUtils, TimeUtils, ConversionUtils, NotificationUtils

# OpenAI integration
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class SystemService:
    """Service class for system-wide operations and settings management"""
    
    @staticmethod
    def get_system_setting(key: str, default: Any = None) -> Any:
        """Get a system setting value"""
        try:
            from .models import SystemSettings
            setting = SystemSettings.query.filter_by(key=key).first()
            if setting:
                # For boolean settings, convert string 'true'/'false' to boolean
                if key in ['flexible_service_tier', 'openai_api_enabled', 'emergency_stop_active', 'new_accounts_enabled']:
                    if isinstance(setting.value, str):
                        return setting.value.lower() == 'true'
                    elif isinstance(setting.value, bool):
                        return setting.value
                    else:
                        return default
                # For numeric settings, return as string (let caller convert)
                elif key in ['presence_penalty', 'frequency_penalty', 'top_p', 'max_input_tokens', 'max_output_tokens', 'max_total_tokens']:
                    return setting.value
                # For other settings, return as is
                else:
                    return setting.value
            return default
        except Exception as e:
            print(f"Error getting system setting {key}: {e}")
            return default
    
    @staticmethod
    def set_system_setting(key: str, value: Any, description: Optional[str] = None, user_id: Optional[int] = None) -> bool:
        """Set a system setting value"""
        try:
            from .models import SystemSettings
            setting = SystemSettings.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
                setting.updated_at = datetime.utcnow()
                setting.updated_by = user_id
            else:
                setting = SystemSettings(
                    key=key,
                    value=str(value),
                    description=description,
                    updated_by=user_id
                )
                db.session.add(setting)
            
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error setting system setting {key}: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def is_openai_enabled() -> bool:
        """Check if OpenAI API is enabled"""
        return (SystemService.get_system_setting('openai_api_enabled', True) and 
                not SystemService.get_system_setting('emergency_stop_active', False))
    
    @staticmethod
    def is_emergency_stop_active() -> bool:
        """Check if emergency stop is active"""
        return SystemService.get_system_setting('emergency_stop_active', False)
    
    @staticmethod
    def are_new_accounts_enabled() -> bool:
        """Check if new account creation is enabled"""
        return SystemService.get_system_setting('new_accounts_enabled', True)
    
    @staticmethod
    def get_current_gpt_model() -> str:
        """Get the current GPT model being used"""
        return SystemService.get_system_setting('current_gpt_model', 'gpt-3.5-turbo')
    
    @staticmethod
    def get_max_input_tokens() -> int:
        """Get the maximum input tokens allowed per request"""
        return int(SystemService.get_system_setting('max_input_tokens', 2000))
    
    @staticmethod
    def get_max_output_tokens() -> int:
        """Get the maximum output tokens allowed per request"""
        return int(SystemService.get_system_setting('max_output_tokens', 1500))
    
    @staticmethod
    def get_max_total_tokens() -> int:
        """Get the maximum total tokens allowed per request"""
        return int(SystemService.get_system_setting('max_total_tokens', 3500))
    
    @staticmethod
    def get_flexible_service_tier() -> bool:
        """Get whether flexible service tier is enabled"""
        value = SystemService.get_system_setting('flexible_service_tier', 'true')
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() == 'true'
        else:
            return True
    
    @staticmethod
    def get_presence_penalty() -> float:
        """Get the presence penalty value for OpenAI API"""
        value = SystemService.get_system_setting('presence_penalty', '0.0')
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def get_frequency_penalty() -> float:
        """Get the frequency penalty value for OpenAI API"""
        value = SystemService.get_system_setting('frequency_penalty', '0.0')
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def get_top_p() -> float:
        """Get the top-p sampling value for OpenAI API"""
        value = SystemService.get_system_setting('top_p', '0.9')
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.9


class UserService:
    """Service class for user-related operations"""
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """Get the current user from session"""
        from flask import session
        if 'user_id' in session:
            return User.query.get(session['user_id'])
        return None
    
    @staticmethod
    def get_current_user_profile() -> Optional[UserProfile]:
        """Get the current user's profile"""
        user = UserService.get_current_user()
        if user:
            profile = UserProfile.query.filter_by(user_id=user.id).first()
            if not profile:
                # Create a default profile if it doesn't exist (but preserve admin profiles)
                if user.is_admin:
                    # For admin users, don't create a new profile if one doesn't exist
                    # This allows the admin creation function to handle it
                    return None
                else:
                    # Create a default profile for regular users
                    profile = UserProfile(
                        user_id=user.id,
                        name=user.username,
                        avatar='default-avatar.png',
                        weight_unit='kg'
                    )
                    db.session.add(profile)
                    db.session.commit()
            return profile
        return None
    
    @staticmethod
    def is_user_verified_for_ai(user: User) -> bool:
        """Check if user is verified for AI usage (both email and phone verified)"""
        if not user:
            return False
        return user.email_verified and user.phone_verified
    
    @staticmethod
    def get_user_subscription_info(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's subscription information and session usage"""
        try:
            from .models import UserSubscription, SessionCredits
            
            # Get or create subscription record
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription:
                # Create default subscription for new users
                subscription = UserSubscription(
                    user_id=user_id,
                    subscription_type='subscription',
                    billing_cycle_start=datetime.utcnow()
                )
                db.session.add(subscription)
                db.session.commit()
            
            # Check if billing cycle needs to reset
            now = datetime.utcnow()
            if subscription.billing_cycle_start.month != now.month or subscription.billing_cycle_start.year != now.year:
                subscription.sessions_used_this_month = 0
                subscription.billing_cycle_start = now
                db.session.commit()
            
            # Get session credits
            credits = SessionCredits.query.filter_by(user_id=user_id).first()
            if not credits:
                credits = SessionCredits(user_id=user_id)
                db.session.add(credits)
                db.session.commit()
            
            return {
                'subscription_type': subscription.subscription_type,
                'sessions_per_month': subscription.sessions_per_month,
                'sessions_used_this_month': subscription.sessions_used_this_month,
                'sessions_remaining': subscription.sessions_per_month - subscription.sessions_used_this_month,
                'credits_remaining': credits.credits_remaining,
                'billing_cycle_start': subscription.billing_cycle_start,
                'monthly_fee': subscription.monthly_fee_usd
            }
        except Exception as e:
            print(f"❌ Error getting subscription info: {e}")
            return None
    
    @staticmethod
    def can_user_use_ai(user_id: int) -> bool:
        """Check if user can use AI features (has sessions or credits remaining)"""
        try:
            sub_info = UserService.get_user_subscription_info(user_id)
            if not sub_info:
                return False
            
            # Check if user has subscription sessions or credits remaining
            return (sub_info['sessions_remaining'] > 0 or sub_info['credits_remaining'] > 0)
        except Exception as e:
            print(f"❌ Error checking AI usage permission: {e}")
            return False


class NutritionService:
    """Service class for nutritional data and food-related operations"""
    
    # Barcode database for products not in OpenFoodFacts
    BARCODE_DATABASE = {
        '0828267571602': {
            'food_name': 'Omega 3 Trail Mix',
            'brand': 'Generic',
            'calories': 520,
            'protein': 12,
            'carbs': 45,
            'fat': 32,
            'fiber': 8,
            'sugar': 25,
            'sodium': 120,
            'source': 'barcode_db'
        },
        '1126275101910': {
            'food_name': 'Mixed Nuts and Dried Fruits',
            'brand': 'Generic',
            'calories': 580,
            'protein': 15,
            'carbs': 35,
            'fat': 45,
            'fiber': 10,
            'sugar': 20,
            'sodium': 80,
            'source': 'barcode_db'
        }
    }
    
    # Fallback nutritional database for common foods (per 100g)
    COMMON_FOODS_DATABASE = {
        'apple': {
            'food_name': 'Apple, raw',
            'calories': 52,
            'protein': 0.3,
            'carbs': 14,
            'fat': 0.2,
            'fiber': 2.4,
            'sugar': 10.4,
            'sodium': 1,
            'source': 'common_foods_db'
        },
        'banana': {
            'food_name': 'Banana, raw',
            'calories': 89,
            'protein': 1.1,
            'carbs': 23,
            'fat': 0.3,
            'fiber': 2.6,
            'sugar': 12.2,
            'sodium': 1,
            'source': 'common_foods_db'
        },
        'chicken breast': {
            'food_name': 'Chicken breast, cooked',
            'calories': 165,
            'protein': 31,
            'carbs': 0,
            'fat': 3.6,
            'fiber': 0,
            'sugar': 0,
            'sodium': 74,
            'source': 'common_foods_db'
        },
        'brown rice': {
            'food_name': 'Brown rice, cooked',
            'calories': 111,
            'protein': 2.6,
            'carbs': 23,
            'fat': 0.9,
            'fiber': 1.8,
            'sugar': 0.4,
            'sodium': 5,
            'source': 'common_foods_db'
        },
        'almonds': {
            'food_name': 'Almonds, raw',
            'calories': 579,
            'protein': 21.2,
            'carbs': 21.7,
            'fat': 49.9,
            'fiber': 12.5,
            'sugar': 4.4,
            'sodium': 1,
            'source': 'common_foods_db'
        },
        'yogurt': {
            'food_name': 'Greek yogurt, plain',
            'calories': 59,
            'protein': 10,
            'carbs': 3.6,
            'fat': 0.4,
            'fiber': 0,
            'sugar': 3.2,
            'sodium': 36,
            'source': 'common_foods_db'
        },
        'spinach': {
            'food_name': 'Spinach, raw',
            'calories': 23,
            'protein': 2.9,
            'carbs': 3.6,
            'fat': 0.4,
            'fiber': 2.2,
            'sugar': 0.4,
            'sodium': 79,
            'source': 'common_foods_db'
        },
        'salmon': {
            'food_name': 'Salmon, cooked',
            'calories': 208,
            'protein': 25,
            'carbs': 0,
            'fat': 12,
            'fiber': 0,
            'sugar': 0,
            'sodium': 59,
            'source': 'common_foods_db'
        },
        'quinoa': {
            'food_name': 'Quinoa, cooked',
            'calories': 120,
            'protein': 4.4,
            'carbs': 22,
            'fat': 1.9,
            'fiber': 2.8,
            'sugar': 0.9,
            'sodium': 7,
            'source': 'common_foods_db'
        },
        'cilantro': {
            'food_name': 'Cilantro, raw',
            'calories': 23,
            'protein': 2.1,
            'carbs': 3.7,
            'fat': 0.5,
            'fiber': 2.8,
            'sugar': 0.9,
            'sodium': 46,
            'source': 'common_foods_db'
        },
        'parsley': {
            'food_name': 'Parsley, raw',
            'calories': 36,
            'protein': 3.0,
            'carbs': 6.3,
            'fat': 0.8,
            'fiber': 3.3,
            'sugar': 0.9,
            'sodium': 56,
            'source': 'common_foods_db'
        },
        'basil': {
            'food_name': 'Basil, raw',
            'calories': 22,
            'protein': 3.2,
            'carbs': 2.6,
            'fat': 0.6,
            'fiber': 1.6,
            'sugar': 0.3,
            'sodium': 4,
            'source': 'common_foods_db'
        },
        'mint': {
            'food_name': 'Mint, raw',
            'calories': 44,
            'protein': 3.8,
            'carbs': 8.4,
            'fat': 0.7,
            'fiber': 8.0,
            'sugar': 0.2,
            'sodium': 30,
            'source': 'common_foods_db'
        },
        'omega 3 trail mix': {
            'food_name': 'Omega 3 Trail Mix',
            'calories': 520,
            'protein': 12,
            'carbs': 45,
            'fat': 32,
            'fiber': 8,
            'sugar': 25,
            'sodium': 120,
            'source': 'common_foods_db'
        },
        'trail mix': {
            'food_name': 'Trail Mix',
            'calories': 500,
            'protein': 10,
            'carbs': 50,
            'fat': 30,
            'fiber': 6,
            'sugar': 30,
            'sodium': 100,
            'source': 'common_foods_db'
        },
        'egg': {
            'food_name': 'Egg, whole, raw',
            'calories': 155,
            'protein': 13,
            'carbs': 1.1,
            'fat': 11,
            'fiber': 0,
            'sugar': 1.1,
            'sodium': 124,
            'source': 'common_foods_db'
        },
        'eggs': {
            'food_name': 'Eggs, whole, raw',
            'calories': 155,
            'protein': 13,
            'carbs': 1.1,
            'fat': 11,
            'fiber': 0,
            'sugar': 1.1,
            'sodium': 124,
            'source': 'common_foods_db'
        },
        'avocado': {
            'food_name': 'Avocado, raw',
            'calories': 160,
            'protein': 2,
            'carbs': 9,
            'fat': 15,
            'fiber': 7,
            'sugar': 0.7,
            'sodium': 7,
            'source': 'common_foods_db'
        },
        'bacon': {
            'food_name': 'Bacon, cooked',
            'calories': 541,
            'protein': 37,
            'carbs': 1.4,
            'fat': 42,
            'fiber': 0,
            'sugar': 0,
            'sodium': 1717,
            'source': 'common_foods_db'
        },
        'unsmoked bacon': {
            'food_name': 'Unsmoked back bacon rashers',
            'calories': 290,
            'protein': 25,
            'carbs': 0,
            'fat': 20,
            'fiber': 0,
            'sugar': 0,
            'sodium': 800,
            'source': 'common_foods_db'
        },
        'back bacon': {
            'food_name': 'Back bacon rashers',
            'calories': 290,
            'protein': 25,
            'carbs': 0,
            'fat': 20,
            'fiber': 0,
            'sugar': 0,
            'sodium': 800,
            'source': 'common_foods_db'
        },
            'streaky bacon': {
        'food_name': 'Streaky bacon',
        'calories': 541,
        'protein': 37,
        'carbs': 1.4,
        'fat': 42,
        'fiber': 0,
        'sugar': 0,
        'sodium': 1717,
        'source': 'common_foods_db'
    },
    'bacon': {
        'food_name': 'Bacon',
        'calories': 541,
        'protein': 37,
        'carbs': 1.4,
        'fat': 42,
        'fiber': 0,
        'sugar': 0,
        'sodium': 1717,
        'source': 'common_foods_db'
    },
    'turkey bacon': {
        'food_name': 'Turkey bacon',
        'calories': 382,
        'protein': 28,
        'carbs': 4.3,
        'fat': 28,
        'fiber': 0,
        'sugar': 0,
        'sodium': 1033,
        'source': 'common_foods_db'
    },
    'canadian bacon': {
        'food_name': 'Canadian bacon',
        'calories': 185,
        'protein': 12,
        'carbs': 0.7,
        'fat': 15,
        'fiber': 0,
        'sugar': 0,
        'sodium': 560,
        'source': 'common_foods_db'
    },
    'pancetta': {
        'food_name': 'Pancetta',
        'calories': 357,
        'protein': 14,
        'carbs': 0,
        'fat': 33,
        'fiber': 0,
        'sugar': 0,
        'sodium': 800,
        'source': 'common_foods_db'
    },
    'sauerkraut': {
        'food_name': 'Sauerkraut, canned',
        'calories': 19,
        'protein': 0.9,
        'carbs': 4.3,
        'fat': 0.1,
        'fiber': 2.9,
        'sugar': 1.8,
        'sodium': 661,
        'source': 'common_foods_db'
    },
    'fermented cabbage': {
        'food_name': 'Sauerkraut, fermented cabbage',
        'calories': 19,
        'protein': 0.9,
        'carbs': 4.3,
        'fat': 0.1,
        'fiber': 2.9,
        'sugar': 1.8,
        'sodium': 661,
        'source': 'common_foods_db'
    },
    'sour kraut': {
        'food_name': 'Sauerkraut, sour kraut',
        'calories': 19,
        'protein': 0.9,
        'carbs': 4.3,
        'fat': 0.1,
        'fiber': 2.9,
        'sugar': 1.8,
        'sodium': 661,
        'source': 'common_foods_db'
    },
    'sauer kraut': {
        'food_name': 'Sauerkraut, sauer kraut',
        'calories': 19,
        'protein': 0.9,
        'carbs': 4.3,
        'fat': 0.1,
        'fiber': 2.9,
        'sugar': 1.8,
        'sodium': 661,
        'source': 'common_foods_db'
    }
    }
    
    @staticmethod
    def search_common_foods_database(food_name: str) -> Optional[Dict[str, Any]]:
        """Search the local common foods database"""
        food_lower = food_name.lower().strip()
        
        # Direct match
        if food_lower in NutritionService.COMMON_FOODS_DATABASE:
            data = NutritionService.COMMON_FOODS_DATABASE[food_lower].copy()
            data['serving_size'] = 100
            data['serving_unit'] = 'g'
            return data
        
        # Partial match
        for key, data in NutritionService.COMMON_FOODS_DATABASE.items():
            if key in food_lower or food_lower in key:
                data_copy = data.copy()
                data_copy['serving_size'] = 100
                data_copy['serving_unit'] = 'g'
                return data_copy
        
        # Word-based matching
        food_words = set(food_lower.split())
        best_match = None
        best_score = 0
        
        for key, data in NutritionService.COMMON_FOODS_DATABASE.items():
            key_words = set(key.split())
            common_words = food_words.intersection(key_words)
            score = len(common_words)
            
            if score > best_score:
                best_score = score
                best_match = data
        
        if best_score >= 1:  # At least one word matches
            data_copy = best_match.copy()
            data_copy['serving_size'] = 100
            data_copy['serving_unit'] = 'g'
            return data_copy
        
        return None

    @staticmethod
    def search_common_foods_multiple(food_name: str) -> List[Dict[str, Any]]:
        """Search the local common foods database and return multiple matching results"""
        food_lower = food_name.lower().strip()
        results = []
        
        # Direct match
        if food_lower in NutritionService.COMMON_FOODS_DATABASE:
            data = NutritionService.COMMON_FOODS_DATABASE[food_lower].copy()
            data['serving_size'] = 100
            data['serving_unit'] = 'g'
            results.append(data)
        
        # Partial matches
        for key, data in NutritionService.COMMON_FOODS_DATABASE.items():
            if key in food_lower or food_lower in key:
                data_copy = data.copy()
                data_copy['serving_size'] = 100
                data_copy['serving_unit'] = 'g'
                if data_copy not in results:  # Avoid duplicates
                    results.append(data_copy)
        
        # Word-based matching for additional results
        food_words = set(food_lower.split())
        scored_matches = []
        
        for key, data in NutritionService.COMMON_FOODS_DATABASE.items():
            key_words = set(key.split())
            common_words = food_words.intersection(key_words)
            score = len(common_words)
            
            if score >= 1:  # At least one word matches
                data_copy = data.copy()
                data_copy['serving_size'] = 100
                data_copy['serving_unit'] = 'g'
                scored_matches.append((score, data_copy))
        
        # Sort by score and add top matches (avoiding duplicates)
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        for score, data in scored_matches:
            if data not in results and len(results) < 10:  # Limit to 10 results
                results.append(data)
        
        return results
    
    @staticmethod
    def search_barcode_database(barcode: str) -> Optional[Dict[str, Any]]:
        """Search local barcode database for products not in OpenFoodFacts"""
        try:
            if barcode in NutritionService.BARCODE_DATABASE:
                data = NutritionService.BARCODE_DATABASE[barcode].copy()
                # Add serving size and unit for consistency
                data['serving_size'] = 100
                data['serving_unit'] = 'g'
                return data
            return None
        except Exception as e:
            print(f"Error searching barcode database: {e}")
            return None

    @staticmethod
    def search_openfoodfacts_by_barcode(barcode: str) -> Optional[Dict[str, Any]]:
        """Search Open Food Facts API v2 by barcode for specific product"""
        try:
            # Use the official API v2 product endpoint
            url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}"
            
            # Set up headers with proper User-Agent as required by the API
            headers = {
                'User-Agent': 'KiWellness/1.0 (nutrition@kiwellness.org)',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Handle rate limiting (429 status)
            if response.status_code == 429:
                print("Open Food Facts API: Rate limit reached (100 req/min for product queries)")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 1 and data.get('product'):
                product = data['product']
                return NutritionService.extract_nutritional_data(product, product.get('product_name', ''))
            
            return None
        except requests.exceptions.Timeout:
            print("Open Food Facts API v2 barcode search: Request timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Open Food Facts API v2 barcode search request error: {e}")
            return None
        except Exception as e:
            print(f"Open Food Facts API v2 barcode search error: {e}")
            return None
    
    @staticmethod
    def search_openfoodfacts_api(food_name: str) -> Optional[Dict[str, Any]]:
        """Search Open Food Facts API v2 for nutritional information with improved accuracy"""
        try:
            # Clean and improve search terms
            search_terms = NutritionService.clean_search_terms(food_name)
            
            # Use the official API v2 search endpoint
            url = f"https://world.openfoodfacts.org/cgi/search.pl"
            
            # Set up headers with proper User-Agent as required by the API
            headers = {
                'User-Agent': 'KiWellness/1.0 (nutrition@kiwellness.org)',
                'Content-Type': 'application/json'
            }
            
            # Search parameters for the legacy endpoint
            params = {
                'search_terms': search_terms,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 20  # Get more results for user selection
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Handle rate limiting (429 status)
            if response.status_code == 429:
                print("Open Food Facts API: Rate limit reached (10 req/min for search)")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('products') and len(data['products']) > 0:
                # Find the best match
                best_product = NutritionService.find_best_match(data['products'], food_name)
                if best_product:
                    return NutritionService.extract_nutritional_data(best_product, food_name)
            
            return None
        except requests.exceptions.Timeout:
            print("Open Food Facts API v2: Request timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Open Food Facts API v2 request error: {e}")
            return None
        except Exception as e:
            print(f"Open Food Facts API v2 error: {e}")
            return None

    @staticmethod
    def search_openfoodfacts_multiple(food_name: str) -> List[Dict[str, Any]]:
        """Search Open Food Facts API v2 and return multiple results for user selection"""
        try:
            # Clean and improve search terms
            search_terms = NutritionService.clean_search_terms(food_name)
            
            # Use the official API v2 search endpoint
            url = f"https://world.openfoodfacts.org/cgi/search.pl"
            
            # Set up headers with proper User-Agent as required by the API
            headers = {
                'User-Agent': 'KiWellness/1.0 (nutrition@kiwellness.org)',
                'Content-Type': 'application/json'
            }
            
            # Search parameters for the legacy endpoint
            params = {
                'search_terms': search_terms,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 20  # Get up to 20 results for user selection
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Handle rate limiting (429 status)
            if response.status_code == 429:
                print("Open Food Facts API: Rate limit reached (10 req/min for search)")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            results = []
            if data.get('products') and len(data['products']) > 0:
                # Process up to 20 products and return them as options
                for product in data['products'][:20]:
                    nutritional_data = NutritionService.extract_nutritional_data(product, food_name)
                    if nutritional_data:
                        results.append(nutritional_data)
            
            return results
        except requests.exceptions.Timeout:
            print("Open Food Facts API v2: Request timeout")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Open Food Facts API v2 request error: {e}")
            return []
        except Exception as e:
            print(f"Open Food Facts API v2 error: {e}")
            return []
    
    @staticmethod
    def clean_search_terms(food_name: str) -> str:
        """Clean and improve search terms for better API results"""
        # Remove common words that might interfere with search
        remove_words = ['fresh', 'organic', 'raw', 'whole', 'natural']
        cleaned = food_name.lower()
        
        for word in remove_words:
            cleaned = cleaned.replace(word, '').strip()
        
        # Add common variations
        variations = {
            'apple': 'apple fruit',
            'banana': 'banana fruit', 
            'chicken': 'chicken meat',
            'rice': 'rice grain',
            'almond': 'almond nut',
            'yogurt': 'yogurt dairy',
            'spinach': 'spinach vegetable',
            'salmon': 'salmon fish',
            'quinoa': 'quinoa grain',
            'avocado': 'avocado fruit'
        }
        
        for key, value in variations.items():
            if key in cleaned:
                cleaned = value
                break
        
        return cleaned

    @staticmethod
    def get_fuzzy_search_suggestions(query: str, food_list: List[str], limit: int = 5) -> List[tuple]:
        """Get fuzzy search suggestions for misspelled food names"""
        if not FUZZY_AVAILABLE:
            return []
        
        try:
            # Use fuzzywuzzy to find similar food names
            suggestions = process.extract(query.lower(), food_list, limit=limit, scorer=fuzz.token_sort_ratio)
            # Filter out very low similarity matches (below 60%)
            filtered_suggestions = [(name, score) for name, score in suggestions if score >= 60]
            return filtered_suggestions
        except Exception as e:
            print(f"Error in fuzzy search: {e}")
            return []

    @staticmethod
    def get_common_misspellings() -> Dict[str, str]:
        """Get common misspellings and their correct forms"""
        return {
            # Sauerkraut variations
            'sourkraut': 'sauerkraut',
            'sour kraut': 'sauerkraut',
            'sauer kraut': 'sauerkraut',
            'sourcrout': 'sauerkraut',
            'sauerkrout': 'sauerkraut',
            'saurkraut': 'sauerkraut',  # Missing 'e'
            'saur kraut': 'sauerkraut',  # Missing 'e'
            'saurkraut': 'sauerkraut',  # Missing 'e'
            
            # Common food misspellings
            'brocolli': 'broccoli',
            'brocolli': 'broccoli',
            'cauliflour': 'cauliflower',
            'cauliflour': 'cauliflower',
            'zuchini': 'zucchini',
            'zuchini': 'zucchini',
            'eggplant': 'aubergine',
            'aubergine': 'eggplant',
            'courgette': 'zucchini',
            'zucchini': 'courgette',
            
            # Protein variations
            'chicken breast': 'chicken',
            'chicken thigh': 'chicken',
            'ground beef': 'beef',
            'lean beef': 'beef',
            'salmon fillet': 'salmon',
            'tuna fish': 'tuna',
            
            # Grain variations
            'brown rice': 'rice',
            'white rice': 'rice',
            'wild rice': 'rice',
            'quinoa grain': 'quinoa',
            'oatmeal': 'oats',
            'rolled oats': 'oats',
            
            # Dairy variations
            'greek yogurt': 'yogurt',
            'plain yogurt': 'yogurt',
            'vanilla yogurt': 'yogurt',
            'cheddar cheese': 'cheese',
            'mozzarella cheese': 'cheese',
            
            # Fruit variations
            'red apple': 'apple',
            'green apple': 'apple',
            'banana fruit': 'banana',
            'orange fruit': 'orange',
            'strawberry': 'strawberries',
            'strawberries': 'strawberry',
            
            # Vegetable variations
            'carrot vegetable': 'carrot',
            'tomato vegetable': 'tomato',
            'cucumber vegetable': 'cucumber',
            'lettuce vegetable': 'lettuce',
            'spinach vegetable': 'spinach',
            'kale vegetable': 'kale',
            
            # Additional common misspellings
            'asparagus': 'asparagus',
            'asparagus': 'asparagus',
            'brussel sprouts': 'brussels sprouts',
            'brussels sprout': 'brussels sprouts',
            'brussel sprout': 'brussels sprouts',
            'bell pepper': 'pepper',
            'red pepper': 'pepper',
            'green pepper': 'pepper',
            'yellow pepper': 'pepper',
            'onion': 'onion',
            'garlic': 'garlic',
            'ginger': 'ginger',
            'mushroom': 'mushrooms',
            'mushrooms': 'mushroom',
            'potato': 'potatoes',
            'potatoes': 'potato',
            'sweet potato': 'sweet potatoes',
            'sweet potatoes': 'sweet potato',
            'yam': 'yams',
            'yams': 'yam',
            'corn': 'corn',
            'peas': 'peas',
            'green beans': 'green beans',
            'string beans': 'green beans',
            'snap beans': 'green beans',
            'celery': 'celery',
            'radish': 'radishes',
            'radishes': 'radish',
            'beet': 'beets',
            'beets': 'beet',
            'turnip': 'turnips',
            'turnips': 'turnip',
            'parsnip': 'parsnips',
            'parsnips': 'parsnip',
            
            # Herb variations
            'cilantro herb': 'cilantro',
            'fresh cilantro': 'cilantro',
            'coriander': 'cilantro',
            'coriander leaves': 'cilantro',
            'parsley herb': 'parsley',
            'fresh parsley': 'parsley',
            'basil herb': 'basil',
            'fresh basil': 'basil',
            'mint herb': 'mint',
            'fresh mint': 'mint',
            'rutabaga': 'rutabagas',
            'rutabagas': 'rutabaga',
            'swiss chard': 'chard',
            'chard': 'swiss chard',
            'collard greens': 'collards',
            'collards': 'collard greens',
            'mustard greens': 'mustard',
            'mustard': 'mustard greens',
            'bok choy': 'pak choi',
            'pak choi': 'bok choy',
            'napa cabbage': 'chinese cabbage',
            'chinese cabbage': 'napa cabbage',
            'daikon': 'daikon radish',
            'daikon radish': 'daikon',
            'jicama': 'jicama',
            'water chestnut': 'water chestnuts',
            'water chestnuts': 'water chestnut',
            'bamboo shoot': 'bamboo shoots',
            'bamboo shoots': 'bamboo shoot',
            'snow pea': 'snow peas',
            'snow peas': 'snow pea',
            'sugar snap pea': 'sugar snap peas',
            'sugar snap peas': 'sugar snap pea',
            'edamame': 'edamame',
            'soybean': 'soybeans',
            'soybeans': 'soybean',
            'tofu': 'tofu',
            'tempeh': 'tempeh',
            'seitan': 'seitan',
            'quorn': 'quorn',
            'textured vegetable protein': 'tvp',
            'tvp': 'textured vegetable protein'
        }

    @staticmethod
    def correct_spelling(query: str) -> str:
        """Correct common misspellings in food search queries"""
        query_lower = query.lower().strip()
        
        # Check for exact matches in misspellings dictionary
        misspellings = NutritionService.get_common_misspellings()
        if query_lower in misspellings:
            return misspellings[query_lower]
        
        # Check for partial matches (e.g., "sour" should match "sourkraut")
        for misspelled, correct in misspellings.items():
            if query_lower in misspelled or misspelled in query_lower:
                return correct
        
        return query

    @staticmethod
    def enhance_search_query(query: str) -> List[str]:
        """Enhance search query with spelling corrections and variations"""
        enhanced_queries = [query]
        
        # Add spelling correction
        corrected = NutritionService.correct_spelling(query)
        if corrected != query:
            enhanced_queries.append(corrected)
        
        # Add common variations
        variations = {
            'sauerkraut': ['sourkraut', 'sour kraut', 'saurkraut', 'saur kraut', 'fermented cabbage'],
            'broccoli': ['brocolli', 'brocolli'],
            'cauliflower': ['cauliflour', 'cauliflour'],
            'zucchini': ['zuchini', 'courgette'],
            'quinoa': ['quinoa grain', 'keenwa'],
            'yogurt': ['yoghurt', 'yoghurt'],
            'tomato': ['tomatoes', 'tomato vegetable'],
            'apple': ['apples', 'apple fruit'],
            'banana': ['bananas', 'banana fruit'],
            'chicken': ['chicken meat', 'chicken breast', 'chicken thigh'],
            'salmon': ['salmon fish', 'salmon fillet'],
            'rice': ['rice grain', 'brown rice', 'white rice'],
            'spinach': ['spinach vegetable', 'spinach leaves'],
            'carrot': ['carrots', 'carrot vegetable'],
            'cucumber': ['cucumbers', 'cucumber vegetable'],
            'lettuce': ['lettuce vegetable', 'lettuce leaves'],
            'kale': ['kale vegetable', 'kale leaves'],
            'cilantro': ['coriander', 'coriander leaves', 'fresh cilantro', 'cilantro herb'],
            'parsley': ['fresh parsley', 'parsley herb'],
            'basil': ['fresh basil', 'basil herb'],
            'mint': ['fresh mint', 'mint herb']
        }
        
        # Add variations for the query
        query_lower = query.lower()
        for food, food_variations in variations.items():
            if query_lower in food_variations or query_lower == food:
                enhanced_queries.extend(food_variations)
                enhanced_queries.append(food)  # Add the base form
                break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in enhanced_queries:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)
        
        return unique_queries[:5]  # Limit to 5 variations
    
    @staticmethod
    def find_best_match(products: List[Dict[str, Any]], original_food_name: str) -> Optional[Dict[str, Any]]:
        """Find the best matching product from search results"""
        original_lower = original_food_name.lower()
        
        # Score each product based on relevance
        scored_products = []
        
        for product in products:
            score = 0
            product_name = product.get('product_name', '').lower()
            brands = product.get('brands', '').lower()
            categories = product.get('categories_tags', [])
            
            # Exact name match gets highest score
            if original_lower in product_name:
                score += 100
            
            # Partial name match
            if any(word in product_name for word in original_lower.split()):
                score += 50
            
            # Prefer raw/unprocessed foods
            if any(tag in categories for tag in ['en:raw-foods', 'en:unprocessed-foods']):
                score += 30
            
            # Penalize heavily processed foods
            if any(tag in categories for tag in ['en:processed-foods', 'en:snacks', 'en:candies']):
                score -= 50
            
            # Penalize if it's clearly a different food
            if 'bar' in product_name or 'candy' in product_name or 'snack' in product_name:
                if not any(word in original_lower for word in ['bar', 'candy', 'snack']):
                    score -= 100
            
            scored_products.append((score, product))
        
        # Sort by score and return the best match
        scored_products.sort(key=lambda x: x[0], reverse=True)
        
        # Only return if the best match has a reasonable score
        if scored_products and scored_products[0][0] > 0:
            return scored_products[0][1]
        
        return None
    
    @staticmethod
    def extract_nutritional_data(product: Dict[str, Any], original_food_name: str) -> Optional[Dict[str, Any]]:
        """Extract and validate nutritional data from product with comprehensive fields"""
        nutriments = product.get('nutriments', {})
        
        # Core nutritional values (displayed to user)
        calories = nutriments.get('energy-kcal_100g') or nutriments.get('energy_100g')
        protein = nutriments.get('proteins_100g')
        carbs = nutriments.get('carbohydrates_100g')
        fat = nutriments.get('fat_100g')
        fiber = nutriments.get('fiber_100g')
        sugar = nutriments.get('sugars_100g')
        # OpenFoodFacts provides salt in grams, convert to sodium in mg
        salt_g = nutriments.get('salt_100g')
        try:
            if salt_g is not None:
                # Ensure salt_g is a number
                if isinstance(salt_g, str):
                    salt_g = float(salt_g)
                elif not isinstance(salt_g, (int, float)):
                    salt_g = None
                
                if salt_g is not None and not float('nan') == salt_g:
                    sodium = salt_g * 400  # 1g salt ≈ 400mg sodium
                else:
                    sodium = None
            else:
                sodium = None
        except (ValueError, TypeError):
            sodium = None
        

        
        # Extended nutritional values (stored but not displayed)
        saturated_fat = nutriments.get('saturated-fat_100g')
        trans_fat = nutriments.get('trans-fat_100g')
        cholesterol = nutriments.get('cholesterol_100g')
        potassium = nutriments.get('potassium_100g')
        calcium = nutriments.get('calcium_100g')
        iron = nutriments.get('iron_100g')
        vitamin_a = nutriments.get('vitamin-a_100g')
        vitamin_c = nutriments.get('vitamin-c_100g')
        vitamin_d = nutriments.get('vitamin-d_100g')
        vitamin_e = nutriments.get('vitamin-e_100g')
        vitamin_k = nutriments.get('vitamin-k_100g')
        vitamin_b6 = nutriments.get('vitamin-b6_100g')
        vitamin_b12 = nutriments.get('vitamin-b12_100g')
        magnesium = nutriments.get('magnesium_100g')
        zinc = nutriments.get('zinc_100g')
        phosphorus = nutriments.get('phosphorus_100g')
        manganese = nutriments.get('manganese_100g')
        selenium = nutriments.get('selenium_100g')
        copper = nutriments.get('copper_100g')
        thiamin = nutriments.get('thiamin_100g')
        riboflavin = nutriments.get('riboflavin_100g')
        niacin = nutriments.get('niacin_100g')
        folate = nutriments.get('folate_100g')
        pantothenic_acid = nutriments.get('pantothenic-acid_100g')
        biotin = nutriments.get('biotin_100g')
        choline = nutriments.get('choline_100g')
        betaine = nutriments.get('betaine_100g')
        taurine = nutriments.get('taurine_100g')
        caffeine = nutriments.get('caffeine_100g')
        alcohol = nutriments.get('alcohol_100g')
        water_content = nutriments.get('water_100g')
        ash = nutriments.get('ash_100g')
        
        # Validate data quality - be more lenient
        if calories is None:
            calories = 0  # Set to 0 if not available
        
        # Convert calories to float for comparison
        try:
            if isinstance(calories, str):
                calories = float(calories)
            elif not isinstance(calories, (int, float)):
                calories = 0
        except (ValueError, TypeError):
            calories = 0
        
        # Check for reasonable ranges
        if calories > 900:  # Most foods don't exceed 900 cal/100g
            calories = 0  # Reset to 0 if unreasonable
        
        return {
            'food_name': product.get('product_name', original_food_name),
            'brand': product.get('brands', ''),
            'serving_size': 100,
            'serving_unit': 'g',
            
            # Core nutritional values (displayed to user)
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fat': fat,
            'fiber': fiber,
            'sugar': sugar,
            'sodium': sodium,
            
            # Extended nutritional values (stored but not displayed)
            'saturated_fat': saturated_fat,
            'trans_fat': trans_fat,
            'cholesterol': cholesterol,
            'potassium': potassium,
            'calcium': calcium,
            'iron': iron,
            'vitamin_a': vitamin_a,
            'vitamin_c': vitamin_c,
            'vitamin_d': vitamin_d,
            'vitamin_e': vitamin_e,
            'vitamin_k': vitamin_k,
            'vitamin_b6': vitamin_b6,
            'vitamin_b12': vitamin_b12,
            'magnesium': magnesium,
            'zinc': zinc,
            'phosphorus': phosphorus,
            'manganese': manganese,
            'selenium': selenium,
            'copper': copper,
            'thiamin': thiamin,
            'riboflavin': riboflavin,
            'niacin': niacin,
            'folate': folate,
            'pantothenic_acid': pantothenic_acid,
            'biotin': biotin,
            'choline': choline,
            'betaine': betaine,
            'taurine': taurine,
            'caffeine': caffeine,
            'alcohol': alcohol,
            'water_content': water_content,
            'ash': ash,
            
            'source': 'openfoodfacts'
        }
    
    @staticmethod
    def search_usda_api(food_name: str) -> Optional[Dict[str, Any]]:
        """Search USDA API for nutritional information"""
        try:
            # Using USDA FoodData Central API
            url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={os.environ.get('USDA_API_KEY')}&query={food_name}&pageSize=1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('foods') and len(data['foods']) > 0:
                food = data['foods'][0]
                nutrients = {item['nutrientName']: item['value'] for item in food.get('foodNutrients', [])}
                
                return {
                    'food_name': food.get('description', food_name),
                    'brand': food.get('brandOwner', ''),
                    'serving_size': 100,  # Default to 100g
                    'serving_unit': 'g',
                    'calories': nutrients.get('Energy'),
                    'protein': nutrients.get('Protein'),
                    'carbs': nutrients.get('Carbohydrate, by difference'),
                    'fat': nutrients.get('Total lipid (fat)'),
                    'fiber': nutrients.get('Fiber, total dietary'),
                    'sugar': nutrients.get('Sugars, total including NLEA'),
                    'sodium': nutrients.get('Sodium, Na'),
                    'source': 'usda'
                }
        except Exception as e:
            print(f"USDA API error: {e}")
            return None
    
    @staticmethod
    def convert_nutritional_data(nutrition_data: Dict[str, Any], user_serving_size: float, user_serving_unit: str) -> Optional[Dict[str, Any]]:
        """Convert nutritional data based on user's serving size and unit"""
        if not nutrition_data:
            return None
        
        # Convert to grams for calculation
        base_serving_size = nutrition_data['serving_size']
        base_serving_unit = nutrition_data['serving_unit']
        
        # Convert user serving to grams
        user_serving_in_grams = ConversionUtils.convert_to_grams(user_serving_size, user_serving_unit)
        base_serving_in_grams = ConversionUtils.convert_to_grams(base_serving_size, base_serving_unit)
        
        if base_serving_in_grams == 0:
            return None
        
        # Calculate conversion factor
        conversion_factor = user_serving_in_grams / base_serving_in_grams
        
        # Convert all nutritional values
        converted_data = nutrition_data.copy()
        converted_data['serving_size'] = user_serving_size
        converted_data['serving_unit'] = user_serving_unit
        
        # Core nutritional fields (displayed to user)
        core_nutritional_fields = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
        
        # Extended nutritional fields (stored but not displayed)
        extended_nutritional_fields = [
            'saturated_fat', 'trans_fat', 'cholesterol', 'potassium', 'calcium', 'iron',
            'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 'vitamin_b6', 'vitamin_b12',
            'magnesium', 'zinc', 'phosphorus', 'manganese', 'selenium', 'copper', 'thiamin',
            'riboflavin', 'niacin', 'folate', 'pantothenic_acid', 'biotin', 'choline', 'betaine',
            'taurine', 'caffeine', 'alcohol', 'water_content', 'ash'
        ]
        
        # Convert all nutritional fields
        all_nutritional_fields = core_nutritional_fields + extended_nutritional_fields
        for field in all_nutritional_fields:
            if converted_data.get(field) is not None:
                try:
                    # Convert to float if it's a string, then multiply
                    value = converted_data[field]
                    if isinstance(value, str):
                        value = float(value)
                    elif not isinstance(value, (int, float)):
                        continue  # Skip non-numeric values
                    
                    converted_data[field] = round(value * conversion_factor, 2)
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Warning: Could not convert {field} value '{converted_data[field]}' to number: {e}")
                    continue  # Skip this field if conversion fails
        
        return converted_data


class AIService:
    """Service class for AI-related operations and OpenAI integration"""
    
    @staticmethod
    def analyze_patterns_with_openai(entries_data: List[Dict[str, Any]], time_period: str, user_profile: Optional[UserProfile] = None) -> Dict[str, Any]:
        """Analyze food journal patterns using OpenAI API with user profile context"""
        try:
            # Check emergency stop first
            if SystemService.is_emergency_stop_active():
                print("🚨 EMERGENCY STOP ACTIVE: OpenAI API calls are disabled")
                return {
                    'analysis': "⚠️ AI analysis is temporarily unavailable due to emergency stop. Please try again later or contact support.",
                    'suggestions': "System is in maintenance mode. Please check back later.",
                    'error': 'emergency_stop_active'
                }
            
            # Check if OpenAI is enabled
            if not SystemService.is_openai_enabled():
                print("🚫 OpenAI API is disabled")
                return {
                    'analysis': "⚠️ AI analysis is currently disabled. Please try again later or contact support.",
                    'suggestions': "System is in maintenance mode. Please check back later.",
                    'error': 'openai_disabled'
                }
            
            # Check if user is verified for AI usage
            current_user = UserService.get_current_user()
            if current_user and not UserService.is_user_verified_for_ai(current_user):
                print("🔒 User not verified for AI usage")
                return {
                    'analysis': "⚠️ Account Verification Required: Please verify your email and phone number before using AI features.",
                    'suggestions': "Check your email and phone for verification codes, or contact support for assistance.",
                    'error': 'verification_required'
                }
            
            # Check if user has AI usage permissions
            if current_user and not UserService.can_user_use_ai(current_user.id):
                print("🔒 User has no AI usage sessions or credits remaining")
                return {
                    'analysis': "⚠️ AI Usage Limit Reached: You've used all your monthly sessions and have no credits remaining.",
                    'suggestions': "Upgrade to monthly subscription or purchase session credits to continue using AI features.",
                    'error': 'usage_limit_reached'
                }
            
            # Initialize OpenAI client
            if not OPENAI_AVAILABLE:
                return {
                    'analysis': "⚠️ AI service is not available. Please try again later.",
                    'suggestions': "System is in maintenance mode. Please check back later.",
                    'error': 'openai_not_available'
                }
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Prepare the data for analysis (simplified for brevity)
            analysis_data = {
                'total_entries': len(entries_data),
                'foods': [],
                'moods': [],
                'water_intake': [],
                'nutritional_totals': {
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'fiber': 0,
                    'sugar': 0,
                    'sodium': 0
                }
            }
            
            # Process entries data (simplified)
            for entry in entries_data:
                if entry.get('food_name'):
                    analysis_data['foods'].append({
                        'name': entry['food_name'],
                        'calories': entry.get('calories', 0),
                        'protein': entry.get('protein', 0),
                        'carbs': entry.get('carbs', 0),
                        'fat': entry.get('fat', 0)
                    })
                
                if entry.get('mood'):
                    analysis_data['moods'].append(entry['mood'])
                
                # Sum nutritional data
                for nutrient in ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']:
                    if entry.get(nutrient) is not None:
                        analysis_data['nutritional_totals'][nutrient] += entry[nutrient]
            
            # Create prompt for OpenAI
            user_name = user_profile.name if user_profile and user_profile.name else "there"
            
            prompt = f"""
            You are {user_name}'s personal wellness coach. Analyze their nutritional journal data from the past {time_period} days.
            
            DATA SUMMARY:
            - Total entries: {analysis_data['total_entries']}
            - Foods consumed: {len(analysis_data['foods'])} different items
            - Mood entries: {len(analysis_data['moods'])} entries
            
            NUTRITIONAL TOTALS:
            - Total calories: {analysis_data['nutritional_totals']['calories']:.1f}
            - Total protein: {analysis_data['nutritional_totals']['protein']:.1f}g
            - Total carbs: {analysis_data['nutritional_totals']['carbs']:.1f}g
            - Total fat: {analysis_data['nutritional_totals']['fat']:.1f}g
            - Total fiber: {analysis_data['nutritional_totals']['fiber']:.1f}g
            - Total sugar: {analysis_data['nutritional_totals']['sugar']:.1f}g
            - Total sodium: {analysis_data['nutritional_totals']['sodium']:.1f}mg
            
            Provide personalized insights and actionable suggestions based on this data.
            """
            
            # Get current model and settings
            current_model = SystemService.get_current_gpt_model()
            max_output_tokens = SystemService.get_max_output_tokens()
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": f"You are {user_name}'s personal wellness coach. Provide encouraging, actionable advice."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_output_tokens,
                temperature=0.7,
                presence_penalty=SystemService.get_presence_penalty(),
                frequency_penalty=SystemService.get_frequency_penalty(),
                top_p=SystemService.get_top_p()
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Track token usage
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate cost
            api_costs = APICosts.query.filter_by(model_name=current_model, is_active=True).first()
            cost_usd = 0.0
            if api_costs:
                input_cost = (input_tokens / 1000000) * api_costs.input_cost_per_1m
                output_cost = (output_tokens / 1000000) * api_costs.output_cost_per_1m
                cost_usd = input_cost + output_cost
            
            # Record usage session
            if current_user:
                from .models import AIUsageSession
                usage_session = AIUsageSession(
                    user_id=current_user.id,
                    session_type='patterns_analysis',
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    cost_usd=cost_usd,
                    model_used=current_model,
                    subscription_used=True
                )
                db.session.add(usage_session)
                db.session.commit()
            
            return {
                'success': True,
                'analysis': ai_response,
                'suggestions': "Based on your data, consider these wellness tips...",
                'created_at': datetime.utcnow().isoformat(),
                'summary': {
                    'total_entries': analysis_data['total_entries'],
                    'total_calories': analysis_data['nutritional_totals']['calories'],
                    'total_protein': analysis_data['nutritional_totals']['protein'],
                    'total_carbs': analysis_data['nutritional_totals']['carbs'],
                    'total_fat': analysis_data['nutritional_totals']['fat']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error analyzing patterns: {str(e)}"
            }
