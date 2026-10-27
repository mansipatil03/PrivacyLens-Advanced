"""
Unit tests for PrivacyLens detector.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.detector import PrivacyLens
from src.redactor import RedactionStrategy


def test_empty_text():
    detector = PrivacyLens(use_spacy=False)
    result = detector.analyze("")
    assert result.entity_count == 0
    assert result.risk_score == 0.0


def test_aadhaar_detection():
    detector = PrivacyLens(use_spacy=False)
    text = "User Aadhaar: 1234-5678-9012"
    result = detector.analyze(text)
    types = [e.entity_type for e in result.entities]
    assert "AADHAAR" in types


def test_pan_detection():
    detector = PrivacyLens(use_spacy=False)
    text = "PAN is ABCDE1234F"
    result = detector.analyze(text)
    assert any(e.entity_type == "PAN" for e in result.entities)


def test_email_and_phone():
    detector = PrivacyLens(use_spacy=False)
    text = "Reach me at test@example.com or 9876543210"
    result = detector.analyze(text)
    types = {e.entity_type for e in result.entities}
    assert "EMAIL" in types
    assert "PHONE" in types


def test_redaction_mask():
    detector = PrivacyLens(use_spacy=False)
    text = "Email: secret@company.com"
    redacted = detector.redact(text, strategy=RedactionStrategy.MASK)
    assert "secret@company.com" not in redacted
    assert "*" in redacted


def test_redaction_label():
    detector = PrivacyLens(use_spacy=False)
    text = "PAN ABCDE1234F"
    redacted = detector.redact(text, strategy=RedactionStrategy.LABEL)
    assert "[PAN]" in redacted


def test_risk_score_increases_with_critical():
    detector = PrivacyLens(use_spacy=False)
    clean = detector.analyze("Hello world")
    sensitive = detector.analyze("Aadhaar 1234-5678-9012 and PAN ABCDE1234F")
    assert sensitive.risk_score > clean.risk_score
    assert sensitive.risk_level in ("high", "critical")
