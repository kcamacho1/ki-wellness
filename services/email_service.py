import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from config.email_config import EmailConfig
import os

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        self.api_key = EmailConfig.SENDGRID_API_KEY
        self.from_email = EmailConfig.FROM_EMAIL
        self.from_name = EmailConfig.FROM_NAME
        
        if self.api_key:
            self.sendgrid_client = SendGridAPIClient(api_key=self.api_key)
            logger.info("Email service initialized with SendGrid")
        else:
            logger.warning("SendGrid API key not configured. Email functionality will be disabled.")
            self.sendgrid_client = None
    
    def send_password_reset_email(self, to_email, reset_token, username=None):
        """Send password reset email"""
        if not self.sendgrid_client:
            logger.error("Cannot send email: SendGrid not configured")
            return False
        
        try:
            reset_link = EmailConfig.get_reset_link(reset_token)
            subject = EmailConfig.PASSWORD_RESET_SUBJECT
            html_content = self._get_password_reset_html(reset_link, username)
            
            return self._send_sendgrid_email(to_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False
    
    def _send_sendgrid_email(self, to_email, subject, html_content):
        """Send email via SendGrid"""
        try:
            from_email = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email)
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                html_content=html_content
            )
            
            response = self.sendgrid_client.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Password reset email sent successfully via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email via SendGrid. Status: {response.status_code}, Body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send SendGrid email: {str(e)}")
            return False
    
    def _get_password_reset_html(self, reset_link, username):
        """Generate beautiful HTML content for password reset email using template"""
        username_display = username or "there"
        
        try:
            # Get the template file path
            template_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'templates', 'emails', 'password_reset.html'
            )
            
            # Read the template file
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Replace template variables
            html_content = template_content.replace('{{ username }}', username_display)
            html_content = html_content.replace('{{ reset_link }}', reset_link)
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error loading email template: {e}")
            # Fallback to simple HTML if template fails
            return self._get_fallback_html(reset_link, username_display)
    
    def _get_fallback_html(self, reset_link, username):
        """Fallback HTML email if template fails"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: 'Quicksand', sans-serif; line-height: 1.6; color: #333; background: #f0fdf4; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background: white; border-radius: 12px; }}
                .header {{ text-align: center; margin-bottom: 30px; background: #059669; color: white; padding: 30px; border-radius: 8px; }}
                .logo {{ font-size: 28px; font-weight: bold; }}
                .button {{ display: inline-block; padding: 15px 30px; background-color: #059669; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: 600; }}
                .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🌿 Ki Wellness</div>
                    <p>Self Health Simplified</p>
                </div>
                
                <h2>Hello {username}!</h2>
                <p>We received a request to reset your password for your Ki Wellness account.</p>
                <p>Click the button below to reset your password:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </div>
                
                <p>If the button doesn't work, copy this link: <br><code>{reset_link}</code></p>
                <p><strong>This link expires in 24 hours.</strong></p>
                
                <div class="footer">
                    <p>Ki Wellness Team<br>© 2024 Ki Wellness. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_password_reset_text(self, reset_link, username):
        """Generate plain text content for password reset email"""
        username_display = username or "there"
        
        return f"""
        Hello {username_display},

        We received a request to reset your password for your Ki Wellness account.

        To reset your password, visit this link:
        {reset_link}

        This link will expire in 24 hours for security reasons.

        If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.

        Best regards,
        The Ki Wellness Team

        ---
        This is an automated message. Please do not reply to this email.
        If you need assistance, please contact our support team.
        """
