"""
Static page routes - Privacy, Terms, Disclaimer, etc.
These are simple content pages that don't require authentication
"""
from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app
from flask_login import current_user
from sqlalchemy import text
from database import db

# Create blueprint
static_bp = Blueprint('static_pages', __name__)


@static_bp.route('/')
def index():
    """Homepage - redirect to dashboard if logged in, otherwise show landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('landing.html')


@static_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')


@static_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')


@static_bp.route('/disclaimer')
def disclaimer():
    """Disclaimer page"""
    return render_template('disclaimer.html')


@static_bp.route('/human-help')
def human_help():
    """Human help page with Calendly booking"""
    return render_template('human_help.html')


@static_bp.route('/robots.txt')
def robots_txt():
    """Serve robots.txt for AI crawlers and search engines"""
    return send_from_directory(current_app.static_folder, 'robots.txt', mimetype='text/plain')


@static_bp.route('/sitemap.xml')
def sitemap_xml():
    """Serve sitemap.xml for search engines"""
    return send_from_directory(current_app.static_folder, 'sitemap.xml', mimetype='application/xml')


@static_bp.route('/health')
def health_check():
    """Health check endpoint for debugging"""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        return {
            'status': 'healthy',
            'database': 'connected',
            'message': 'All systems operational'
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'database': 'error',
            'message': f'Database connection failed: {str(e)}'
        }, 500
