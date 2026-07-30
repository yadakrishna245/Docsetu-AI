"""
DocSetu AI - MFA Service
TOTP-based Multi-Factor Authentication using pyotp.
"""

import pyotp
import qrcode
import io
import base64


class MFAService:
    """Service for TOTP-based MFA operations."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a new random base32 secret for TOTP."""
        return pyotp.random_base32()

    @staticmethod
    def get_totp_uri(secret: str, email: str) -> str:
        """
        Generate a TOTP provisioning URI for authenticator apps.

        Args:
            secret: Base32-encoded TOTP secret.
            email: User's email address (used as account name).

        Returns:
            otpauth:// URI string.
        """
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email, issuer_name='DocSetu AI'
        )

    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """
        Generate a QR code image from a TOTP URI.

        Args:
            uri: otpauth:// URI to encode.

        Returns:
            Base64-encoded PNG image string.
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()

    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """
        Verify a TOTP token against the secret.

        Args:
            secret: Base32-encoded TOTP secret.
            token: 6-digit TOTP code from authenticator app.

        Returns:
            True if the token is valid (within ±1 time window).
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
