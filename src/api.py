"""
FastAPI application for PrivacyLens.
"""

from typing import List, Optional
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .detector import PrivacyLens
from .redactor import RedactionStrategy
from .config import settings
from .patterns import list_supported_entities

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Sensitive Information Detection & Redaction API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared detector instance
detector = PrivacyLens(
    use_spacy=settings.use_spacy,
    spacy_model=settings.spacy_model,
    confidence_threshold=settings.confidence_threshold,
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, example="My name is Rahul and my Aadhaar is 1234-5678-9012")
    redact: bool = False
    strategy: RedactionStrategy = RedactionStrategy.MASK
    entities_of_interest: Optional[List[str]] = None


class BatchAnalyzeRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1)
    redact: bool = False
    strategy: RedactionStrategy = RedactionStrategy.MASK


class EntityOut(BaseModel):
    entity_type: str
    text: str
    start: int
    end: int
    score: float
    category: str
    risk: str
    source: str


class AnalyzeResponse(BaseModel):
    original_text: str
    entities: List[EntityOut]
    risk_score: float
    risk_level: str
    summary: str
    redacted_text: Optional[str] = None
    entity_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "PrivacyLens",
        "version": settings.api_version,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/entities")
def supported_entities():
    """List all supported entity types."""
    return {"entities": list_supported_entities()}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    try:
        result = detector.analyze(
            text=request.text,
            redact=request.redact,
            strategy=request.strategy,
            entities_of_interest=request.entities_of_interest,
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch", response_model=List[AnalyzeResponse])
def batch_analyze(request: BatchAnalyzeRequest):
    try:
        results = detector.batch_analyze(
            texts=request.texts,
            redact=request.redact,
            strategy=request.strategy,
        )
        return [r.to_dict() for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/redact")
def redact_only(request: AnalyzeRequest):
    """Shortcut endpoint that only returns redacted text."""
    try:
        redacted = detector.redact(
            text=request.text,
            strategy=request.strategy,
            entities_of_interest=request.entities_of_interest,
        )
        return {"redacted_text": redacted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
