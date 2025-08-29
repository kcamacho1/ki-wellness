"""
Helper functions and utilities
"""
import re
import html
from datetime import datetime
from flask import jsonify
from database import db, AppSettings, AIUsageLog

# OpenRouter model configuration
OPENROUTER_MODEL = "openai/gpt-4o-mini"


def initialize_default_settings():
    """Initialize default app settings"""
    settings = [
        ('new_accounts_enabled', 'true', 'Enable or disable new user account creation'),
        ('maintenance_mode', 'false', 'Enable maintenance mode for the application'),
        ('max_users', '1000', 'Maximum number of users allowed in the system'),
        ('allowed_emails', '', 'Comma-separated list of email addresses allowed to register even when disabled'),
        ('human_help_payment_type', '30min_session', 'Payment type for human help: 30min_session or donation'),
        ('calendly_link', 'https://calendly.com/ki-wellness/human-health-coach', 'Calendly link for scheduling appointments')
    ]
    
    for key, value, description in settings:
        setting = AppSettings.query.filter_by(key=key).first()
        if not setting:
            setting = AppSettings(key=key, value=value, description=description)
            db.session.add(setting)
    
    db.session.commit()


def get_app_setting(key, default=None):
    """Get an app setting value"""
    setting = AppSettings.query.filter_by(key=key).first()
    return setting.value if setting else default


def set_app_setting(key, value):
    """Set an app setting value"""
    # Convert boolean values to lowercase strings for consistency
    if isinstance(value, bool):
        value = str(value).lower()
    elif isinstance(value, str) and value.lower() in ['true', 'false']:
        value = value.lower()
    
    setting = AppSettings.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = AppSettings(key=key, value=value)
        db.session.add(setting)
    
    db.session.commit()
    return True


def check_ai_usage_limits(user_id):
    """Check if user has exceeded AI usage limits (PER-USER limits, globally configured)"""
    if not get_app_setting('enforce_limits', 'false').lower() == 'true':
        return True, None  # Limits not enforced
    
    today = datetime.utcnow().date()
    this_month = datetime.utcnow().replace(day=1).date()
    
    # Check PER-USER daily token limit (configured globally, applied per user)
    daily_token_limit = int(get_app_setting('daily_token_limit', '0'))
    if daily_token_limit > 0:
        today_tokens = db.session.query(
            db.func.sum(AIUsageLog.input_tokens + AIUsageLog.output_tokens)
        ).filter(
            AIUsageLog.user_id == user_id,
            db.func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        if today_tokens >= daily_token_limit:
            return False, f"Daily token limit ({daily_token_limit}) exceeded. You used: {today_tokens}"
    
    # Check PER-USER daily call limit (configured globally, applied per user)
    daily_call_limit = int(get_app_setting('daily_call_limit', '0'))
    if daily_call_limit > 0:
        today_calls = db.session.query(
            db.func.count(AIUsageLog.id)
        ).filter(
            AIUsageLog.user_id == user_id,
            db.func.date(AIUsageLog.created_at) == today
        ).scalar() or 0
        
        if today_calls >= daily_call_limit:
            return False, f"Daily call limit ({daily_call_limit}) exceeded. You made: {today_calls} calls"
    
    # Check PER-USER monthly cost limit (configured globally, applied per user)
    monthly_cost_limit = float(get_app_setting('monthly_cost_limit', '0'))
    if monthly_cost_limit > 0:
        month_cost = db.session.query(
            db.func.sum(AIUsageLog.total_cost)
        ).filter(
            AIUsageLog.user_id == user_id,
            db.func.date(AIUsageLog.created_at) >= this_month
        ).scalar() or 0
        
        if month_cost >= monthly_cost_limit:
            return False, f"Monthly cost limit (${monthly_cost_limit:.4f}) exceeded. Your cost: ${month_cost:.4f}"
    
    return True, None  # All limits passed


def validate_user_input(text, max_length=1000):
    """
    Validate user input for safety and length constraints
    Returns True if valid, False otherwise
    """
    if not text:
        return True  # Empty input is valid
    
    if not isinstance(text, str):
        return False
    
    if len(text) > max_length:
        return False
    
    # Basic security checks
    if any(dangerous in text.lower() for dangerous in ['<script', 'javascript:', 'data:', 'vbscript:']):
        return False
    
    return True


def sanitize_user_input(text, max_length=1000):
    """
    Sanitize user input by removing dangerous content and limiting length
    Returns cleaned string
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Limit length
    text = text[:max_length]
    
    # HTML escape
    text = html.escape(text)
    
    # Remove potentially dangerous patterns
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'data:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def validate_password_strength(password):
    """
    Validate password strength with comprehensive requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    
    # Check for common patterns
    common_patterns = [
        'password', '123456', 'qwerty', 'abc123', 'password123',
        'admin', 'user', 'test', 'welcome', 'letmein'
    ]
    
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            return False, "Password contains common patterns that are not allowed"
    
    # Check for repeated characters
    if re.search(r'(.)\1{2,}', password):
        return False, "Password cannot contain more than 2 consecutive identical characters"
    
    return True, "Password meets all requirements"
