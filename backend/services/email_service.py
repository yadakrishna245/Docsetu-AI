"""
DocSetu AI - Email Service
Async email sending for verification and password reset flows.
Uses aiosmtplib for non-blocking SMTP operations.
"""

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_verification_html(token: str, base_url: str) -> str:
    """Build HTML email body for email verification."""
    verify_url = f"{base_url}/verify-email?token={token}"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .header {{ background: #1a73e8; padding: 30px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .body {{ padding: 40px 30px; }}
            .body p {{ color: #333; line-height: 1.6; font-size: 16px; }}
            .btn {{ display: inline-block; background: #1a73e8; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-size: 16px; font-weight: 600; margin: 20px 0; }}
            .footer {{ padding: 20px 30px; text-align: center; color: #888; font-size: 12px; border-top: 1px solid #eee; }}
            .code {{ background: #f0f4f8; padding: 12px 20px; border-radius: 4px; font-family: monospace; font-size: 14px; word-break: break-all; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>DocSetu AI</h1>
            </div>
            <div class="body">
                <p>Welcome to DocSetu AI! Please verify your email address to activate your account.</p>
                <p style="text-align: center;">
                    <a href="{verify_url}" class="btn">Verify Email Address</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p class="code">{verify_url}</p>
                <p>If you didn't create an account with DocSetu AI, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 DocSetu AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


def _build_password_reset_html(token: str, base_url: str) -> str:
    """Build HTML email body for password reset."""
    reset_url = f"{base_url}/reset-password?token={token}"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .header {{ background: #d93025; padding: 30px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .body {{ padding: 40px 30px; }}
            .body p {{ color: #333; line-height: 1.6; font-size: 16px; }}
            .btn {{ display: inline-block; background: #d93025; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-size: 16px; font-weight: 600; margin: 20px 0; }}
            .footer {{ padding: 20px 30px; text-align: center; color: #888; font-size: 12px; border-top: 1px solid #eee; }}
            .code {{ background: #f0f4f8; padding: 12px 20px; border-radius: 4px; font-family: monospace; font-size: 14px; word-break: break-all; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>DocSetu AI - Password Reset</h1>
            </div>
            <div class="body">
                <p>We received a request to reset your password. Click the button below to choose a new password.</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="btn">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p class="code">{reset_url}</p>
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 DocSetu AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


async def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an email via SMTP. Falls back to logging if SMTP is not configured.

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        html_body: HTML content of the email.

    Returns:
        True if sent (or logged) successfully, False on failure.
    """
    # Check if SMTP is configured
    if not settings.smtp_host or not settings.smtp_username:
        logger.info(
            f"[DEV MODE] SMTP not configured. Email would be sent to: {to_email}\n"
            f"Subject: {subject}\n"
            f"Body (first 200 chars): {html_body[:200]}..."
        )
        return True

    try:
        message = MIMEMultipart("alternative")
        message["From"] = settings.smtp_from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=True,
        )

        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_verification_email(email: str, token: str, base_url: str) -> bool:
    """
    Send email verification link to a new user.

    Args:
        email: User's email address.
        token: Verification token.
        base_url: Application base URL for building the verification link.

    Returns:
        True if email was sent successfully.
    """
    subject = "DocSetu AI - Verify Your Email Address"
    html_body = _build_verification_html(token, base_url)
    return await _send_email(email, subject, html_body)


async def send_password_reset_email(email: str, token: str, base_url: str) -> bool:
    """
    Send password reset link to a user.

    Args:
        email: User's email address.
        token: Password reset token.
        base_url: Application base URL for building the reset link.

    Returns:
        True if email was sent successfully.
    """
    subject = "DocSetu AI - Reset Your Password"
    html_body = _build_password_reset_html(token, base_url)
    return await _send_email(email, subject, html_body)
