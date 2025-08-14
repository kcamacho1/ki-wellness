"""
Ki Wellness - Database Models
=============================

This module contains all database models for the Ki Wellness application.
Models are organized by functionality and include proper relationships and constraints.

Author: Ki Wellness Team
Version: 2.0
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional

# Create SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """Initialize the database with Flask app"""
    db.init_app(app)
    return db


class User(db.Model):
    """
    User model for authentication and user management
    
    Handles user authentication, verification, and basic user information.
    Supports both traditional username/password and OAuth authentication.
    """
    __tablename__ = 'users'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True, index=True)
    
    # Account status and permissions
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Verification fields
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    phone_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True, unique=True)
    phone_verification_code = db.Column(db.String(6), nullable=True)
    phone_verification_expires = db.Column(db.DateTime, nullable=True)
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    push_notifications = db.Column(db.Boolean, default=True)
    
    # OAuth fields
    oauth_provider = db.Column(db.String(20), nullable=True)
    oauth_id = db.Column(db.String(255), nullable=True, unique=True)
    oauth_email = db.Column(db.String(255), nullable=True)
    oauth_name = db.Column(db.String(255), nullable=True)
    oauth_picture = db.Column(db.String(500), nullable=True)
    
    def set_password(self, password: str) -> None:
        """Set user password with secure hashing"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify user password"""
        return check_password_hash(self.password_hash, password)
    
    def is_verified_for_ai(self) -> bool:
        """Check if user is verified for AI usage (both email and phone verified)"""
        return self.email_verified and self.phone_verified
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'


class UserProfile(db.Model):
    """
    User Profile model for detailed user information
    
    Stores comprehensive user profile data including wellness goals,
    physical attributes, and personal preferences.
    """
    __tablename__ = 'user_profiles'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(100), nullable=True, default='default-avatar.png')
    weight_unit = db.Column(db.String(10), nullable=True, default='kg')
    
    # Basic profile information
    date_of_birth = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)  # male, female, self-described
    weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    height_ft = db.Column(db.Float, nullable=True)  # Height in feet (e.g., 5.6 for 5'6")
    
    # Wellness goals and preferences
    goal = db.Column(db.String(100), nullable=True)
    goals = db.Column(db.Text, nullable=True)
    custom_goal = db.Column(db.String(200), nullable=True)
    ailments = db.Column(db.Text, nullable=True)
    dietary_preferences = db.Column(db.Text, nullable=True)
    sleep_schedule = db.Column(db.String(100), nullable=True)
    
    # Physical wellness
    daily_activities = db.Column(db.Text, nullable=True)
    exercise_routine = db.Column(db.Text, nullable=True)
    day_notes = db.Column(db.Text, nullable=True)
    night_notes = db.Column(db.Text, nullable=True)
    
    # Spiritual and emotional wellness
    spiritual_religion = db.Column(db.Text, nullable=True)
    self_connection = db.Column(db.Text, nullable=True)
    surroundings_connection = db.Column(db.Text, nullable=True)
    providing_others = db.Column(db.Text, nullable=True)
    safe_groups = db.Column(db.Text, nullable=True)
    awe_things = db.Column(db.Text, nullable=True)
    creative_expression = db.Column(db.Text, nullable=True)
    upsetting_situations = db.Column(db.Text, nullable=True)
    spirit_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='profile', uselist=False)
    
    def __repr__(self) -> str:
        return f'<UserProfile {self.name}>'



class FoodJournal(db.Model):
    """
    Food Journal model for user food entries
    
    Stores comprehensive food journal entries with nutritional data,
    mood tracking, and metadata.
    """
    __tablename__ = 'food_journal'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    food_name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    serving_size = db.Column(db.Float, nullable=False)
    serving_unit = db.Column(db.String(20), nullable=False)
    
    # Core nutritional values (displayed to user)
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    fiber = db.Column(db.Float, nullable=True)
    sugar = db.Column(db.Float, nullable=True)
    sodium = db.Column(db.Float, nullable=True)
    
    # Extended nutritional values (stored but not displayed)
    saturated_fat = db.Column(db.Float, nullable=True)
    trans_fat = db.Column(db.Float, nullable=True)
    cholesterol = db.Column(db.Float, nullable=True)
    potassium = db.Column(db.Float, nullable=True)
    calcium = db.Column(db.Float, nullable=True)
    iron = db.Column(db.Float, nullable=True)
    vitamin_a = db.Column(db.Float, nullable=True)
    vitamin_c = db.Column(db.Float, nullable=True)
    vitamin_d = db.Column(db.Float, nullable=True)
    vitamin_e = db.Column(db.Float, nullable=True)
    vitamin_k = db.Column(db.Float, nullable=True)
    vitamin_b6 = db.Column(db.Float, nullable=True)
    vitamin_b12 = db.Column(db.Float, nullable=True)
    magnesium = db.Column(db.Float, nullable=True)
    zinc = db.Column(db.Float, nullable=True)
    phosphorus = db.Column(db.Float, nullable=True)
    manganese = db.Column(db.Float, nullable=True)
    selenium = db.Column(db.Float, nullable=True)
    copper = db.Column(db.Float, nullable=True)
    thiamin = db.Column(db.Float, nullable=True)
    riboflavin = db.Column(db.Float, nullable=True)
    niacin = db.Column(db.Float, nullable=True)
    folate = db.Column(db.Float, nullable=True)
    pantothenic_acid = db.Column(db.Float, nullable=True)
    biotin = db.Column(db.Float, nullable=True)
    choline = db.Column(db.Float, nullable=True)
    betaine = db.Column(db.Float, nullable=True)
    taurine = db.Column(db.Float, nullable=True)
    caffeine = db.Column(db.Float, nullable=True)
    alcohol = db.Column(db.Float, nullable=True)
    water_content = db.Column(db.Float, nullable=True)
    ash = db.Column(db.Float, nullable=True)
    
    # Metadata
    data_source = db.Column(db.String(50), nullable=True)
    barcode = db.Column(db.String(50), nullable=True)
    time_of_day = db.Column(db.String(20), nullable=True)
    water_amount = db.Column(db.Float, nullable=True)
    water_unit = db.Column(db.String(20), nullable=True)
    mood = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    consumed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_profile = db.relationship('UserProfile', backref='food_entries')
    
    def __repr__(self) -> str:
        return f'<FoodJournal {self.food_name}>'


class MoodEntry(db.Model):
    """
    Mood Entry model for quick mood logging
    
    Stores user mood entries with timestamps and optional notes.
    """
    __tablename__ = 'mood_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    mood = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_profile = db.relationship('UserProfile', backref='mood_entries')
    
    def __repr__(self) -> str:
        return f'<MoodEntry {self.mood}>'


class PatternsCache(db.Model):
    """
    Patterns Cache model for storing analysis results
    
    Caches AI analysis results to improve performance and reduce API calls.
    """
    __tablename__ = 'patterns_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    period_type = db.Column(db.String(10), nullable=False)  # '7day' or '30day'
    analysis = db.Column(db.Text, nullable=True)
    suggestions = db.Column(db.Text, nullable=True)
    summary = db.Column(db.JSON, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_profile = db.relationship('UserProfile', backref='patterns_cache')
    
    def __repr__(self) -> str:
        return f'<PatternsCache {self.period_type}>'


class Review(db.Model):
    """
    Review model for user testimonials and feedback
    
    Stores user reviews with moderation and spam detection features.
    """
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    spam_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<Review {self.name}>'


class UserAgreement(db.Model):
    """
    User Agreement model for tracking legal agreements
    
    Stores user acceptance of privacy policy, terms of service, and disclaimers.
    """
    __tablename__ = 'user_agreements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    privacy_policy_accepted = db.Column(db.Boolean, default=False)
    terms_of_service_accepted = db.Column(db.Boolean, default=False)
    disclaimer_accepted = db.Column(db.Boolean, default=False)
    privacy_policy_version = db.Column(db.String(20), nullable=True)
    terms_version = db.Column(db.String(20), nullable=True)
    disclaimer_version = db.Column(db.String(20), nullable=True)
    accepted_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='agreements')
    
    def __repr__(self) -> str:
        return f'<UserAgreement {self.user_id}>'


class Reminder(db.Model):
    """
    Reminder model for wellness reminders
    
    Stores user-configured reminders for various wellness activities.
    """
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    reminder_type = db.Column(db.String(50), nullable=False)  # water, macronutrients, mood
    frequency = db.Column(db.String(50), nullable=False)  # daily, hourly, custom
    time_of_day = db.Column(db.Time, nullable=False)
    days_of_week = db.Column(db.String(100))  # JSON string for custom days
    is_active = db.Column(db.Boolean, default=True)
    last_triggered = db.Column(db.DateTime)
    next_trigger = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='reminders')
    
    def __repr__(self) -> str:
        return f'<Reminder {self.title}>'


class ReminderLog(db.Model):
    """
    Reminder Log model for tracking reminder interactions
    
    Logs when reminders are triggered and how users respond to them.
    """
    __tablename__ = 'reminder_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    action_taken = db.Column(db.String(50))  # completed, snoozed, dismissed
    response_time = db.Column(db.Integer)  # seconds from trigger to response
    
    # Relationships
    reminder = db.relationship('Reminder', backref='logs')
    user = db.relationship('User', backref='reminder_logs')
    
    def __repr__(self) -> str:
        return f'<ReminderLog {self.reminder_id}>'


class Notification(db.Model):
    """
    Notification model for tracking sent notifications
    
    Stores records of notifications sent to users via various channels.
    """
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=True)
    notification_type = db.Column(db.String(50), nullable=False)  # email, sms, push
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, sent, failed
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    reminder = db.relationship('Reminder', backref='notifications')
    
    def __repr__(self) -> str:
        return f'<Notification {self.notification_type}>'


class SystemSettings(db.Model):
    """
    System Settings model for application configuration
    
    Stores system-wide settings that can be modified by administrators.
    """
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='system_settings')
    
    def __repr__(self) -> str:
        return f'<SystemSettings {self.key}>'


class TokenUsage(db.Model):
    """
    Token Usage model for tracking OpenAI API usage
    
    Tracks token usage and costs for billing and analytics purposes.
    """
    __tablename__ = 'token_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM format
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    cost_usd = db.Column(db.Float, default=0.0)
    model_used = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='token_usage')
    
    def __repr__(self) -> str:
        return f'<TokenUsage {self.user_id} {self.month}>'


class APICosts(db.Model):
    """
    API Costs model for tracking OpenAI model pricing
    
    Stores current pricing for different OpenAI models for cost calculation.
    """
    __tablename__ = 'api_costs'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), nullable=False)
    input_cost_per_1m = db.Column(db.Float, nullable=False)  # Cost per 1M input tokens
    output_cost_per_1m = db.Column(db.Float, nullable=False)  # Cost per 1M output tokens
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='api_costs')
    
    def __repr__(self) -> str:
        return f'<APICosts {self.model_name}>'


class UserSubscription(db.Model):
    """
    User Subscription model for subscription management
    
    Tracks user subscriptions, billing cycles, and session allowances.
    """
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    subscription_type = db.Column(db.String(20), nullable=False, default='subscription')
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    monthly_fee_usd = db.Column(db.Float, default=10.0)
    sessions_per_month = db.Column(db.Integer, default=600)
    sessions_used_this_month = db.Column(db.Integer, default=0)
    billing_cycle_start = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='subscription', uselist=False)
    
    def __repr__(self) -> str:
        return f'<UserSubscription {self.user_id}>'


class SessionCredits(db.Model):
    """
    Session Credits model for pay-as-you-go usage
    
    Tracks purchased session credits and their usage.
    """
    __tablename__ = 'session_credits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    credits_purchased = db.Column(db.Integer, default=0)
    credits_used = db.Column(db.Integer, default=0)
    credits_remaining = db.Column(db.Integer, default=0)
    stripe_payment_intent_id = db.Column(db.String(100), nullable=True)
    payment_amount_usd = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='session_credits')
    
    def __repr__(self) -> str:
        return f'<SessionCredits {self.user_id}>'


class AIUsageSession(db.Model):
    """
    AI Usage Session model for tracking AI interactions
    
    Records individual AI usage sessions for analytics and billing.
    """
    __tablename__ = 'ai_usage_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_type = db.Column(db.String(50), nullable=False)  # 'patterns_analysis', 'ai_chat', etc.
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    cost_usd = db.Column(db.Float, default=0.0)
    model_used = db.Column(db.String(50), nullable=True)
    subscription_used = db.Column(db.Boolean, default=True)
    credit_id = db.Column(db.Integer, db.ForeignKey('session_credits.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ai_sessions')
    credit = db.relationship('SessionCredits', backref='usage_sessions')
    
    def __repr__(self) -> str:
        return f'<AIUsageSession {self.session_type}>'


class EmailSubscription(db.Model):
    """
    Email Subscription model for waitlist management
    
    Tracks email addresses of users who want to be notified when account creation opens.
    """
    __tablename__ = 'email_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    unsubscribe_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<EmailSubscription {self.email}>'
