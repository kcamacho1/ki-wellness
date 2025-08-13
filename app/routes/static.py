"""
Ki Wellness - Static Routes
===========================

This module contains static page routes like terms of service,
privacy policy, disclaimer, and other informational pages.

Author: Ki Wellness Team
Version: 2.0
"""

from flask import Blueprint, render_template, request, jsonify
from ..models import db, Review
from ..utils import SecurityUtils

# Create blueprint
static_bp = Blueprint('static', __name__)


@static_bp.route('/')
def index():
    """Home page"""
    return render_template('landing.html')


@static_bp.route('/coaching')
def coaching():
    """Coaching overview page"""
    return render_template('coaching.html')


@static_bp.route('/human-coaching')
def human_coaching():
    """Human coaching page"""
    return render_template('coaching.html')


@static_bp.route('/ai-coaching')
def ai_coaching():
    """AI coaching page"""
    return render_template('ai_coaching.html')


@static_bp.route('/coaching-selection')
def coaching_selection():
    """Coaching selection page"""
    return render_template('coaching_selection.html')


@static_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')


@static_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')


@static_bp.route('/disclaimer')
def disclaimer():
    """Disclaimer page"""
    return render_template('disclaimer.html')


@static_bp.route('/ai-self-health')
def ai_self_health():
    """AI self-health page"""
    return render_template('ai_self_health.html')


@static_bp.route('/reviews')
def reviews():
    """Public reviews page"""
    # Get approved reviews
    approved_reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(10).all()
    
    return render_template('reviews.html', reviews=approved_reviews)


@static_bp.route('/reviews/submit', methods=['POST'])
def submit_review():
    """Submit a new review"""
    data = request.get_json()
    
    # Validate required fields
    name = data.get('name', '').strip()
    rating = data.get('rating')
    content = data.get('content', '').strip()
    
    if not name or not rating or not content:
        return jsonify({'success': False, 'error': 'Name, rating, and content are required'}), 400
    
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400
    
    if len(content) < 10:
        return jsonify({'success': False, 'error': 'Review content must be at least 10 characters'}), 400
    
    # Check for spam indicators
    spam_score = 0
    
    # Check for excessive links
    if content.count('http') > 2:
        spam_score += 3
    
    # Check for excessive capitalization
    if sum(1 for c in content if c.isupper()) > len(content) * 0.3:
        spam_score += 2
    
    # Check for repeated words
    words = content.lower().split()
    if len(set(words)) < len(words) * 0.5:
        spam_score += 2
    
    # Create review
    review = Review(
        name=name,
        rating=rating,
        content=content,
        is_approved=False,  # Requires admin approval
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        spam_score=spam_score
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Review submitted successfully! It will be reviewed and published soon.'
    })


@static_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Validate input
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        if not name or not email or not subject or not message:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Check for spam indicators
        if len(message) < 10:
            return jsonify({'success': False, 'error': 'Message must be at least 10 characters'}), 400
        
        # In a real application, you would send an email here
        # For now, just log the contact request
        print(f"📧 Contact form submission:")
        print(f"   From: {name} ({email})")
        print(f"   Subject: {subject}")
        print(f"   Message: {message}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your message! We will get back to you soon.'
        })
    
    return render_template('contact.html')


@static_bp.route('/api/recaptcha-status')
def recaptcha_status():
    """Get reCAPTCHA configuration status"""
    from flask import current_app
    
    # Check if we're on localhost/development
    is_localhost = request.host in ['localhost', '127.0.0.1', '0.0.0.0'] or request.host.startswith('localhost:')
    
    # Disable reCAPTCHA on localhost for development
    enabled = not is_localhost
    
    return jsonify({
        'enabled': enabled,
        'site_key': current_app.config.get('RECAPTCHA_SITE_KEY', '') if enabled else ''
    })
