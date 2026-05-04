"""OrchestratorAgent — the single entry point for the identification pipeline.

Wires together:
  1. ImagePreprocessingAgent  — validate + normalise + segment
  2. FeatureExtractionAgent   — embed the segmented ROI
  3. SimilaritySearchAgent    — query pgvector, return ranked matches

Each stage's AgentResult is inspected before proceeding; failures are
surfaced with a clear error message and do not propagate as exceptions to
the caller.  The orchestrator itself is also an agent so it participates in
the same timing/logging infrastructure.

The clean API surface exposed to the HTTP layer is ``identify(image_bytes)``.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from models.schemas import IdentificationResponse
from .base_agent import BaseAgent, AgentResult
from .feature_extraction_agent import FeatureExtractionAgent, FeatureInput
from .preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput
from .similarity_search_agent import SimilarityInput, SimilaritySearchAgent


@dataclass
class IdentifyInput:
    image_bytes: bytes
    region: str = "head"
    top_k: int = 5
    threshold: float = 0.60
    exclude_photo_id: UUID | None = None


class OrchestratorAgent(BaseAgent[IdentifyInput, IdentificationResponse]):
    name = "Orchestrator"

    def __init__(
        self,
        preprocessing: ImagePreprocessingAgent,
        feature_extraction: FeatureExtractionAgent,
        similarity_search: SimilaritySearchAgent,
    ) -> None:
        super().__init__()
        self._preprocessing = preprocessing
        self._feature_extraction = feature_extraction
        self._similarity_search = similarity_search

    async def _execute(self, payload: IdentifyInput) -> IdentificationResponse:
        # Stage 1 — preprocess
        prep_result = await self._preprocessing.run(
            PreprocessingInput(image_bytes=payload.image_bytes, region=payload.region)
        )
        self._require_ok(prep_result, "Preprocessing")

        prep = prep_result.value
        roi = prep.segmentation.roi
        mask = prep.segmentation.mask

        # Stage 2 — embed
        feat_result = await self._feature_extraction.run(
            FeatureInput(image=roi, mask=mask)
        )
        self._require_ok(feat_result, "Feature extraction")

        embedding = feat_result.value.embedding

        # Stage 3 — search
        search_result = await self._similarity_search.run(
            SimilarityInput(
                embedding=embedding,
                top_k=payload.top_k,
                threshold=payload.threshold,
                exclude_photo_id=payload.exclude_photo_id,
            )
        )
        self._require_ok(search_result, "Similarity search")

        output = search_result.value
        return IdentificationResponse(
            matches=output.matches,
            threshold=output.threshold,
            accepted=output.accepted,
        )

    @staticmethod
    def _require_ok(result: AgentResult, stage: str) -> None:
        if not result.ok:
            raise RuntimeError(f"{stage} failed: {result.error}")
