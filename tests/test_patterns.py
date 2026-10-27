"""
Unit tests for regex patterns.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.patterns import PATTERNS


def test_email():
    text = "Contact me at john.doe@example.com for details."
    matches = list(PATTERNS["EMAIL"].finditer(text))
    assert len(matches) == 1
    assert matches[0].group() == "john.doe@example.com"


def test_aadhaar():
    text = "My Aadhaar is 1234-5678-9012 and another is 987654321098"
    matches = list(PATTERNS["AADHAAR"].finditer(text))
    assert len(matches) >= 1


def test_pan():
    text = "PAN number is ABCDE1234F"
    matches = list(PATTERNS["PAN"].finditer(text))
    assert len(matches) == 1
    assert matches[0].group() == "ABCDE1234F"


def test_phone_indian():
    text = "Call +91-98765-43210 or 09876543210"
    matches = list(PATTERNS["PHONE"].finditer(text))
    assert len(matches) >= 1


def test_ip():
    text = "Server IP: 192.168.1.1 and public 8.8.8.8"
    matches = list(PATTERNS["IP_ADDRESS"].finditer(text))
    assert len(matches) == 2


def test_no_false_positive_short_number():
    text = "The code is 1234"
    matches = list(PATTERNS["AADHAAR"].finditer(text))
    assert len(matches) == 0
