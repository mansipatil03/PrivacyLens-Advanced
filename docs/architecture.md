# PrivacyLens Architecture

## High-Level Overview

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Input Text │────▶│  PrivacyLens Engine  │────▶│  Analysis Result│
└─────────────┘     │                      │     │  + Redacted Text│
                    │  ┌────────────────┐  │     └─────────────────┘
                    │  │ Regex Layer    │  │
                    │  │ (High Precision│  │
                    │  │  Structured IDs)│  │
                    │  └───────┬────────┘  │
                    │          │           │
                    │  ┌───────▼────────┐  │
                    │  │ spaCy NER      │  │
                    │  │ (Names, Orgs,  │  │
                    │  │  Locations)    │  │
                    │  └───────┬────────┘  │
                    │          │           │
                    │  ┌───────▼────────┐  │
                    │  │ Post-process   │  │
                    │  │ Dedup + Risk   │  │
                    │  │ Scoring        │  │
                    │  └───────┬────────┘  │
                    │          │           │
                    │  ┌───────▼────────┐  │
                    │  │ Redactor       │  │
                    │  │ (Mask/Hash/..) │  │
                    │  └────────────────┘  │
                    └──────────────────────┘
```

## Components

### 1. Pattern Layer (`patterns.py`)
- Hand-crafted regex for high-precision structured identifiers.
- Special focus on Indian identifiers (Aadhaar, PAN, IFSC, UPI, Indian phone formats).
- Luhn check for credit cards to reduce false positives.

### 2. NER Layer (spaCy)
- Uses `en_core_web_sm` (or `en_core_web_trf` for higher accuracy).
- Detects PERSON, ORG, GPE, LOC, DATE entities.
- Complements regex for free-form sensitive mentions.

### 3. Risk Engine
- Each entity type has a risk weight (critical / high / medium / low).
- Aggregates into a document-level risk score (0–1) and risk level.
- Boosts score when multiple critical identifiers co-occur.

### 4. Redactor
- Strategies: mask, hash, label, partial (last-4), remove.
- Offset-safe replacement (processes from end of text).

### 5. Serving Layer
- **FastAPI**: Production-ready REST API with OpenAPI docs.
- **Streamlit**: Interactive demo for stakeholders and interviews.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Hybrid (regex + NER) | Regex gives near-perfect precision on structured IDs; NER covers free text |
| Offline-first | No external API calls → better privacy & compliance |
| Indian ID focus | Most open-source PII tools are US/EU centric; DPDP Act relevance |
| Explainable output | Confidence + source + risk help auditors and developers |
| Simple risk model | Transparent and easy to tune for different industries |

## Extension Points

1. Add new regex patterns in `patterns.py`
2. Swap spaCy model or add a Hugging Face token classifier
3. Plug in Microsoft Presidio as an additional analyzer
4. Add document loaders (PDF, DOCX, images via OCR)
5. Connect to a vector DB for privacy filtering in RAG pipelines
