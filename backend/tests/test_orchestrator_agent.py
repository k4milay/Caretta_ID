"""Tests for OrchestratorAgent — all dependencies faked in-memory."""
from dataclasses import dataclass
from uuid import uuid4

import cv2
import numpy as np
import pytest

from agents.base_agent import AgentResult
from agents.feature_extraction_agent import FeatureExtractionAgent, FeatureInput, FeatureOutput
from agents.orchestrator_agent import IdentifyInput, OrchestratorAgent
from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput, PreprocessingOutput
from agents.similarity_search_agent import SimilarityInput, SimilarityOutput, SimilaritySearchAgent
from models.schemas import IdentificationResponse, MatchResult
from services.segmentation.base import SegmentationResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_jpeg(w: int = 200, h: int = 200) -> bytes:
    img = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def _unit_vec(dim: int = 512) -> np.ndarray:
    v = np.ones(dim, dtype=np.float32)
    return v / np.linalg.norm(v)


def _fake_seg_result() -> SegmentationResult:
    roi = np.zeros((256, 512, 3), dtype=np.uint8)
    mask = np.ones((256, 512), dtype=np.uint8) * 255
    return SegmentationResult(roi=roi, mask=mask, region_name="head")


# ── Stub agents ───────────────────────────────────────────────────────────────

class _OkPreprocessing(ImagePreprocessingAgent):
    async def _execute(self, payload: PreprocessingInput) -> PreprocessingOutput:
        img = np.zeros((512, 512, 3), dtype=np.uint8)
        return PreprocessingOutput(normalised=img, segmentation=_fake_seg_result(), original_size=(512, 512))


class _OkFeatures(FeatureExtractionAgent):
    async def _execute(self, payload: FeatureInput) -> FeatureOutput:
        return FeatureOutput(embedding=_unit_vec())


class _OkSearch(SimilaritySearchAgent):
    def __init__(self):
        # bypass super().__init__ which needs repos
        from core.logging import get_logger
        self.log = get_logger("test.search")
        self._photo_repo = None
        self._turtle_repo = None

    async def _execute(self, payload: SimilarityInput) -> SimilarityOutput:
        return SimilarityOutput(
            matches=[
                MatchResult(
                    turtle_id=uuid4(),
                    name="Athena",
                    similarity_score=0.91,
                    confidence="high",
                )
            ],
            threshold=payload.threshold,
            accepted=True,
        )


class _FailingPreprocessing(ImagePreprocessingAgent):
    async def _execute(self, payload: PreprocessingInput) -> PreprocessingOutput:
        raise ValueError("corrupt image")


def _make_orchestrator(prep=None, feat=None, search=None) -> OrchestratorAgent:
    return OrchestratorAgent(
        preprocessing=prep or _OkPreprocessing(),
        feature_extraction=feat or _OkFeatures(),
        similarity_search=search or _OkSearch(),
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_pipeline_returns_match():
    agent = _make_orchestrator()
    result = await agent.run(IdentifyInput(image_bytes=_make_jpeg()))
    assert result.ok
    resp: IdentificationResponse = result.value
    assert resp.accepted is True
    assert resp.matches[0].name == "Athena"
    assert resp.matches[0].confidence == "high"


@pytest.mark.asyncio
async def test_preprocessing_failure_propagates():
    agent = _make_orchestrator(prep=_FailingPreprocessing())
    result = await agent.run(IdentifyInput(image_bytes=_make_jpeg()))
    assert result.ok is False
    assert "Preprocessing" in (result.error or "")
    assert "corrupt image" in (result.error or "")


@pytest.mark.asyncio
async def test_accepted_false_when_no_matches():
    class _EmptySearch(_OkSearch):
        async def _execute(self, payload):
            return SimilarityOutput(matches=[], threshold=payload.threshold, accepted=False)

    agent = _make_orchestrator(search=_EmptySearch())
    result = await agent.run(IdentifyInput(image_bytes=_make_jpeg()))
    assert result.ok
    assert result.value.accepted is False
    assert result.value.matches == []
