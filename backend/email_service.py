import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """Send email using Gmail SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach plain text
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach HTML if provided
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        # Connect and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_otp_email(to_email: str, otp: str, purpose: str = "verification") -> bool:
    """Send OTP email"""
    subject = f"{settings.APP_NAME} - Verification Code"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #333;">Verification Code</h2>
                <p>Your verification code for {purpose} is:</p>
                <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                    {otp}
                </div>
                <p style="color: #666;">This code will expire in 10 minutes.</p>
                <p style="color: #666; font-size: 12px;">If you didn't request this code, please ignore this email.</p>
            </div>
        </body>
    </html>
    """
    
    body = f"Your verification code is: {otp}\n\nThis code will expire in 10 minutes."
    
    return await send_email(to_email, subject, body, html_body)


async def send_welcome_email(to_email: str, name: str) -> bool:
    """Send welcome email after registration"""
    subject = f"Welcome to {settings.APP_NAME}!"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #333;">Welcome to {settings.APP_NAME}!</h2>
                <p>Hi {name},</p>
                <p>Thank you for signing up! We're excited to have you on board.</p>
                <p>You can now start verifying emails and cleaning your email lists.</p>
                <a href="{settings.APP_URL}/dashboard" style="display: inline-block; background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Go to Dashboard</a>
                <p style="color: #666; font-size: 12px;">If you have any questions, feel free to reach out to our support team.</p>
            </div>
        </body>
    </html>
    """
    
    body = f"Welcome to {settings.APP_NAME}!\n\nHi {name},\n\nThank you for signing up!"
    
    return await send_email(to_email, subject, body, html_body)


async def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """Send password reset email"""
    reset_url = f"{settings.APP_URL}/reset-password?token={reset_token}"
    subject = f"{settings.APP_NAME} - Password Reset"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #333;">Password Reset Request</h2>
                <p>We received a request to reset your password.</p>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_url}" style="display: inline-block; background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Reset Password</a>
                <p style="color: #666;">This link will expire in 1 hour.</p>
                <p style="color: #666; font-size: 12px;">If you didn't request this, please ignore this email.</p>
            </div>
        </body>
    </html>
    """
    
    body = f"Reset your password: {reset_url}\n\nThis link will expire in 1 hour."
    
    return await send_email(to_email, subject, body, html_body)
