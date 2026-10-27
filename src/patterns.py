"""
Regex patterns for structured sensitive information.
Optimized for Indian identifiers + common global formats.
"""

from typing import Dict, List, Pattern
import re

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

PATTERNS: Dict[str, Pattern] = {
    # Email
    "EMAIL": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        re.IGNORECASE
    ),

    # Phone numbers (Indian + International)
    # Supports: +91 98765 43210, 09876543210, 98765-43210, (022) 1234 5678
    "PHONE": re.compile(
        r"""
        (?:
            (?:\+91[\-\s]?)?                # optional +91
            (?:0)?                          # optional leading 0
            (?:
                [6-9]\d{9}                  # 10-digit mobile
                |
                \d{2,4}[\-\s]?\d{6,8}       # landline
            )
        )
        """,
        re.VERBOSE
    ),

    # Aadhaar (12 digits, often spaced as XXXX-XXXX-XXXX)
    "AADHAAR": re.compile(
        r"\b(?:\d{4}[-\s]?){2}\d{4}\b"
    ),

    # PAN Card (AAAAA9999A)
    "PAN": re.compile(
        r"\b[A-Z]{5}\d{4}[A-Z]\b"
    ),

    # Passport (Indian format roughly: 1 letter + 7 digits)
    "PASSPORT": re.compile(
        r"\b[A-Z][0-9]{7}\b"
    ),

    # Credit / Debit Card (13-19 digits, with optional spaces/dashes)
    "CREDIT_CARD": re.compile(
        r"\b(?:\d[ -]*?){13,19}\b"
    ),

    # IFSC Code
    "IFSC": re.compile(
        r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
    ),

    # UPI ID
    "UPI": re.compile(
        r"\b[\w.\-]+@[\w]+\b"
    ),

    # IP Address (IPv4)
    "IP_ADDRESS": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    ),

    # MAC Address
    "MAC_ADDRESS": re.compile(
        r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"
    ),

    # Date of Birth patterns (common Indian formats)
    "DATE_OF_BIRTH": re.compile(
        r"\b(?:(?:0?[1-9]|[12][0-9]|3[01])[\/\-.](?:0?[1-9]|1[0-2])[\/\-.](?:19|20)\d{2})\b"
    ),

    # Driving License (very loose — state codes vary)
    "DRIVING_LICENSE": re.compile(
        r"\b[A-Z]{2}[-\s]?\d{2}[-\s]?\d{4}[-\s]?\d{7}\b"
    ),

    # Employee / Staff ID (common patterns)
    "EMPLOYEE_ID": re.compile(
        r"\b(?:EMP|STAFF|ID)[-_]?\d{4,8}\b",
        re.IGNORECASE
    ),
}


# Entity type metadata (for UI + risk scoring)
ENTITY_META = {
    "EMAIL": {"category": "Personal", "risk": "medium", "description": "Email address"},
    "PHONE": {"category": "Personal", "risk": "high", "description": "Phone number"},
    "AADHAAR": {"category": "Government ID", "risk": "critical", "description": "Aadhaar number"},
    "PAN": {"category": "Government ID", "risk": "critical", "description": "PAN card"},
    "PASSPORT": {"category": "Government ID", "risk": "critical", "description": "Passport number"},
    "CREDIT_CARD": {"category": "Financial", "risk": "critical", "description": "Credit/Debit card"},
    "IFSC": {"category": "Financial", "risk": "high", "description": "Bank IFSC code"},
    "UPI": {"category": "Financial", "risk": "high", "description": "UPI ID"},
    "IP_ADDRESS": {"category": "Technical", "risk": "medium", "description": "IP address"},
    "MAC_ADDRESS": {"category": "Technical", "risk": "low", "description": "MAC address"},
    "DATE_OF_BIRTH": {"category": "Personal", "risk": "high", "description": "Date of birth"},
    "DRIVING_LICENSE": {"category": "Government ID", "risk": "high", "description": "Driving license"},
    "EMPLOYEE_ID": {"category": "Organizational", "risk": "medium", "description": "Employee ID"},
    "PERSON": {"category": "Personal", "risk": "medium", "description": "Person name"},
    "ORG": {"category": "Organizational", "risk": "low", "description": "Organization"},
    "GPE": {"category": "Location", "risk": "low", "description": "Geo-political entity"},
    "LOC": {"category": "Location", "risk": "low", "description": "Location"},
}


def get_pattern(entity_type: str) -> Pattern | None:
    return PATTERNS.get(entity_type.upper())


def list_supported_entities() -> List[str]:
    return list(PATTERNS.keys()) + ["PERSON", "ORG", "GPE", "LOC"]
