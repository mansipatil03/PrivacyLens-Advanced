"""
Core PrivacyLens detection engine.
Combines regex patterns + spaCy NER + optional transformer models.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from enum import Enum

from .patterns import PATTERNS, ENTITY_META
from .redactor import Redactor, RedactionStrategy

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Entity:
    entity_type: str
    text: str
    start: int
    end: int
    score: float
    category: str = ""
    risk: str = "medium"
    source: str = "regex"  # regex | spacy | transformer

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    original_text: str
    entities: List[Entity]
    risk_score: float
    risk_level: str
    summary: str
    redacted_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "entities": [e.to_dict() for e in self.entities],
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "summary": self.summary,
            "redacted_text": self.redacted_text,
            "entity_count": len(self.entities),
        }


class PrivacyLens:
    """
    Main detector class.

    Usage:
        detector = PrivacyLens()
        result = detector.analyze("My Aadhaar is 1234-5678-9012")
        print(result.entities)
    """

    def __init__(
        self,
        use_spacy: bool = True,
        spacy_model: str = "en_core_web_sm",  # use en_core_web_trf for higher accuracy
        confidence_threshold: float = 0.5,
    ):
        self.use_spacy = use_spacy
        self.confidence_threshold = confidence_threshold
        self.nlp = None
        self.redactor = Redactor()

        if use_spacy:
            self._load_spacy(spacy_model)

    def _load_spacy(self, model_name: str) -> None:
        try:
            import spacy
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(
                f"spaCy model '{model_name}' not found. "
                f"Run: python -m spacy download {model_name}\n"
                "Falling back to regex-only mode."
            )
            self.use_spacy = False
            self.nlp = None
        except ImportError:
            logger.warning("spaCy not installed. Using regex-only mode.")
            self.use_spacy = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        text: str,
        redact: bool = False,
        strategy: RedactionStrategy = RedactionStrategy.MASK,
        entities_of_interest: Optional[List[str]] = None,
    ) -> AnalysisResult:
        """
        Analyze text for sensitive information.

        Args:
            text: Input text
            redact: Whether to also return redacted version
            strategy: Redaction strategy (mask / hash / label / remove)
            entities_of_interest: Optional filter list of entity types

        Returns:
            AnalysisResult
        """
        if not text or not text.strip():
            return AnalysisResult(
                original_text=text,
                entities=[],
                risk_score=0.0,
                risk_level="low",
                summary="Empty text — no analysis performed",
            )

        entities: List[Entity] = []

        # 1. Regex layer (high precision for structured IDs)
        entities.extend(self._detect_regex(text))

        # 2. spaCy NER layer
        if self.use_spacy and self.nlp is not None:
            entities.extend(self._detect_spacy(text))

        # Deduplicate overlapping entities (keep higher score)
        entities = self._deduplicate(entities)

        # Filter by interest list
        if entities_of_interest:
            interest = {e.upper() for e in entities_of_interest}
            entities = [e for e in entities if e.entity_type.upper() in interest]

        # Filter by confidence
        entities = [e for e in entities if e.score >= self.confidence_threshold]

        # Sort by position
        entities.sort(key=lambda e: e.start)

        # Risk calculation
        risk_score, risk_level, summary = self._calculate_risk(entities)

        redacted = None
        if redact:
            redacted = self.redactor.redact(text, entities, strategy)

        return AnalysisResult(
            original_text=text,
            entities=entities,
            risk_score=risk_score,
            risk_level=risk_level,
            summary=summary,
            redacted_text=redacted,
        )

    def redact(
        self,
        text: str,
        strategy: RedactionStrategy = RedactionStrategy.MASK,
        entities_of_interest: Optional[List[str]] = None,
    ) -> str:
        """Convenience method: analyze + redact in one call."""
        result = self.analyze(
            text,
            redact=True,
            strategy=strategy,
            entities_of_interest=entities_of_interest,
        )
        return result.redacted_text or text

    def batch_analyze(
        self,
        texts: List[str],
        **kwargs,
    ) -> List[AnalysisResult]:
        return [self.analyze(t, **kwargs) for t in texts]

    # ------------------------------------------------------------------
    # Internal detection methods
    # ------------------------------------------------------------------

    def _detect_regex(self, text: str) -> List[Entity]:
        found: List[Entity] = []

        for entity_type, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                matched_text = match.group()
                # Basic validation to reduce false positives
                if not self._is_valid_match(entity_type, matched_text):
                    continue

                meta = ENTITY_META.get(entity_type, {})
                found.append(
                    Entity(
                        entity_type=entity_type,
                        text=matched_text,
                        start=match.start(),
                        end=match.end(),
                        score=0.92,  # regex is high precision
                        category=meta.get("category", "Unknown"),
                        risk=meta.get("risk", "medium"),
                        source="regex",
                    )
                )
        return found

    def _detect_spacy(self, text: str) -> List[Entity]:
        found: List[Entity] = []
        doc = self.nlp(text)

        # Map spaCy labels to our taxonomy
        label_map = {
            "PERSON": "PERSON",
            "ORG": "ORG",
            "GPE": "GPE",
            "LOC": "LOC",
            "DATE": "DATE_OF_BIRTH",  # approximate; refine later
        }

        for ent in doc.ents:
            mapped = label_map.get(ent.label_)
            if not mapped:
                continue

            # Skip very short or pure number "names"
            if mapped == "PERSON" and (len(ent.text) < 3 or ent.text.isdigit()):
                continue

            meta = ENTITY_META.get(mapped, {})
            # spaCy confidence is not directly available on all models;
            # we assign a reasonable default and can calibrate later.
            score = 0.85 if mapped == "PERSON" else 0.75

            found.append(
                Entity(
                    entity_type=mapped,
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    score=score,
                    category=meta.get("category", "Unknown"),
                    risk=meta.get("risk", "medium"),
                    source="spacy",
                )
            )
        return found

    def _is_valid_match(self, entity_type: str, text: str) -> bool:
        """Lightweight validation to reduce false positives."""
        cleaned = text.replace(" ", "").replace("-", "")

        if entity_type == "AADHAAR":
            return len(cleaned) == 12 and cleaned.isdigit()

        if entity_type == "PAN":
            return len(text) == 10 and text[:5].isalpha() and text[5:9].isdigit()

        if entity_type == "CREDIT_CARD":
            digits = "".join(c for c in text if c.isdigit())
            return 13 <= len(digits) <= 19 and self._luhn_check(digits)

        if entity_type == "PHONE":
            digits = "".join(c for c in text if c.isdigit())
            return 10 <= len(digits) <= 13

        if entity_type == "EMAIL":
            return "@" in text and "." in text.split("@")[-1]

        return True

    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """Luhn algorithm for credit card validation."""
        try:
            digits = [int(d) for d in card_number]
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            total = sum(odd_digits)
            for d in even_digits:
                total += sum(divmod(d * 2, 10))
            return total % 10 == 0
        except Exception:
            return False

    def _deduplicate(self, entities: List[Entity]) -> List[Entity]:
        """Keep highest-scoring entity when spans overlap."""
        if not entities:
            return []

        # Sort by start, then by score descending
        sorted_ents = sorted(entities, key=lambda e: (e.start, -e.score))
        result: List[Entity] = []

        for ent in sorted_ents:
            overlap = False
            for existing in result:
                if not (ent.end <= existing.start or ent.start >= existing.end):
                    # Overlap → keep the one with higher score
                    if ent.score > existing.score:
                        result.remove(existing)
                        result.append(ent)
                    overlap = True
                    break
            if not overlap:
                result.append(ent)

        return result

    def _calculate_risk(
        self, entities: List[Entity]
    ) -> tuple[float, str, str]:
        if not entities:
            return 0.0, "low", "No sensitive information detected"

        risk_weights = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.15,
        }

        scores = []
        critical_count = 0
        high_count = 0

        for e in entities:
            w = risk_weights.get(e.risk, 0.4)
            scores.append(w * e.score)
            if e.risk == "critical":
                critical_count += 1
            elif e.risk == "high":
                high_count += 1

        # Aggregate risk (capped at 1.0)
        avg = sum(scores) / len(scores)
        boost = min(0.3, 0.08 * critical_count + 0.04 * high_count)
        risk_score = min(1.0, avg + boost)

        if risk_score >= 0.75 or critical_count >= 2:
            level = "critical"
            summary = f"Critical risk — {critical_count} critical + {high_count} high sensitivity identifiers found"
        elif risk_score >= 0.5 or critical_count >= 1:
            level = "high"
            summary = f"High risk — {len(entities)} sensitive entities detected"
        elif risk_score >= 0.25:
            level = "medium"
            summary = f"Medium risk — {len(entities)} potentially sensitive items found"
        else:
            level = "low"
            summary = f"Low risk — {len(entities)} low-sensitivity entities found"

        return round(risk_score, 3), level, summary
