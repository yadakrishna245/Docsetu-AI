"""
DocSetu AI - Indian Document Regex Patterns
Comprehensive regex patterns for Indian government IDs, financial codes, and document elements.
"""

import re
from typing import Dict, List, Pattern

# ==================== Identity Documents ====================

# PAN (Permanent Account Number) - Format: ABCDE1234F
PAN_PATTERN: Pattern = re.compile(
    r'\b[A-Z]{3}[ABCFGHLJPTK][A-Z]\d{4}[A-Z]\b'
)

# Aadhaar Number - Format: 1234 5678 9012 (12 digits, optionally space-separated)
AADHAAR_PATTERN: Pattern = re.compile(
    r'\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b'
)

# Voter ID (EPIC) - Format: ABC1234567
VOTER_ID_PATTERN: Pattern = re.compile(
    r'\b[A-Z]{3}\d{7}\b'
)

# Passport Number - Format: A1234567 or AB1234567
PASSPORT_PATTERN: Pattern = re.compile(
    r'\b[A-Z][1-9]\d{6,7}\b'
)

# Driving License - Format varies by state (e.g., KA01 20120001234)
DRIVING_LICENSE_PATTERN: Pattern = re.compile(
    r'\b[A-Z]{2}\d{2}\s?\d{4}\s?\d{7}\b'
)

# ==================== Financial & Tax ====================

# GST Number (GSTIN) - Format: 22AAAAA0000A1Z5
GSTIN_PATTERN: Pattern = re.compile(
    r'\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b'
)

# IFSC Code - Format: ABCD0123456
IFSC_PATTERN: Pattern = re.compile(
    r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
)

# Bank Account Number - 9 to 18 digits
BANK_ACCOUNT_PATTERN: Pattern = re.compile(
    r'\b\d{9,18}\b'
)

# UPI ID - Format: username@bankname
UPI_PATTERN: Pattern = re.compile(
    r'\b[a-zA-Z0-9._-]+@[a-zA-Z]{3,}\b'
)

# CIN (Corporate Identification Number) - Format: U12345MH2000PTC123456
CIN_PATTERN: Pattern = re.compile(
    r'\b[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b'
)

# TAN (Tax Deduction Account Number) - Format: ABCD12345E
TAN_PATTERN: Pattern = re.compile(
    r'\b[A-Z]{4}\d{5}[A-Z]\b'
)

# HSN/SAC Code - 4, 6, or 8 digit codes
HSN_PATTERN: Pattern = re.compile(
    r'\bHSN\s*:?\s*(\d{4}|\d{6}|\d{8})\b'
)

SAC_PATTERN: Pattern = re.compile(
    r'\bSAC\s*:?\s*(\d{4}|\d{6})\b'
)

# ==================== Contact & Address ====================

# Indian Mobile Number - Format: +91-9876543210 or 09876543210
MOBILE_PATTERN: Pattern = re.compile(
    r'\b(?:\+91[-\s]?|0)?[6-9]\d{9}\b'
)

# Indian Landline - Format: 011-12345678
LANDLINE_PATTERN: Pattern = re.compile(
    r'\b0\d{2,4}[-\s]?\d{6,8}\b'
)

# PIN Code (Postal Index Number) - 6 digits
PINCODE_PATTERN: Pattern = re.compile(
    r'\b[1-9]\d{5}\b'
)

# Email
EMAIL_PATTERN: Pattern = re.compile(
    r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
)

# ==================== Dates & Amounts ====================

# Indian date formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
DATE_PATTERN_DMY: Pattern = re.compile(
    r'\b(0[1-9]|[12]\d|3[01])[/\-\.](0[1-9]|1[0-2])[/\-\.](\d{4}|\d{2})\b'
)

# Date in words: 15th January 2024, 15 Jan 2024
DATE_PATTERN_WORDS: Pattern = re.compile(
    r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b',
    re.IGNORECASE
)

# Indian currency amounts: ₹1,23,456.78 or Rs. 1,23,456.78 or INR 12345
AMOUNT_PATTERN: Pattern = re.compile(
    r'(?:₹|Rs\.?|INR)\s*(\d{1,2}(?:,\d{2})*(?:,\d{3})?(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)',
    re.IGNORECASE
)

# Amount in words (crore, lakh)
AMOUNT_WORDS_PATTERN: Pattern = re.compile(
    r'(?:₹|Rs\.?|INR)?\s*[\d,.]+\s*(?:crore|lakh|thousand|hundred)s?',
    re.IGNORECASE
)

# ==================== Legal & Business ====================

# Invoice Number patterns
INVOICE_PATTERN: Pattern = re.compile(
    r'(?:Invoice|Inv|Bill)\s*(?:No\.?|Number|#)\s*:?\s*([A-Z0-9\-/]+)',
    re.IGNORECASE
)

# GST Invoice number
GST_INVOICE_PATTERN: Pattern = re.compile(
    r'(?:Tax\s+)?Invoice\s*(?:No\.?|Number|#)\s*:?\s*([A-Z0-9\-/]+)',
    re.IGNORECASE
)

# Assessment Year
AY_PATTERN: Pattern = re.compile(
    r'\bA\.?Y\.?\s*:?\s*(\d{4}[-\s]?\d{2,4})\b',
    re.IGNORECASE
)

# Financial Year
FY_PATTERN: Pattern = re.compile(
    r'\bF\.?Y\.?\s*:?\s*(\d{4}[-\s]?\d{2,4})\b',
    re.IGNORECASE
)


# ==================== Utility Functions ====================

def extract_all_patterns(text: str) -> Dict[str, List[str]]:
    """
    Extract all Indian document patterns from text.

    Args:
        text: Input text to search for patterns.

    Returns:
        Dictionary with pattern names as keys and lists of found matches as values.
    """
    results: Dict[str, List[str]] = {}

    patterns = {
        "pan": PAN_PATTERN,
        "aadhaar": AADHAAR_PATTERN,
        "gstin": GSTIN_PATTERN,
        "ifsc": IFSC_PATTERN,
        "mobile": MOBILE_PATTERN,
        "email": EMAIL_PATTERN,
        "pincode": PINCODE_PATTERN,
        "cin": CIN_PATTERN,
        "tan": TAN_PATTERN,
        "voter_id": VOTER_ID_PATTERN,
        "passport": PASSPORT_PATTERN,
        "upi": UPI_PATTERN,
        "dates": DATE_PATTERN_DMY,
        "dates_words": DATE_PATTERN_WORDS,
        "amounts": AMOUNT_PATTERN,
    }

    for name, pattern in patterns.items():
        matches = pattern.findall(text)
        if matches:
            # Flatten tuples from groups
            if matches and isinstance(matches[0], tuple):
                matches = ["/".join(m) for m in matches]
            results[name] = list(set(matches))  # Deduplicate

    return results


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive Indian document numbers in text.

    Args:
        text: Input text containing sensitive data.

    Returns:
        Text with sensitive numbers masked.
    """
    # Mask Aadhaar
    text = AADHAAR_PATTERN.sub(lambda m: "XXXX XXXX " + m.group()[-4:], text)
    # Mask PAN (show first and last chars)
    text = PAN_PATTERN.sub(lambda m: m.group()[0] + "XXXXX" + m.group()[-4:], text)
    # Mask mobile
    text = MOBILE_PATTERN.sub(lambda m: "XXXXXX" + m.group()[-4:], text)

    return text
