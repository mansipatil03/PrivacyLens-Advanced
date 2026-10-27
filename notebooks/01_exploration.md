# PrivacyLens — Exploration Notes

This notebook-style document records key experiments and design choices.

## Goals
- High precision on structured Indian identifiers (Aadhaar, PAN, etc.)
- Reasonable recall on free-form PII (names, phones, emails)
- Transparent risk scoring suitable for compliance review

## Approach Comparison

| Method | Strengths | Weaknesses |
|--------|-----------|------------|
| Pure Regex | Extremely high precision on fixed formats | Misses names and context |
| spaCy NER only | Good on PERSON/ORG | Weak on Aadhaar/PAN/cards |
| **Hybrid (chosen)** | Best of both | Slightly more complex pipeline |

## False Positive Mitigations
- Luhn check for credit cards
- Length + format validation for Aadhaar / PAN
- Minimum length filters for PERSON entities
- Confidence threshold (default 0.5)

## Next Experiments
1. Evaluate `en_core_web_trf` vs `en_core_web_sm` on a labeled set
2. Add a small fine-tuned token classifier for domain-specific terms
3. Measure latency on batch of 1k documents
