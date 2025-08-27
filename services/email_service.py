import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from config.email_config import EmailConfig

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        self.api_key = EmailConfig.SENDGRID_API_KEY
        self.from_email = EmailConfig.SENDGRID_FROM_EMAIL
        self.from_name = EmailConfig.SENDGRID_FROM_NAME
        
        if not self.api_key:
            logger.warning("SendGrid API key not configured. Email functionality will be disabled.")
            self.client = None
        else:
            self.client = SendGridAPIClient(api_key=self.api_key)
    
    def send_password_reset_email(self, to_email, reset_token, username=None):
        """Send password reset email"""
        if not self.client:
            logger.error("Cannot send email: SendGrid not configured")
            return False
        
        try:
            reset_link = EmailConfig.get_reset_link(reset_token)
            
            # Email content
            subject = EmailConfig.PASSWORD_RESET_SUBJECT
            html_content = self._get_password_reset_html(reset_link, username)
            text_content = self._get_password_reset_text(reset_link, username)
            
            # Create email
            from_email = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email)
            
            # Send HTML email
            mail = Mail(from_email, subject, to_email_obj, HtmlContent(html_content))
            
            # Send email
            response = self.client.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Password reset email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False
    
    def _get_password_reset_html(self, reset_link, username):
        """Generate HTML content for password reset email"""
        username_display = username or "there"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #059669; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #059669; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }}
                .warning {{ background-color: #fef3c7; border: 1px solid #f59e0b; padding: 15px; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">Ki Wellness</div>
                </div>
                
                <h2>Hello {username_display},</h2>
                
                <p>We received a request to reset your password for your Ki Wellness account.</p>
                
                <p>Click the button below to reset your password:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </div>
                
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #059669;">{reset_link}</p>
                
                <div class="warning">
                    <strong>Important:</strong> This link will expire in 24 hours for security reasons.
                </div>
                
                <p>If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                
                <p>Best regards,<br>The Ki Wellness Team</p>
                
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>If you need assistance, please contact our support team.</p>
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
