"""
Quick demo script for PrivacyLens.
Run: python demo.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.detector import PrivacyLens
from src.redactor import RedactionStrategy
from src.utils import pretty_print_entities


def main():
    print("=" * 70)
    print("  PrivacyLens — Sensitive Information Detection Demo")
    print("=" * 70)

    detector = PrivacyLens(use_spacy=True)

    samples = [
        "Hi, I am Rahul Sharma. Email: rahul.s@gmail.com, Phone: +91-98765-43210. "
        "Aadhaar: 1234-5678-9012, PAN: ABCDE1234F. Card: 4532014879321142.",
        "The meeting notes contain no personal data.",
        "Patient Priya (DOB 15/08/1990) contacted from 192.168.0.12.",
    ]

    for i, text in enumerate(samples, 1):
        print(f"\n--- Sample {i} ---")
        print(f"Input : {text[:80]}{'...' if len(text) > 80 else ''}")

        result = detector.analyze(text, redact=True, strategy=RedactionStrategy.LABEL)

        print(f"Risk  : {result.risk_level.upper()} ({result.risk_score})")
        print(f"Summary: {result.summary}")
        print("\nEntities:")
        pretty_print_entities([e.to_dict() for e in result.entities])
        print(f"\nRedacted: {result.redacted_text}")

    print("\n" + "=" * 70)
    print("Demo complete. Try the Streamlit UI: streamlit run app/streamlit_app.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
