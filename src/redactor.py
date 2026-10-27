"""
Redaction strategies for sensitive spans.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .detector import Entity


class RedactionStrategy(str, Enum):
    MASK = "mask"          # ********
    HASH = "hash"          # sha256 short hash
    LABEL = "label"        # [AADHAAR]
    PARTIAL = "partial"    # show last 4 chars
    REMOVE = "remove"      # delete the span


class Redactor:
    """Applies redaction strategies to detected entities."""

    def redact(
        self,
        text: str,
        entities: List["Entity"],
        strategy: RedactionStrategy = RedactionStrategy.MASK,
    ) -> str:
        if not entities:
            return text

        # Work from the end so offsets stay valid
        sorted_ents = sorted(entities, key=lambda e: e.start, reverse=True)
        result = text

        for ent in sorted_ents:
            replacement = self._get_replacement(ent, strategy)
            result = result[: ent.start] + replacement + result[ent.end :]

        return result

    def _get_replacement(self, ent: "Entity", strategy: RedactionStrategy) -> str:
        if strategy == RedactionStrategy.MASK:
            return "*" * len(ent.text)

        if strategy == RedactionStrategy.HASH:
            h = hashlib.sha256(ent.text.encode()).hexdigest()[:10]
            return f"[HASH:{h}]"

        if strategy == RedactionStrategy.LABEL:
            return f"[{ent.entity_type}]"

        if strategy == RedactionStrategy.PARTIAL:
            if len(ent.text) <= 4:
                return "*" * len(ent.text)
            return "*" * (len(ent.text) - 4) + ent.text[-4:]

        if strategy == RedactionStrategy.REMOVE:
            return ""

        # fallback
        return "[REDACTED]"
