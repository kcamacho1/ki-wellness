"""
Static page routes - Privacy, Terms, Disclaimer, etc.
These are simple content pages that don't require authentication
"""
from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app, request, flash
from flask_login import current_user, login_required
from sqlalchemy import text
from database import db
from services.email_service import EmailService
from werkzeug.utils import secure_filename
import os
import uuid

# Create blueprint
static_bp = Blueprint('static_pages', __name__)


@static_bp.route('/')
def index():
    """Homepage - redirect to dashboard if logged in, otherwise show landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('pages/static/landing.html')


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


@static_bp.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    """Support page with documentation links and ticket submission form"""
    if request.method == 'POST':
        return handle_support_ticket()
    
    return render_template('support.html')


def handle_support_ticket():
    """Handle support ticket submission"""
    try:
        # Get form data
        ticket_type = request.form.get('ticket_type')
        subject = request.form.get('subject', '').strip()
        description = request.form.get('description', '').strip()
        user_email = request.form.get('email', '').strip()
        
        # Validate required fields
        if not all([ticket_type, subject, description, user_email]):
            flash('All fields are required.', 'error')
            return render_template('support.html')
        
        if ticket_type not in ['Bug', 'Suggestion']:
            flash('Invalid ticket type selected.', 'error')
            return render_template('support.html')
        
        # Create subject line from first 5 words
        subject_words = subject.split()[:5]
        email_subject = f"[{ticket_type}] {' '.join(subject_words)}"
        
        # Handle file upload if present
        screenshot_info = ""
        if 'screenshot' in request.files:
            screenshot = request.files['screenshot']
            if screenshot and screenshot.filename:
                if allowed_file(screenshot.filename):
                    filename = secure_filename(screenshot.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # Create upload directory if it doesn't exist
                    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'support')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    screenshot_path = os.path.join(upload_dir, unique_filename)
                    screenshot.save(screenshot_path)
                    screenshot_info = f"\n\nScreenshot attached: {unique_filename}"
                else:
                    flash('Invalid file type. Please upload PNG, JPG, or GIF files only.', 'error')
                    return render_template('support.html')
        
        # Compose email content
        email_body = f"""
        Support Ticket Submission
        
        Type: {ticket_type}
        Subject: {subject}
        User Email: {user_email}
        User: {current_user.name or current_user.username} (ID: {current_user.id})
        
        Description:
        {description}
        {screenshot_info}
        
        ---
        Submitted from Ki Wellness Support Form
        """
        
        # Send email using EmailService
        email_service = EmailService()
        success = send_support_email(email_service, email_subject, email_body, user_email)
        
        if success:
            flash('Support ticket submitted successfully! We\'ll get back to you soon.', 'success')
        else:
            flash('There was an error submitting your ticket. Please try again later.', 'error')
        
        return redirect(url_for('static_pages.support'))
        
    except Exception as e:
        current_app.logger.error(f"Error handling support ticket: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return render_template('support.html')


def send_support_email(email_service, subject, body, user_email):
    """Send support ticket email"""
    try:
        # Create HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
        </head>
        <body style="font-family: 'Quicksand', Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background: white;">
                <div style="text-align: center; margin-bottom: 30px; background: #059669; color: white; padding: 20px; border-radius: 8px;">
                    <h1 style="margin: 0; font-size: 24px;">🌿 Ki Wellness Support</h1>
                    <p style="margin: 5px 0 0 0;">Support Ticket Submission</p>
                </div>
                
                <div style="background: #e0f2fe; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #059669;">
                    <p style="margin: 0 0 10px 0; font-weight: bold; color: #059669;">From: {user_email}</p>
                    <p style="margin: 0 0 10px 0; font-weight: bold; color: #059669;">Subject: {subject}</p>
                </div>
                
                <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; color: #333;">Message:</h3>
                    <pre style="white-space: pre-wrap; font-family: Arial, sans-serif; margin: 0;">{body}</pre>
                </div>
                
                <div style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
                    <p>This email was automatically generated from the Ki Wellness support form.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send from support@kiwellness.org to support@kiwellness.org with user CC
        # Use the support email specific method with explicit from address
        return send_support_email_with_fallback(
            email_service=email_service,
            to_email="support@kiwellness.org",
            from_email="support@kiwellness.org", 
            subject=subject,
            html_content=html_content,
            cc_email=user_email
        )
        
    except Exception as e:
        current_app.logger.error(f"Error sending support email: {str(e)}")
        return False


def send_support_email_with_fallback(email_service, to_email, from_email, subject, html_content, cc_email=None):
    """Send support email with explicit from address override"""
    try:
        # Temporarily override the email service's from_email for this specific call
        original_from_email = email_service.from_email
        original_from_name = email_service.from_name
        
        # Set support-specific from address
        email_service.from_email = from_email
        email_service.from_name = "Ki Wellness Support"
        
        # Send the email
        result = email_service._send_sendgrid_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            cc_email=cc_email
        )
        
        # Restore original settings
        email_service.from_email = original_from_email
        email_service.from_name = original_from_name
        
        return result
        
    except Exception as e:
        current_app.logger.error(f"Error in send_support_email_with_fallback: {str(e)}")
        # Restore original settings in case of error
        try:
            email_service.from_email = original_from_email
            email_service.from_name = original_from_name
        except:
            pass
        return False


def allowed_file(filename):
    """Check if file extension is allowed for screenshots"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


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
