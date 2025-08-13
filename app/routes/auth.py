"""
Ki Wellness - Authentication Routes
===================================

This module contains all authentication-related routes including
login, registration, email/phone verification, and password reset.

Author: Ki Wellness Team
Version: 2.0
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, User, UserProfile, UserAgreement
from ..utils import ValidationUtils, SecurityUtils, NotificationUtils
from ..services import UserService, SystemService
from ..decorators import login_required
from ..config import oauth, google_oauth, OAUTH_AVAILABLE

# Create blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        # Validate input
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'}), 400
        
        # Check if new accounts are enabled
        if not SystemService.are_new_accounts_enabled():
            return jsonify({'success': False, 'error': 'New account creation is currently disabled'}), 403
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                return jsonify({'success': False, 'error': 'Account is suspended. Please contact support.'}), 403
            
            # Set session
            session['user_id'] = user.id
            session['last_activity'] = datetime.utcnow().isoformat()
            session.permanent = remember_me
            
            # Update last login
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'redirect_url': url_for('dashboard'),
                'message': 'Login successful!'
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
    
    return render_template('login.html')


@auth_bp.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    if not OAUTH_AVAILABLE:
        flash('OAuth is not available', 'error')
        return redirect(url_for('login'))
    
    return google_oauth.authorize(callback=url_for('auth.google_authorized', _external=True))


@auth_bp.route('/login/google/authorized')
def google_authorized():
    """Handle Google OAuth callback"""
    if not OAUTH_AVAILABLE:
        flash('OAuth is not available', 'error')
        return redirect(url_for('login'))
    
    resp = google_oauth.authorized_response()
    if resp is None or resp.get('access_token') is None:
        flash('Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        ), 'error')
        return redirect(url_for('login'))
    
    session['google_token'] = (resp['access_token'], '')
    me = google_oauth.get('userinfo')
    
    # Check if user exists
    user = User.query.filter_by(oauth_id=me.data['id']).first()
    
    if not user:
        # Create new user
        user = User(
            username=me.data['email'].split('@')[0],
            email=me.data['email'],
            oauth_provider='google',
            oauth_id=me.data['id'],
            oauth_email=me.data['email'],
            oauth_name=me.data.get('name', ''),
            oauth_picture=me.data.get('picture', ''),
            email_verified=True,  # Google emails are pre-verified
            is_active=True
        )
        user.set_password(SecurityUtils.generate_verification_token())  # Random password
        
        db.session.add(user)
        db.session.commit()
        
        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            name=me.data.get('name', ''),
            avatar='default-avatar.png'
        )
        db.session.add(profile)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
    
    # Set session
    session['user_id'] = user.id
    session['last_activity'] = datetime.utcnow().isoformat()
    
    return redirect(url_for('dashboard'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Check if new accounts are enabled
        if not SystemService.are_new_accounts_enabled():
            return jsonify({'success': False, 'error': 'New account creation is currently disabled'}), 403
        
        # Validate input
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        phone = data.get('phone', '').strip()
        
        # Validation
        if not ValidationUtils.is_kiwellness_username(username):
            return jsonify({'success': False, 'error': 'Invalid username format'}), 400
        
        if not ValidationUtils.validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        if not ValidationUtils.validate_password_strength(password):
            return jsonify({'success': False, 'error': 'Password does not meet requirements'}), 400
        
        if phone and not ValidationUtils.validate_phone(phone):
            return jsonify({'success': False, 'error': 'Invalid phone number format'}), 400
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 409
        
        # Create user
        user = User(
            username=username,
            email=email,
            phone=phone,
            is_active=True
        )
        user.set_password(password)
        
        # Generate verification tokens
        user.email_verification_token = SecurityUtils.generate_verification_token()
        if phone:
            user.phone_verification_code = SecurityUtils.generate_phone_verification_code()
            user.phone_verification_expires = datetime.utcnow() + timedelta(minutes=10)
        
        db.session.add(user)
        db.session.commit()
        
        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            name=username,
            avatar='default-avatar.png'
        )
        db.session.add(profile)
        db.session.commit()
        
        # Send verification emails/SMS
        if email:
            NotificationUtils.send_verification_email(email, user.email_verification_token)
        
        if phone:
            NotificationUtils.send_verification_sms(phone, user.phone_verification_code)
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully! Please check your email and phone for verification codes.',
            'redirect_url': url_for('onboarding')
        })
    
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address with token"""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if user:
        user.email_verified = True
        user.email_verification_token = None
        db.session.commit()
        
        flash('Email verified successfully!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid or expired verification token.', 'error')
        return redirect(url_for('login'))


@auth_bp.route('/verify-phone', methods=['GET', 'POST'])
def verify_phone():
    """Verify phone number with code"""
    if request.method == 'POST':
        data = request.get_json()
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()
        
        user = User.query.filter_by(phone=phone).first()
        
        if user and user.phone_verification_code == code:
            if user.phone_verification_expires and datetime.utcnow() > user.phone_verification_expires:
                return jsonify({'success': False, 'error': 'Verification code has expired'}), 400
            
            user.phone_verified = True
            user.phone_verification_code = None
            user.phone_verification_expires = None
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Phone verified successfully!'})
        else:
            return jsonify({'success': False, 'error': 'Invalid verification code'}), 400
    
    return render_template('verify_phone.html')


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email/SMS"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    
    if email:
        user = User.query.filter_by(email=email).first()
        if user and not user.email_verified:
            user.email_verification_token = SecurityUtils.generate_verification_token()
            db.session.commit()
            NotificationUtils.send_verification_email(email, user.email_verification_token)
            return jsonify({'success': True, 'message': 'Verification email sent!'})
    
    if phone:
        user = User.query.filter_by(phone=phone).first()
        if user and not user.phone_verified:
            user.phone_verification_code = SecurityUtils.generate_phone_verification_code()
            user.phone_verification_expires = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()
            NotificationUtils.send_verification_sms(phone, user.phone_verification_code)
            return jsonify({'success': True, 'message': 'Verification SMS sent!'})
    
    return jsonify({'success': False, 'error': 'User not found or already verified'}), 404


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request"""
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not ValidationUtils.validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate reset token
            user.email_verification_token = SecurityUtils.generate_verification_token()
            db.session.commit()
            
            # Send reset email
            NotificationUtils.send_verification_email(email, user.email_verification_token)
            
            return jsonify({'success': True, 'message': 'Password reset email sent!'})
        else:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
    
    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password', '')
        
        if not ValidationUtils.validate_password_strength(password):
            return jsonify({'success': False, 'error': 'Password does not meet requirements'}), 400
        
        user.set_password(password)
        user.email_verification_token = None
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password reset successfully!'})
    
    return render_template('reset_password.html', token=token)


@auth_bp.route('/extend-session', methods=['POST'])
@login_required
def extend_session():
    """Extend user session"""
    session['last_activity'] = datetime.utcnow().isoformat()
    return jsonify({'success': True, 'message': 'Session extended'})
