"""
Authentication routes - Login, Register, Password Reset, Email Verification
Handles user authentication and account management
"""
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User
from database_security import validate_user_input, sanitize_user_input
from security_middleware import rate_limit
from utils.helpers import get_app_setting

# Create blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=50, window=60)  # Increased limit for development
def login():
    """User login"""
    if request.method == 'POST':
        # Validate and sanitize inputs
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Input validation
        if not validate_user_input(username, max_length=50):
            flash('Invalid username format', 'error')
            return render_template('login.html')
            
        if not validate_user_input(password, max_length=100):
            flash('Invalid password format', 'error')
            return render_template('login.html')
        
        # Sanitize inputs
        username = sanitize_user_input(username, max_length=50)
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            # Check if email is verified
            if not user.email_verified:
                flash('Please verify your email address before logging in. Check your inbox for the verification link.', 'warning')
                return render_template('login.html')
            
            login_user(user, remember=True)  # Enable remember me functionality
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            session.permanent = True  # Make session permanent for timeout tracking
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=300)  # Limit registration attempts
def register():
    """User registration"""
    # Check if new account creation is enabled
    new_accounts_enabled = get_app_setting('new_accounts_enabled', 'true').lower() == 'true'
    allowed_emails = get_app_setting('allowed_emails', '').split(',')
    allowed_emails = [email.strip().lower() for email in allowed_emails if email.strip()]
    
    # Always show the registration form, but pass registration status to template
    registration_disabled = not new_accounts_enabled
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        
        # Check if registration is disabled and email is not in allowed list
        if not new_accounts_enabled and email not in allowed_emails:
            flash('New account registration is currently disabled. Your email address is not on the allowed list. Please contact the administrator.', 'error')
            return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)
    
    if request.method == 'POST':
        # Validate and sanitize all inputs
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '')
        gender = request.form.get('gender', '')
        activity_level = request.form.get('activity_level', '')
        health_goals = request.form.get('health_goals', '').strip()
        terms_agreed = request.form.get('terms_agreed') == 'on'
        disclaimer_agreed = request.form.get('disclaimer_agreed') == 'on'
        
        # Input validation
        if not validate_user_input(username, max_length=50):
            flash('Invalid username format', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
            
        if not validate_user_input(email, max_length=120):
            flash('Invalid email format', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
            
        if not validate_user_input(password, max_length=100):
            flash('Invalid password format', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
            
        if not validate_user_input(name, max_length=100):
            flash('Invalid name format', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
        
        # Sanitize inputs
        username = sanitize_user_input(username, max_length=50)
        email = sanitize_user_input(email, max_length=120)
        name = sanitize_user_input(name, max_length=100)
        health_goals = sanitize_user_input(health_goals, max_length=500)
        
        # Validate required fields
        if not all([username, email, password, name]):
            flash('Please fill in all required fields', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
        
        # Validate agreements
        if not terms_agreed:
            flash('You must agree to the Terms of Service', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
            
        if not disclaimer_agreed:
            flash('You must agree to the Health Disclaimer', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
        
        # Validate password strength
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            flash(f'Password requirement: {error_message}', 'error')
            return render_template('register.html', registration_disabled=registration_disabled)
        
        # Parse age if provided
        age_int = None
        if age:
            try:
                age_int = int(age)
                if age_int < 13 or age_int > 120:
                    flash('Please enter a valid age between 13 and 120', 'error')
                    return render_template('register.html', registration_disabled=registration_disabled)
            except ValueError:
                flash('Please enter a valid age', 'error')
                return render_template('register.html', registration_disabled=registration_disabled)
        
        try:
            # Create new user
            verification_token = str(uuid.uuid4())
            
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                name=name,
                age=age_int,
                gender=gender if gender else None,
                activity_level=activity_level if activity_level else None,
                health_goals=health_goals,
                agreed_to_terms=terms_agreed,
                agreed_to_disclaimer=disclaimer_agreed,
                agreements_date=datetime.utcnow(),
                email_verification_token=verification_token,
                email_verified=False
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            try:
                from services.email_service import EmailService
                email_service = EmailService()
                
                if email_service.send_verification_email(email, verification_token, name):
                    flash('Registration successful! Please check your email to verify your account before logging in.', 'success')
                else:
                    flash('Registration successful! However, we couldn\'t send the verification email. Please contact support.', 'warning')
            except Exception as email_error:
                print(f"❌ Email service error: {email_error}")
                flash('Registration successful! However, we couldn\'t send the verification email. Please contact support.', 'warning')
            
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html', registration_disabled=registration_disabled, allowed_emails=allowed_emails)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/extend-session')
@login_required
def extend_session():
    """Extend user session by updating session expiry"""
    session.permanent = True
    return {'status': 'session_extended'}, 200


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot_password.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                # Generate reset token
                reset_token = str(uuid.uuid4())
                reset_expires = datetime.now() + timedelta(hours=24)
                
                # Update user with reset token
                user.reset_token = reset_token
                user.reset_token_expires = reset_expires
                db.session.commit()
                
                # Send password reset email
                from services.email_service import EmailService
                email_service = EmailService()
                
                if email_service.send_password_reset_email(email, reset_token, user.name):
                    flash('Password reset link has been sent to your email address.', 'success')
                else:
                    flash('Failed to send password reset email. Please try again later.', 'error')
                    
            except Exception as e:
                print(f"Password reset error: {e}")
                flash('An error occurred. Please try again later.', 'error')
        else:
            # For security, don't reveal whether email exists or not
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
    
    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    # Find user by reset token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now():
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Validate password strength
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            flash(f'Password requirement: {error_message}', 'error')
            return render_template('reset_password.html', token=token)
        
        try:
            # Update user password and clear reset token
            user.password_hash = generate_password_hash(password)
            user.reset_token = None
            user.reset_token_expires = None
            db.session.commit()
            
            flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Password reset error: {e}")
            flash('An error occurred while resetting your password. Please try again.', 'error')
    
    return render_template('reset_password.html', token=token)


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Handle email verification with token"""
    # Find user by verification token
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash('Invalid verification link.', 'error')
        return redirect(url_for('auth.login'))
    
    if user.email_verified:
        flash('Your email is already verified. You can log in.', 'info')
        return redirect(url_for('auth.login'))
    
    try:
        # Mark email as verified
        user.email_verified = True
        user.email_verification_token = None
        db.session.commit()
        
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Email verification error: {e}")
        flash('An error occurred during verification. Please try again or contact support.', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification', methods=['POST'])
@rate_limit(max_requests=3, window=300)  # Limit resend attempts
def resend_verification():
    """Resend email verification"""
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        flash('Please enter your email address.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('No account found with that email address.', 'error')
        return redirect(url_for('auth.login'))
    
    if user.email_verified:
        flash('Your email is already verified.', 'info')
        return redirect(url_for('auth.login'))
    
    try:
        # Generate new verification token if needed
        if not user.email_verification_token:
            user.email_verification_token = str(uuid.uuid4())
            db.session.commit()
        
        # Send verification email
        from services.email_service import EmailService
        email_service = EmailService()
        
        if email_service.send_verification_email(email, user.email_verification_token, user.name):
            flash('Verification email sent! Please check your inbox.', 'success')
        else:
            flash('Failed to send verification email. Please try again later.', 'error')
            
    except Exception as e:
        print(f"Resend verification error: {e}")
        flash('An error occurred. Please try again later.', 'error')
    
    return redirect(url_for('auth.login'))


def validate_password_strength(password):
    """
    Validate password strength with comprehensive requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not has_upper:
        return False, "Password must contain at least one uppercase letter"
    
    if not has_lower:
        return False, "Password must contain at least one lowercase letter"
    
    if not has_digit:
        return False, "Password must contain at least one number"
    
    if not has_special:
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    
    return True, "Password meets all requirements"
