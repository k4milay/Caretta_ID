"""SimilaritySearchAgent — queries the vector database and returns ranked matches.

Input : SimilarityInput  (embedding vector + optional search config)
Output: SimilarityOutput (ranked MatchResult list, threshold used, accepted flag)

Confidence banding:
  ≥ 0.85  → "high"
  ≥ 0.70  → "medium"
  ≥ 0.60  → "low"
  < 0.60  → filtered out (below threshold)

The similarity algorithm is injected via a Strategy interface so cosine (default),
euclidean, or a learned metric can be swapped without touching this class.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

import numpy as np

from core.config import get_settings
from models.schemas import MatchResult
from repositories.photo_repository import EmbeddingMatch

from .base_agent import BaseAgent

# Güven bantları — tam vücut + 3 bölge gömme için ayarlandı (eşik: 0.78)
_GUVEN_BANTLARI = [
    (0.94, "high"),    # Yüksek güven: %94 ve üzeri
    (0.89, "medium"),  # Orta güven:   %89 – %94
    (0.84, "low"),     # Düşük güven:  %84 – %89
]
# Geriye dönük uyumluluk için eski ad
_CONFIDENCE_BANDS = _GUVEN_BANTLARI


# ── Similarity Strategy ────────────────────────────────────────────────────────

class SimilarityStrategy(ABC):
    @abstractmethod
    def score(self, query: np.ndarray, candidate: np.ndarray) -> float:
        """Return a similarity in [0, 1] (higher = more similar)."""


class CosineStrategy(SimilarityStrategy):
    def score(self, query: np.ndarray, candidate: np.ndarray) -> float:
        return float(np.dot(query, candidate))


class EuclideanStrategy(SimilarityStrategy):
    """Converts L2 distance to a [0,1] similarity via exponential decay."""
    def score(self, query: np.ndarray, candidate: np.ndarray) -> float:
        dist = float(np.linalg.norm(query - candidate))
        return float(np.exp(-dist))


# ── Agent I/O ─────────────────────────────────────────────────────────────────

@dataclass
class SimilarityInput:
    embedding: np.ndarray
    top_k: int = field(default_factory=lambda: get_settings().top_n_matches)
    threshold: float = field(default_factory=lambda: get_settings().similarity_threshold)
    exclude_photo_id: UUID | None = None


@dataclass
class SimilarityOutput:
    matches: list[MatchResult]
    threshold: float
    accepted: bool


# ── Agent ─────────────────────────────────────────────────────────────────────

class SimilaritySearchAgent(BaseAgent[SimilarityInput, SimilarityOutput]):
    name = "SimilaritySearch"

    def __init__(
        self,
        photo_repo,
        turtle_repo,
        strategy: SimilarityStrategy | None = None,
    ) -> None:
        super().__init__()
        self._photo_repo = photo_repo
        self._turtle_repo = turtle_repo
        self._strategy = strategy or CosineStrategy()

    async def _execute(self, payload: SimilarityInput) -> SimilarityOutput:
        raw_matches = await self._photo_repo.search_by_embedding(
            payload.embedding,
            top_k=payload.top_k,
            exclude_photo_id=payload.exclude_photo_id,
        )
        results = await self._build_results(raw_matches, payload.threshold)
        return SimilarityOutput(
            matches=results,
            threshold=payload.threshold,
            accepted=len(results) > 0,
        )

    async def _build_results(
        self, raw: list[EmbeddingMatch], threshold: float
    ) -> list[MatchResult]:
        if not raw:
            return []

        turtle_ids = [m.turtle_id for m in raw if m.turtle_id]
        turtles = {t.id: t for t in await self._turtle_repo.get_by_ids(turtle_ids)}

        results: list[MatchResult] = []
        seen_turtle_ids: set[UUID] = set()

        for match in raw:
            if match.turtle_id is None or match.turtle_id not in turtles:
                continue
            if match.similarity < threshold:
                continue
            # Deduplicate: keep best photo score per turtle
            if match.turtle_id in seen_turtle_ids:
                continue
            seen_turtle_ids.add(match.turtle_id)

            turtle = turtles[match.turtle_id]
            confidence = self._confidence_band(match.similarity, threshold)
            results.append(
                MatchResult(
                    turtle_id=match.turtle_id,
                    name=turtle.name,
                    similarity_score=round(match.similarity, 4),
                    confidence=confidence,
                )
            )

        return sorted(results, key=lambda r: r.similarity_score, reverse=True)

    @staticmethod
    def _confidence_band(score: float, threshold: float) -> str:
        for cutoff, label in _CONFIDENCE_BANDS:
            if score >= cutoff:
                return label
        return "low"
