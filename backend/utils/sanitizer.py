"""
DocSetu AI - Input Sanitization Utilities
OWASP-compliant input validation and sanitization.
Prevents XSS, SQL injection, path traversal, and other injection attacks.
"""

import re
import html
from typing import Optional


class InputSanitizer:
    # XSS prevention
    @staticmethod
    def sanitize_string(value: str, max_length: int = 500) -> str:
        if not value:
            return value
        # Strip HTML tags
        value = re.sub(r'<[^>]+>', '', value)
        # HTML-encode special chars
        value = html.escape(value, quote=True)
        # Trim length
        return value[:max_length].strip()

    # SQL injection prevention (for any raw queries - though SQLAlchemy parameterizes)
    @staticmethod
    def sanitize_identifier(value: str) -> str:
        # Only allow alphanumeric, underscore, hyphen
        return re.sub(r'[^a-zA-Z0-9_\-]', '', value)

    # Path traversal prevention
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        # Remove path separators and null bytes
        filename = filename.replace('/', '').replace('\\', '').replace('\x00', '')
        # Remove leading dots (hidden files)
        filename = filename.lstrip('.')
        # Only allow safe chars
        filename = re.sub(r'[^a-zA-Z0-9._\-]', '_', filename)
        return filename[:255]

    # Email validation (strict)
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254

    # Password strength
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        if len(password) < 8:
            return False, 'Password must be at least 8 characters'
        if len(password) > 128:
            return False, 'Password too long (max 128 characters)'
        if not re.search(r'[A-Z]', password):
            return False, 'Password must contain at least one uppercase letter'
        if not re.search(r'[a-z]', password):
            return False, 'Password must contain at least one lowercase letter'
        if not re.search(r'[0-9]', password):
            return False, 'Password must contain at least one digit'
        return True, 'Password meets requirements'

    # Prevent NoSQL/JSON injection in free-text fields
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        # Remove $ operators (MongoDB-style injection)
        query = re.sub(r'\$[a-zA-Z]+', '', query)
        # Remove common SQL keywords in suspicious context
        dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', '--', ';', 'UNION', 'SELECT']
        for word in dangerous:
            query = re.sub(rf'\b{word}\b', '', query, flags=re.IGNORECASE)
        return query.strip()[:1000]
