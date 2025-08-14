"""
Ki Wellness - Utilities Module
==============================

This module contains utility functions and helper classes used throughout
the Ki Wellness application to reduce code duplication and improve maintainability.

Author: Ki Wellness Team
Version: 2.0
"""

import os
import re
import secrets
import random
from datetime import datetime, timedelta, time
from typing import Optional, Dict, Any, List
from flask import request, current_app
import pytz


class ValidationUtils:
    """Utility class for input validation and sanitization"""
    
    @staticmethod
    def is_kiwellness_username(username: str) -> bool:
        """
        Check if username contains 'kiwellness' in any form including special characters, numbers, and variations
        Returns True if the username contains 'kiwellness' in any form, False otherwise
        """
        # Convert to lowercase for case-insensitive comparison
        username_lower = username.lower()
        
        # Remove ALL special characters, spaces, and numbers for comparison
        # This catches variations like: k!wellness, k1wellness, k@wellness, etc.
        cleaned_username = re.sub(r'[^a-zA-Z]', '', username_lower)
        
        # Check if 'kiwellness' is contained in the cleaned username
        if 'kiwellness' in cleaned_username:
            return True
        
        # Check for common variations with special characters and numbers
        variations = [
            'kiwellness', 'ki_wellness', 'ki-wellness', 'ki wellness',
            'kiwellness123', 'ki_wellness_123', 'ki-wellness-123', 'ki wellness 123',
            'kiwellness2024', 'ki_wellness_2024', 'ki-wellness-2024', 'ki wellness 2024',
            'kiwellness2023', 'ki_wellness_2023', 'ki-wellness-2023', 'ki wellness 2023',
            'kiwellness2025', 'ki_wellness_2025', 'ki-wellness-2025', 'ki wellness 2025',
            # Special character variations
            'k!wellness', 'k1wellness', 'k@wellness', 'k#wellness', 'k$wellness',
            'k%wellness', 'k^wellness', 'k&wellness', 'k*wellness', 'k(wellness',
            'k)wellness', 'k-wellness', 'k+wellness', 'k=wellness', 'k[wellness',
            'k]wellness', 'k{wellness', 'k}wellness', 'k|wellness', 'k\\wellness',
            'k:wellness', 'k;wellness', 'k"wellness', 'k\'wellness', 'k<wellness',
            'k>wellness', 'k,wellness', 'k.wellness', 'k?wellness', 'k/wellness'
        ]
        
        for variation in variations:
            if variation in username_lower:
                return True
        
        # Check for patterns with special characters and numbers
        patterns = [
            r'ki\s*wellness',           # ki wellness, ki  wellness
            r'ki_wellness',             # ki_wellness
            r'ki-wellness',             # ki-wellness
            r'kiwellness',              # kiwellness
            r'k[!@#$%^&*()_+\-=\[\]{}|\\:;"\'<>,.?/0-9]*wellness',  # k followed by any special chars/numbers + wellness
            r'ki[!@#$%^&*()_+\-=\[\]{}|\\:;"\'<>,.?/0-9]*wellness', # ki followed by any special chars/numbers + wellness
            r'k[!@#$%^&*()_+\-=\[\]{}|\\:;"\'<>,.?/0-9]*i[!@#$%^&*()_+\-=\[\]{}|\\:;"\'<>,.?/0-9]*wellness'  # k + special chars + i + special chars + wellness
        ]
        
        for pattern in patterns:
            if re.search(pattern, username_lower):
                return True
        
        # Additional check: look for 'ki' followed by any characters, then 'wellness'
        # This catches cases like: k1wellness, k!wellness, k@wellness, etc.
        ki_pattern = re.search(r'k[^a-zA-Z]*i[^a-zA-Z]*wellness', username_lower)
        if ki_pattern:
            return True
        
        return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(email_pattern.match(email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        phone_clean = re.sub(r'[^\d+]', '', phone)
        return len(phone_clean) >= 10
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength and return detailed feedback"""
        errors = []
        warnings = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Additional strength checks
        if len(password) < 12:
            warnings.append("Consider using a longer password for better security")
        
        if re.search(r'(.)\1{2,}', password):
            warnings.append("Avoid repeating characters")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'strength_score': max(0, 10 - len(errors) * 2)
        }


class SecurityUtils:
    """Utility class for security-related functions"""
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_phone_verification_code() -> str:
        """Generate a 6-digit verification code"""
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def check_honeypot(data: Dict[str, Any]) -> bool:
        """Check if honeypot field was filled (indicates bot)"""
        honeypot_fields = ['website', 'phone_number', 'company', 'subject']
        
        for field in honeypot_fields:
            if data.get(field) and data.get(field).strip():
                print(f"🚫 Bot detected: Honeypot field '{field}' was filled")
                return False
        
        return True
    
    @staticmethod
    def is_localhost_environment() -> bool:
        """Check if running on localhost"""
        try:
            if request:
                host = request.host
                is_local = host in ['127.0.0.1:5001', 'localhost:5001', '0.0.0.0:5001']
                print(f"🔧 Host check: {host} -> localhost: {is_local}")
                return is_local
        except RuntimeError as e:
            print(f"🔧 RuntimeError in host check: {e}")
            pass
        print("🔧 No request context, assuming not localhost")
        return False


class TimeUtils:
    """Utility class for time and date operations"""
    
    @staticmethod
    def get_browser_timezone_datetime(browser_timezone: Optional[str] = None) -> datetime:
        """Get current datetime in browser timezone"""
        try:
            if browser_timezone:
                # Get current time in the browser's timezone
                now = datetime.utcnow()
                # Convert to the browser's timezone
                browser_tz = pytz.timezone(browser_timezone)
                utc_tz = pytz.UTC
                utc_now = utc_tz.localize(now)
                browser_now = utc_now.astimezone(browser_tz)
                # Return as naive datetime in browser timezone
                return browser_now.replace(tzinfo=None)
            else:
                # Fallback to UTC if no timezone provided
                return datetime.utcnow()
        except Exception as e:
            print(f"Error parsing browser timezone: {e}")
            return datetime.utcnow()
    
    @staticmethod
    def calculate_next_trigger(time_of_day: time, frequency: str, days_of_week: Optional[List[int]] = None) -> datetime:
        """Calculate next trigger time for reminders"""
        now = datetime.utcnow()
        today = now.date()
        
        if frequency == 'daily':
            # Set to today at the specified time
            next_trigger = datetime.combine(today, time_of_day)
            # If time has passed today, set to tomorrow
            if next_trigger <= now:
                next_trigger += timedelta(days=1)
            return next_trigger
        
        elif frequency == 'hourly':
            # Set to next hour at the specified minute
            next_trigger = now.replace(minute=time_of_day.minute, second=0, microsecond=0)
            if next_trigger <= now:
                next_trigger += timedelta(hours=1)
            return next_trigger
        
        elif frequency == 'custom' and days_of_week:
            # Find next occurrence on specified days
            current_weekday = now.weekday()
            days_ahead = 0
            
            for i in range(7):
                check_day = (current_weekday + i) % 7
                if check_day in days_of_week:
                    days_ahead = i
                    break
            
            next_trigger = datetime.combine(today + timedelta(days=days_ahead), time_of_day)
            if next_trigger <= now:
                # Move to next week
                next_trigger += timedelta(days=7)
            return next_trigger
        
        # Default to daily
        next_trigger = datetime.combine(today, time_of_day)
        if next_trigger <= now:
            next_trigger += timedelta(days=1)
        return next_trigger


class ConversionUtils:
    """Utility class for unit conversions"""
    
    @staticmethod
    def convert_to_grams(amount: float, unit: str) -> float:
        """Convert various units to grams"""
        unit = unit.lower()
        if unit in ['g', 'gram', 'grams']:
            return amount
        elif unit in ['kg', 'kilogram', 'kilograms']:
            return amount * 1000
        elif unit in ['oz', 'ounce', 'ounces']:
            return amount * 28.35
        elif unit in ['lb', 'pound', 'pounds']:
            return amount * 453.59
        elif unit in ['ml', 'milliliter', 'milliliters']:
            return amount  # Approximate for water-based foods
        elif unit in ['l', 'liter', 'liters']:
            return amount * 1000
        elif unit in ['cup', 'cups']:
            return amount * 236.59
        elif unit in ['tbsp', 'tablespoon', 'tablespoons']:
            return amount * 14.79
        elif unit in ['tsp', 'teaspoon', 'teaspoons']:
            return amount * 4.93
        elif unit in ['item', 'items']:
            # For bacon, 1 item ≈ 15g (typical bacon slice)
            # This is an approximation and could be made more specific per food
            return amount * 15
        else:
            return amount  # Default to grams


class NotificationUtils:
    """Utility class for notification handling"""
    
    @staticmethod
    def send_verification_email(user_email: str, token: str) -> bool:
        """Send verification email (placeholder for actual email service)"""
        # In production, integrate with SendGrid, Mailgun, or similar
        verification_url = f"{request.host_url}verify-email/{token}"
        subject = "Verify Your Email - Ki Wellness"
        message = f"""
        Hello!
        
        Please verify your email address by clicking the link below:
        {verification_url}
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        Ki Wellness Team
        """
        
        try:
            # Placeholder for actual email sending
            print(f"📧 Verification email would be sent to {user_email}")
            print(f"📧 Subject: {subject}")
            print(f"📧 Message: {message}")
            return True
        except Exception as e:
            print(f"❌ Error sending verification email: {e}")
            return False
    
    @staticmethod
    def send_verification_sms(phone_number: str, code: str) -> bool:
        """Send verification SMS (placeholder for actual SMS service)"""
        # In production, integrate with Twilio, AWS SNS, or similar
        message = f"Your Ki Wellness verification code is: {code}. Valid for 10 minutes."
        
        try:
            # Placeholder for actual SMS sending
            print(f"📱 Verification SMS would be sent to {phone_number}")
            print(f"📱 Message: {message}")
            return True
        except Exception as e:
            print(f"❌ Error sending verification SMS: {e}")
            return False


class DataQualityUtils:
    """Utility class for data quality assessment"""
    
    @staticmethod
    def assess_nutritional_data_quality(entry: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of nutritional data in a food entry"""
        core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
        extended_nutrients = [
            'saturated_fat', 'trans_fat', 'cholesterol', 'potassium', 'calcium', 'iron',
            'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 'vitamin_b6', 'vitamin_b12',
            'magnesium', 'zinc', 'phosphorus', 'manganese', 'selenium', 'copper', 'thiamin',
            'riboflavin', 'niacin', 'folate', 'pantothenic_acid', 'biotin', 'choline', 'betaine',
            'taurine', 'caffeine', 'alcohol', 'water_content', 'ash'
        ]
        
        has_core_nutrition = any(entry.get(nutrient) is not None for nutrient in core_nutrients)
        has_extended_nutrition = any(entry.get(nutrient) is not None for nutrient in extended_nutrients)
        
        if has_extended_nutrition:
            quality_level = 'full'
        elif has_core_nutrition:
            quality_level = 'basic'
        else:
            quality_level = 'none'
        
        return {
            'quality_level': quality_level,
            'has_core_nutrition': has_core_nutrition,
            'has_extended_nutrition': has_extended_nutrition,
            'core_nutrients_present': sum(1 for nutrient in core_nutrients if entry.get(nutrient) is not None),
            'extended_nutrients_present': sum(1 for nutrient in extended_nutrients if entry.get(nutrient) is not None)
        }
