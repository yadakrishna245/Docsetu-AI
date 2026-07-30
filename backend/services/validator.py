"""
DocSetu AI - Indian Document Validator
Validates Indian document numbers using regex, checksums, and algorithms.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class IndianDocumentValidator:
    """Validates Indian government and financial document numbers."""

    # Verhoeff algorithm tables for Aadhaar validation
    _VERHOEFF_TABLE_D = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
    ]

    _VERHOEFF_TABLE_P = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
        [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
        [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
        [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
    ]

    _VERHOEFF_TABLE_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

    @classmethod
    def _verhoeff_checksum(cls, number: str) -> int:
        """Calculate Verhoeff checksum for a number string."""
        c = 0
        number_reversed = number[::-1]
        for i, digit in enumerate(number_reversed):
            c = cls._VERHOEFF_TABLE_D[c][cls._VERHOEFF_TABLE_P[i % 8][int(digit)]]
        return c

    @classmethod
    def validate_aadhaar(cls, aadhaar: str) -> Tuple[bool, str]:
        """
        Validate an Aadhaar number using the Verhoeff algorithm.

        Args:
            aadhaar: 12-digit Aadhaar number (with or without spaces).

        Returns:
            Tuple of (is_valid, message).
        """
        # Remove spaces and hyphens
        clean = re.sub(r'[\s\-]', '', aadhaar)

        # Basic format check
        if not re.match(r'^[2-9]\d{11}$', clean):
            return False, "Invalid format: Aadhaar must be 12 digits starting with 2-9"

        # Verhoeff checksum validation
        if cls._verhoeff_checksum(clean) != 0:
            return False, "Invalid checksum: Aadhaar number fails Verhoeff validation"

        return True, "Valid Aadhaar number"

    @classmethod
    def validate_pan(cls, pan: str) -> Tuple[bool, str]:
        """
        Validate a PAN (Permanent Account Number).

        Format: ABCDE1234F
        - First 3: Alpha (Area code)
        - 4th: Entity type (C=Company, P=Person, H=HUF, F=Firm, A=AOP, T=Trust, etc.)
        - 5th: First letter of surname/name
        - 6-9: Sequential digits (0001-9999)
        - 10th: Alphabetic check digit

        Args:
            pan: 10-character PAN string.

        Returns:
            Tuple of (is_valid, message).
        """
        pan = pan.upper().strip()

        if len(pan) != 10:
            return False, "Invalid length: PAN must be exactly 10 characters"

        # Format validation
        pattern = r'^[A-Z]{3}[ABCFGHLJPTK][A-Z]\d{4}[A-Z]$'
        if not re.match(pattern, pan):
            return False, "Invalid format: PAN must match XXXXX0000X pattern with valid entity type"

        # Entity type validation
        entity_types = {
            'A': 'Association of Persons (AOP)',
            'B': 'Body of Individuals (BOI)',
            'C': 'Company',
            'F': 'Firm',
            'G': 'Government',
            'H': 'Hindu Undivided Family (HUF)',
            'J': 'Artificial Juridical Person',
            'L': 'Local Authority',
            'P': 'Individual/Person',
            'T': 'Trust',
            'K': 'Krishi (Agriculture)',
        }

        entity_char = pan[3]
        if entity_char not in entity_types:
            return False, f"Invalid entity type character: {entity_char}"

        return True, f"Valid PAN ({entity_types[entity_char]})"

    @classmethod
    def validate_gstin(cls, gstin: str) -> Tuple[bool, str]:
        """
        Validate a GSTIN (Goods and Services Tax Identification Number).

        Format: 22AAAAA0000A1Z5
        - Positions 1-2: State code (01-37)
        - Positions 3-12: PAN of the entity
        - Position 13: Entity number
        - Position 14: 'Z' by default
        - Position 15: Check digit

        Args:
            gstin: 15-character GSTIN string.

        Returns:
            Tuple of (is_valid, message).
        """
        gstin = gstin.upper().strip()

        if len(gstin) != 15:
            return False, "Invalid length: GSTIN must be exactly 15 characters"

        # Format check
        pattern = r'^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$'
        if not re.match(pattern, gstin):
            return False, "Invalid format: GSTIN must match state code + PAN + entity + Z + check"

        # State code validation (01-37, plus some special codes)
        valid_state_codes = [
            '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
            '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
            '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
            '31', '32', '33', '34', '35', '36', '37', '38', '97',
        ]
        state_code = gstin[:2]
        if state_code not in valid_state_codes:
            return False, f"Invalid state code: {state_code}"

        # Validate embedded PAN
        embedded_pan = gstin[2:12]
        pan_valid, pan_msg = cls.validate_pan(embedded_pan)
        if not pan_valid:
            return False, f"Invalid embedded PAN in GSTIN: {pan_msg}"

        # Check digit validation using mod 36 algorithm
        factor = 1
        total = 0
        code_point_table = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for i in range(len(gstin) - 1):
            digit = code_point_table.index(gstin[i])
            digit = (digit * factor) % 36
            digit = (digit // 36) + (digit % 36)
            total += digit
            factor = 2 if factor == 1 else 1

        remainder = total % 36
        check_char = code_point_table[(36 - remainder) % 36]

        if check_char != gstin[14]:
            return False, f"Invalid check digit: expected {check_char}, got {gstin[14]}"

        return True, "Valid GSTIN"

    @classmethod
    def validate_ifsc(cls, ifsc: str) -> Tuple[bool, str]:
        """
        Validate an IFSC (Indian Financial System Code).

        Format: ABCD0123456
        - First 4: Bank code (alphabetic)
        - 5th: Always '0' (reserved)
        - Last 6: Branch code (alphanumeric)

        Args:
            ifsc: 11-character IFSC code.

        Returns:
            Tuple of (is_valid, message).
        """
        ifsc = ifsc.upper().strip()

        if len(ifsc) != 11:
            return False, "Invalid length: IFSC must be exactly 11 characters"

        pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
        if not re.match(pattern, ifsc):
            return False, "Invalid format: IFSC must be 4 letters + 0 + 6 alphanumeric"

        # Known major bank codes for basic validation
        known_banks = [
            'SBIN', 'HDFC', 'ICIC', 'UTIB', 'PUNB', 'BARB', 'CNRB',
            'UBIN', 'IOBA', 'BKID', 'ALLA', 'CORP', 'IDIB', 'MAHB',
            'KKBK', 'YESB', 'INDB', 'FDRL', 'CITI', 'HSBC', 'SCBL',
        ]
        bank_code = ifsc[:4]
        # Not enforcing known banks - just format validation
        logger.debug(f"IFSC bank code: {bank_code}")

        return True, f"Valid IFSC code (Bank: {bank_code})"

    @classmethod
    def validate_mobile(cls, mobile: str) -> Tuple[bool, str]:
        """
        Validate an Indian mobile number.

        Valid formats:
        - 9876543210
        - +919876543210
        - +91-9876543210
        - 09876543210

        Args:
            mobile: Indian mobile number string.

        Returns:
            Tuple of (is_valid, message).
        """
        # Remove common prefixes and formatting
        clean = re.sub(r'[\s\-\(\)]', '', mobile)
        clean = re.sub(r'^(\+91|91|0)', '', clean)

        if not re.match(r'^[6-9]\d{9}$', clean):
            return False, "Invalid: Indian mobile must be 10 digits starting with 6-9"

        return True, "Valid Indian mobile number"

    @classmethod
    def validate_pincode(cls, pincode: str) -> Tuple[bool, str]:
        """
        Validate an Indian PIN code.

        Format: 6 digits, first digit 1-9.

        Args:
            pincode: 6-digit PIN code string.

        Returns:
            Tuple of (is_valid, message).
        """
        clean = pincode.strip()

        if not re.match(r'^[1-9]\d{5}$', clean):
            return False, "Invalid: PIN code must be 6 digits starting with 1-9"

        # Region mapping based on first digit
        regions = {
            '1': 'Delhi, Haryana, HP, J&K, Punjab, Chandigarh',
            '2': 'UP, Uttarakhand',
            '3': 'Rajasthan, Gujarat, Daman & Diu, Dadra & Nagar Haveli',
            '4': 'Maharashtra, Goa, Madhya Pradesh, Chhattisgarh',
            '5': 'Andhra Pradesh, Telangana, Karnataka',
            '6': 'Tamil Nadu, Kerala, Puducherry, Lakshadweep',
            '7': 'West Bengal, Odisha, Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura',
            '8': 'Bihar, Jharkhand',
            '9': 'Army Post Office (APO)',
        }

        region = regions.get(clean[0], 'Unknown')
        return True, f"Valid PIN code (Region: {region})"

    @classmethod
    def validate_cin(cls, cin: str) -> Tuple[bool, str]:
        """
        Validate a CIN (Corporate Identification Number).

        Format: U12345MH2000PTC123456
        - Position 1: Listing status (U=Unlisted, L=Listed)
        - Position 2-6: Industry code (5 digits)
        - Position 7-8: State code (2 letters)
        - Position 9-12: Year of incorporation
        - Position 13-15: Company type (PTC, PLC, etc.)
        - Position 16-21: Registration number (6 digits)

        Args:
            cin: 21-character CIN string.

        Returns:
            Tuple of (is_valid, message).
        """
        cin = cin.upper().strip()

        if len(cin) != 21:
            return False, "Invalid length: CIN must be exactly 21 characters"

        pattern = r'^[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$'
        if not re.match(pattern, cin):
            return False, "Invalid format: CIN must match [U/L]+5digits+2letters+4digits+3letters+6digits"

        listing_status = "Listed" if cin[0] == 'L' else "Unlisted"
        year = cin[8:12]

        return True, f"Valid CIN ({listing_status}, incorporated {year})"
