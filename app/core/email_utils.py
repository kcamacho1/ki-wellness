from postmarker.core import PostmarkClient
import os

postmark = PostmarkClient(server_token=os.getenv("POSTMARK_API_TOKEN"))

def send_password_reset(to_email: str, reset_link: str):
    return postmark.emails.send(
        From=os.getenv("POSTMARK_SENDER"),
        To=to_email,
        Subject="Ki Wellness Password Reset",
        HtmlBody=f"""
        <p>Hello,</p>
        <p>You requested a password reset. Click the link below to reset your password:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>If you didn't request this, you can ignore this email.</p>
        """,
        TextBody=f"Click here to reset your password: {reset_link}",
        MessageStream="outbound"
    )
